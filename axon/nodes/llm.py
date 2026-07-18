"""LLM and agents pack: chat models, prompts, RAG, tools, and an agent loop.

Every node that calls an LLM is uncacheable: each Run makes fresh calls.
"""

from __future__ import annotations

import json

from axon.llm.providers import chat as provider_chat
from axon.sdk import (
    AnyValue,
    Choice,
    Embeddings,
    FilePath,
    Float,
    Int,
    Json,
    Str,
    Text,
    TextDocs,
    TextValue,
    VectorStoreRef,
)
from axon.sdk.node import node

PROVIDER_CHOICES = ["default", "openrouter", "anthropic", "openai", "ollama"]


def _resolve(ctx, provider: str, model: str) -> tuple[str, str]:
    defaults = ctx.settings.get("llm_defaults", {})
    resolved_provider = defaults.get("provider", "openrouter") if provider in ("", "default") else provider
    resolved_model = model or defaults.get("model", "deepseek/deepseek-chat-v3.1:free")
    return resolved_provider, resolved_model


def _call(ctx, provider, model, messages, json_mode=False, temperature=0.7, tools=None):
    p, m = _resolve(ctx, provider, model)
    return provider_chat(p, m, messages, ctx.settings, json_mode=json_mode,
                         temperature=temperature, tools=tools)


def _as_text(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "text"):
        return value.text
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


@node(
    id="llm.chat",
    name="Chat Model",
    category="LLM & Agents",
    description="Send a prompt to a language model and get its reply.",
    inputs={"prompt": "text"},
    outputs={"text": "text"},
    params={
        "system": Text(default="", help="Optional system instructions"),
        "provider": Choice(PROVIDER_CHOICES, default="default"),
        "model": Str(default="", help="Leave empty for your default model"),
        "temperature": Float(default=0.7, min=0.0, max=2.0),
    },
    cacheable=False,
)
def chat_llm(ctx, prompt, system, provider, model, temperature):
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": _as_text(prompt)}
    ]
    out = _call(ctx, provider, model, messages, temperature=temperature)
    return {"text": TextValue(text=out["text"])}


@node(
    id="llm.prompt_template",
    name="Prompt Template",
    category="LLM & Agents",
    description="Build a prompt by filling {a}, {b}, {c} placeholders.",
    inputs={"a": "any", "b": "any", "c": "any"},
    outputs={"text": "text"},
    params={"template": Text(default="", help="Use {a}, {b}, {c} for inputs", required=True)},
)
def prompt_template(ctx, a, b, c, template):
    filled = template.format(a=_as_text(a), b=_as_text(b), c=_as_text(c))
    return {"text": TextValue(text=filled)}


@node(
    id="llm.extract",
    name="Structured Extract",
    category="LLM & Agents",
    description="Pull structured JSON out of messy text.",
    inputs={"text": "text"},
    outputs={"data": "any"},
    params={
        "schema": Json(default={"field": "description of what to extract"},
                       help="Describe the JSON shape you want"),
        "provider": Choice(PROVIDER_CHOICES, default="default"),
        "model": Str(default=""),
    },
    cacheable=False,
)
def extract(ctx, text, schema, provider, model):
    prompt = (
        f"Extract data from the text below as JSON matching this shape:\n{json.dumps(schema)}\n\n"
        f"Text:\n{_as_text(text)}\n\nRespond with only the JSON object."
    )
    out = _call(ctx, provider, model, [{"role": "user", "content": prompt}], json_mode=True)
    for attempt in range(2):
        try:
            return {"data": AnyValue(value=json.loads(out["text"]))}
        except json.JSONDecodeError as exc:
            if attempt == 1:
                raise ValueError(f"Model did not return valid JSON: {out['text'][:200]}") from exc
            out = _call(
                ctx, provider, model,
                [{"role": "user", "content": prompt},
                 {"role": "assistant", "content": out["text"]},
                 {"role": "user", "content": f"That was not valid JSON ({exc}). Respond with only the JSON object."}],
                json_mode=True,
            )


