import json

import httpx
import pytest

from axon.copilot.service import copilot_chat
from axon.sdk import Registry, TextValue
from axon.sdk.node import make_node_decorator


@pytest.fixture()
def registry():
    reg = Registry()
    node = make_node_decorator(reg)

    @node(id="t.src", name="Source", category="T", outputs={"text": "text"})
    def src(ctx):
        return {"text": TextValue(text="x")}

    @node(id="t.sink", name="Sink", category="T", inputs={"text": "text"}, outputs={})
    def sink(ctx, text):
        return None

    return reg


def _settings(replies):
    calls = {"n": 0}

    def handler(request):
        body = replies[min(calls["n"], len(replies) - 1)]
        calls["n"] += 1
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(body)}}]})

    return {
        "keys": {"openrouter": "k"},
        "copilot": {"provider": "openrouter", "model": "test:free"},
        "_transport": httpx.MockTransport(handler),
    }


EMPTY_GRAPH = {"format": "axon-workflow/1", "id": "w", "name": "New", "nodes": [], "edges": [], "meta": {}}


def test_copilot_builds_graph(registry):
    settings = _settings([{
        "reply": "Added a source and sink for you.",
        "ops": [
            {"op": "add_node", "node": {"id": "a", "type": "t.src"}},
            {"op": "add_node", "node": {"id": "b", "type": "t.sink"}},
            {"op": "connect", "edge": {"source": "a", "source_socket": "text",
                                       "target": "b", "target_socket": "text"}},
        ],
    }])
    out = copilot_chat(EMPTY_GRAPH, [{"role": "user", "content": "make a flow"}], registry, settings)
    assert out["workflow"] is not None
    assert len(out["workflow"]["nodes"]) == 2
    assert out["ops_applied"] == 3
    assert "Added" in out["reply"]


def test_copilot_retries_on_invalid_graph(registry):
    settings = _settings([
        {"reply": "try 1", "ops": [{"op": "add_node", "node": {"id": "a", "type": "t.nonexistent"}}]},
        {"reply": "fixed", "ops": [{"op": "add_node", "node": {"id": "a", "type": "t.src"}}]},
    ])
    out = copilot_chat(EMPTY_GRAPH, [{"role": "user", "content": "add a node"}], registry, settings)
    assert out["reply"] == "fixed"
    assert out["workflow"]["nodes"][0]["type"] == "t.src"


def test_copilot_pure_chat(registry):
    settings = _settings([{"reply": "A dataset is a table of rows.", "ops": []}])
    out = copilot_chat(EMPTY_GRAPH, [{"role": "user", "content": "what is a dataset?"}], registry, settings)
    assert out["ops_applied"] == 0
    assert out["workflow"] is None


def test_copilot_gives_up_gracefully(registry):
    settings = _settings([
        {"reply": "bad", "ops": [{"op": "add_node", "node": {"id": "a", "type": "t.nope"}}]},
    ])
    out = copilot_chat(EMPTY_GRAPH, [{"role": "user", "content": "x"}], registry, settings)
    assert out["workflow"] is None
    assert "couldn't" in out["reply"].lower() or "bad" in out["reply"]
