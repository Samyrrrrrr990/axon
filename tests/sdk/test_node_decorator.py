import threading

import pytest

from axon.sdk import Int, Str, TextValue
from axon.sdk.context import NodeContext
from axon.sdk.registry import Registry
from axon.sdk.node import make_node_decorator


@pytest.fixture()
def registry():
    return Registry()


@pytest.fixture()
def node(registry):
    return make_node_decorator(registry)


def test_decorator_registers(node, registry):
    @node(
        id="test.echo",
        name="Echo",
        category="Test",
        inputs={"text": "text"},
        outputs={"text": "text"},
        params={"suffix": Str(default="!")},
    )
    def echo(ctx, text, suffix):
        return {"text": TextValue(text=text.text + suffix)}

    nd = registry.get("test.echo")
    assert nd.name == "Echo"
    assert nd.inputs == {"text": "text"}
    assert nd.cacheable is True
    assert nd.fn is echo.fn if hasattr(echo, "fn") else callable(nd.fn)


def test_duplicate_id_raises(node):
    @node(id="test.a", name="A", category="T", outputs={"out": "any"})
    def a(ctx):
        return {}

    with pytest.raises(ValueError, match="test.a"):
        @node(id="test.a", name="A2", category="T", outputs={"out": "any"})
        def a2(ctx):
            return {}


def test_unknown_socket_type_raises(node):
    with pytest.raises(ValueError, match="bogus"):
        @node(id="test.b", name="B", category="T", outputs={"out": "bogus"})
        def b(ctx):
            return {}


def test_catalog_schema(node, registry):
    @node(
        id="test.count",
        name="Count",
        category="Test",
        description="counts",
        inputs={"data": "dataset"},
        outputs={"n": "metrics"},
        params={"limit": Int(default=10, min=1)},
        pack="core",
    )
    def count(ctx, data, limit):
        return {}

    entry = next(e for e in registry.catalog() if e["id"] == "test.count")
    assert entry["params"]["limit"]["kind"] == "int"
    assert entry["inputs"] == {"data": "dataset"}
    assert entry["outputs"] == {"n": "metrics"}
    assert entry["pack"] == "core"
    assert entry["cacheable"] is True


def test_get_unknown_raises_with_known_ids(registry):
    with pytest.raises(KeyError, match="nothing.registered"):
        registry.get("nothing.registered")


def test_context_progress_and_cancel():
    events = []
    cancel = threading.Event()
    ctx = NodeContext(
        workspace=None,
        settings={},
        log_cb=lambda m: events.append(("log", m)),
        progress_cb=lambda f, m: events.append(("progress", f, m)),
        cancel_event=cancel,
    )
    ctx.log("hi")
    ctx.progress(0.5, {"loss": 1.0})
    assert ("log", "hi") in events
    assert ("progress", 0.5, {"loss": 1.0}) in events
    assert ctx.cancelled is False
    cancel.set()
    assert ctx.cancelled is True