@node(
    id="llm.load_docs",
    name="Load Documents",
    category="LLM & Agents",
    description="Read all .txt and .md files from a folder.",
    outputs={"docs": "docs"},
    params={"path": FilePath(kind="directory", help="Folder of text files", required=True)},
)
def load_docs(ctx, path):
    folder = ctx.resolve_path(path)
    if not folder.is_dir():
        raise ValueError(f"Not a folder: {folder}")
    docs = []
    for p in sorted(folder.rglob("*")):
        if p.suffix.lower() in (".txt", ".md") and p.is_file():
            docs.append({"id": p.name, "text": p.read_text(errors="replace"), "meta": {"path": p.name}})
    if not docs:
        raise ValueError(f"No .txt or .md files found in {folder}")
    ctx.log(f"Loaded {len(docs)} documents")
    return {"docs": TextDocs(docs=docs)}


@node(
    id="llm.embed",
    name="Embed Text",
    category="LLM & Agents",
    description="Turn documents into vectors for semantic search. Runs locally.",
    inputs={"docs": "docs"},
    outputs={"embeddings": "embeddings"},
    params={"model": Str(default="all-MiniLM-L6-v2", help="Sentence-transformers model")},
    pack="rag",
)
def embed(ctx, docs, model):
    from sentence_transformers import SentenceTransformer

    ctx.log(f"Embedding {len(docs.docs)} documents with {model}")
    st = SentenceTransformer(model)
    vectors = st.encode([d["text"] for d in docs.docs], show_progress_bar=False)
    return {"embeddings": Embeddings(vectors=vectors, docs=docs, meta={"embed_model": model})}


@node(
    id="llm.vector_store",
    name="Vector Store",
    category="LLM & Agents",
    description="Index embeddings into a local Chroma database.",
    inputs={"embeddings": "embeddings"},
    outputs={"store": "vectorstore"},
    params={"collection": Str(default="axon")},
    pack="rag",
)
def vector_store(ctx, embeddings, collection):
    import chromadb

    path = str((ctx.workspace or __import__("pathlib").Path(".")) / "data" / "chroma")
    client = chromadb.PersistentClient(path=path)
    try:
        client.delete_collection(collection)
    except Exception:
        pass
    col = client.create_collection(
        collection, metadata={"embed_model": embeddings.meta.get("embed_model", "all-MiniLM-L6-v2")}
    )
    docs = embeddings.docs.docs
    col.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        embeddings=embeddings.vectors.tolist(),
    )
    ctx.log(f"Indexed {len(docs)} documents into '{collection}'")
    return {"store": VectorStoreRef(path=path, collection=collection)}


def _query_store(ctx, store, query_text: str, k: int) -> TextDocs:
    import chromadb
    from sentence_transformers import SentenceTransformer

    client = chromadb.PersistentClient(path=store.path)
    col = client.get_collection(store.collection)
    model = (col.metadata or {}).get("embed_model", "all-MiniLM-L6-v2")
    vector = SentenceTransformer(model).encode([query_text])[0]
    result = col.query(query_embeddings=[vector.tolist()], n_results=k)
    docs = [
        {"id": rid, "text": text, "meta": {}}
        for rid, text in zip(result["ids"][0], result["documents"][0])
    ]
    return TextDocs(docs=docs)


@node(
    id="llm.retrieve",
    name="Retrieve",
    category="LLM & Agents",
    description="Find the most relevant documents for a query.",
    inputs={"store": "vectorstore", "query": "text"},
    outputs={"docs": "docs"},
    params={"k": Int(default=4, min=1, max=50)},
    pack="rag",
)
def retrieve(ctx, store, query, k):
    return {"docs": _query_store(ctx, store, _as_text(query), k)}


