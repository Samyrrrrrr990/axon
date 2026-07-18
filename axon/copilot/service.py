"""The copilot: reads the graph + node catalog, emits validated graph ops."""

from __future__ import annotations

import json

from axon.copilot.ops import apply_ops
from axon.engine.graph import Workflow, validate_workflow
from axon.llm.providers import ProviderError, chat
from axon.sdk.registry import Registry

SYSTEM_PROMPT = """You are Axon's copilot. Axon is a visual AI-building tool: users wire nodes \
into graphs that load data, train ML models, fine-tune LLMs, and build agent pipelines. \
You edit the user's graph by emitting operations. You NEVER write or emit code.

Respond with a single JSON object:
{"reply": "<short friendly explanation of what you did or your answer>",
 "ops": [<zero or more operations>]}

Operations:
- {"op": "add_node", "node": {"id": "<unique>", "type": "<node type id>", "params": {...}}}
- {"op": "remove_node", "node_id": "..."}
- {"op": "set_params", "node_id": "...", "params": {...merged into existing...}}
- {"op": "connect", "edge": {"source": "<node id>", "source_socket": "<output>", "target": "<node id>", "target_socket": "<input>"}}
- {"op": "disconnect", "edge_id": "..."}
- {"op": "set_name", "name": "..."}

Rules:
- Only use node types from the catalog below; match socket names and types exactly.
- Sockets connect only when types match (or one side is "any").
- Every required input socket of every node you add must be connected.
- For pure questions, answer in "reply" with "ops": [].
- Keep graphs minimal, with no dangling or decorative nodes.

NODE CATALOG:
{catalog}

CURRENT GRAPH:
{graph}
"""


def _compact_catalog(registry: Registry) -> str:
    lines = []
    for entry in registry.catalog():
        params = ", ".join(
            f"{k}:{v['kind']}" for k, v in entry["params"].items()
        )
        inputs = ", ".join(f"{k}:{v}" for k, v in entry["inputs"].items()) or "-"
        outputs = ", ".join(f"{k}:{v}" for k, v in entry["outputs"].items()) or "-"
        lines.append(
            f"- {entry['id']} ({entry['name']}): {entry['description'][:100]} | "
            f"in[{inputs}] out[{outputs}] params[{params}]"
        )
    return "\n".join(lines)


def copilot_chat(graph: dict, messages: list[dict], registry: Registry, settings: dict) -> dict:
    wf = Workflow.model_validate(graph)
    provider = settings.get("copilot", {}).get("provider", "openrouter")
    model = settings.get("copilot", {}).get("model", "deepseek/deepseek-chat-v3.1:free")

    system = SYSTEM_PROMPT.replace("{catalog}", _compact_catalog(registry)).replace(
        "{graph}", wf.model_dump_json()
    )
    convo = [{"role": "system", "content": system}] + messages

    reply_text, ops = "", []
    for attempt in range(2):
        try:
            out = chat(provider, model, convo, settings, json_mode=True)
        except ProviderError as exc:
            return {"reply": str(exc), "workflow": None, "ops_applied": 0}

        try:
            parsed = json.loads(out["text"])
            reply_text = str(parsed.get("reply", ""))
            ops = parsed.get("ops", [])
            if not isinstance(ops, list):
                raise ValueError("'ops' must be a list")
        except (json.JSONDecodeError, ValueError) as exc:
            convo += [
                {"role": "assistant", "content": out["text"]},
                {"role": "user", "content": f"Your response was not the required JSON shape ({exc}). "
                                            'Respond again with {"reply": ..., "ops": [...]} only.'},
            ]
            continue

        if not ops:
            return {"reply": reply_text, "workflow": None, "ops_applied": 0}

        try:
            new_wf = apply_ops(wf, ops)
            issues = [i for i in validate_workflow(new_wf, registry) if i.level == "error"]
        except (ValueError, KeyError) as exc:
            issues = None
            error_text = str(exc)
        else:
            error_text = "; ".join(i.message for i in issues) if issues else ""

        if not error_text:
            return {"reply": reply_text, "workflow": new_wf.model_dump(), "ops_applied": len(ops)}

        convo += [
            {"role": "assistant", "content": out["text"]},
            {"role": "user", "content": f"Those ops produce an invalid graph: {error_text}. "
                                        "Emit corrected ops (full replacement for your previous ops)."},
        ]

    return {
        "reply": reply_text or "Sorry, I couldn't produce a valid graph edit for that. "
                               "Try describing the change differently.",
        "workflow": None,
        "ops_applied": 0,
    }
