import json

import httpx
import pytest

from axon.nodes import llm as L
from axon.sdk import TextDocs, TextValue


def _settings_with_transport(replies):
    """Settings dict carrying a mock transport the llm nodes will use. replies: list of response dicts."""
    calls = {"n": 0}

    def handler(request):
        body = replies[min(calls["n"], len(replies) - 1)]
        calls["n"] += 1
        return httpx.Response(200, json=body)

    return {
        "keys": {"openrouter": "sk-test"},
        "llm_defaults": {"provider": "openrouter", "model": "test/model:free"},
        "_transport": httpx.MockTransport(handler),
    }


def _openai_reply(text):
    return {"choices": [{"message": {"content": text}}]}


def test_chat_node(ctx):
    ctx.settings = _settings_with_transport([_openai_reply("bonjour")])
    out = L.chat_llm(ctx, prompt=TextValue(text="hi"), system="be brief",
                     provider="default", model="", temperature=0.7)["text"]
    assert out.text == "bonjour"


def test_prompt_template(ctx):
    out = L.prompt_template(
        ctx, a=TextValue(text="Paris"), b=None, c=None,
        template="What country is {a} in?",
    )["text"]
    assert out.text == "What country is Paris in?"


def test_extract_retries_on_bad_json(ctx):
    ctx.settings = _settings_with_transport([
        _openai_reply("not json at all"),
        _openai_reply('{"city": "Paris"}'),
    ])
    out = L.extract(ctx, text=TextValue(text="I live in Paris"),
                    schema={"city": "string"}, provider="default", model="")["data"]
    assert out.value == {"city": "Paris"}


def test_tool_node_and_agent(ctx):
    tool = L.tool(ctx, name="add", description="add two numbers",
                  code="result = args['x'] + args['y']")["tool"]
    assert tool.value["name"] == "add"

    ctx.settings = _settings_with_transport([
        {"choices": [{"message": {
            "content": None,
            "tool_calls": [{"id": "1", "function": {"name": "add", "arguments": '{"x": 2, "y": 3}'}}],
        }}]},
        _openai_reply("The answer is 5."),
    ])
    out = L.agent(ctx, task=TextValue(text="what is 2+3?"), tools=tool,
                  provider="default", model="", max_steps=4)
    assert "5" in out["text"].text
    assert any("add" in d["text"] for d in out["log"].docs)


def test_rag_pipeline(ctx, tmp_path):
    pytest.importorskip("chromadb")
    pytest.importorskip("sentence_transformers")

    docs = TextDocs(docs=[
        {"id": "1", "text": "Axon is a visual AI builder.", "meta": {}},
        {"id": "2", "text": "Bananas are yellow fruit.", "meta": {}},
        {"id": "3", "text": "Axon runs locally on your machine.", "meta": {}},
    ])
    ctx.workspace = tmp_path
    emb = L.embed(ctx, docs=docs, model="all-MiniLM-L6-v2")["embeddings"]
    assert emb.vectors.shape[0] == 3
    store = L.vector_store(ctx, embeddings=emb, collection="test")["store"]
    found = L.retrieve(ctx, store=store, query=TextValue(text="what is axon?"), k=2)["docs"]
    assert len(found.docs) == 2
    assert any("Axon" in d["text"] for d in found.docs)

    ctx.settings = _settings_with_transport([_openai_reply("Axon is a visual AI builder [1].")])
    answer = L.rag_answer(ctx, store=store, question=TextValue(text="what is axon?"),
                          provider="default", model="", k=2)["text"]
    assert "Axon" in answer.text


def test_load_docs(ctx, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("hello axon")
    (tmp_path / "docs" / "b.txt").write_text("second doc")
    out = L.load_docs(ctx, path=str(tmp_path / "docs"))["docs"]
    assert len(out.docs) == 2