@node(
    id="llm.rag_answer",
    name="RAG Answer",
    category="LLM & Agents",
    description="Answer a question using your documents as the source of truth.",
    inputs={"store": "vectorstore", "question": "text"},
    outputs={"text": "text"},
    params={
        "provider": Choice(PROVIDER_CHOICES, default="default"),
        "model": Str(default=""),
        "k": Int(default=4, min=1, max=20),
    },
    pack="rag",
    cacheable=False,
)
def rag_answer(ctx, store, question, provider, model, k):
    q = _as_text(question)
    found = _query_store(ctx, store, q, k)
    context = "\n\n".join(f"[{d['id']}] {d['text']}" for d in found.docs)
    prompt = (
        "Answer the question using only the sources below. Cite source ids in brackets.\n\n"
        f"Sources:\n{context}\n\nQuestion: {q}"
    )
    out = _call(ctx, provider, model, [{"role": "user", "content": prompt}])
    return {"text": TextValue(text=out["text"])}


@node(
    id="llm.tool",
    name="Tool",
    category="LLM & Agents",
    description="Define a tool the agent can call. Args arrive in `args`; set `result`.",
    outputs={"tool": "any"},
    params={
        "name": Str(required=True, help="Tool name, e.g. calculator"),
        "description": Text(required=True, help="When should the agent use this?"),
        "code": Text(default="result = str(args)", help="Python: read `args` dict, set `result`"),
    },
)
def tool(ctx, name, description, code):
    return {"tool": AnyValue(value={"name": name, "description": description, "code": code})}


def _run_tool(tool_def: dict, arguments: dict) -> str:
    namespace = {"args": arguments}
    exec(compile(tool_def["code"], f"<tool:{tool_def['name']}>", "exec"), namespace)
    return str(namespace.get("result", ""))


@node(
    id="llm.agent",
    name="Agent",
    category="LLM & Agents",
    description="An agent loop: the model reasons, calls your tools, and answers.",
    inputs={"task": "text", "tools": "any"},
    outputs={"text": "text", "log": "docs"},
    params={
        "provider": Choice(PROVIDER_CHOICES, default="default"),
        "model": Str(default=""),
        "max_steps": Int(default=8, min=1, max=25),
    },
    cacheable=False,
)
def agent(ctx, task, tools, provider, model, max_steps):
    tool_defs: list[dict] = []
    if tools is not None:
        value = tools.value if hasattr(tools, "value") else tools
        tool_defs = value if isinstance(value, list) else [value]

    tool_schemas = [
        {"name": t["name"], "description": t["description"],
         "parameters": {"type": "object", "properties": {}, "additionalProperties": True}}
        for t in tool_defs
    ]
    by_name = {t["name"]: t for t in tool_defs}

    messages = [
        {"role": "system", "content": "You are a capable agent. Use the available tools when they help. When you have the final answer, reply with it directly."},
        {"role": "user", "content": _as_text(task)},
    ]
    log: list[dict] = []

    for step in range(max_steps):
        if ctx.cancelled:
            break
        out = _call(ctx, provider, model, messages, tools=tool_schemas or None)
        if not out["tool_calls"]:
            log.append({"id": f"step{step}", "text": f"final answer: {out['text'][:500]}", "meta": {}})
            return {"text": TextValue(text=out["text"]), "log": TextDocs(docs=log)}

        for call in out["tool_calls"]:
            name, arguments = call["name"], call.get("arguments") or {}
            tool_def = by_name.get(name)
            if tool_def is None:
                result = f"error: no tool named {name}"
            else:
                try:
                    result = _run_tool(tool_def, arguments)
                except Exception as exc:
                    result = f"error: {exc}"
            entry = f"called {name}({json.dumps(arguments)}) -> {result[:300]}"
            ctx.log(entry)
            log.append({"id": f"step{step}", "text": entry, "meta": {}})
            messages.append({"role": "assistant", "content": f"I'm calling tool {name} with {json.dumps(arguments)}"})
            messages.append({"role": "user", "content": f"Tool {name} returned: {result}"})

    return {
        "text": TextValue(text="Agent stopped before reaching a final answer (max steps hit)."),
        "log": TextDocs(docs=log),
    }
