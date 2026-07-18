import threading
import time

import pytest

from axon.engine.cache import Cache
from axon.engine.executor import execute_workflow
from axon.engine.graph import Edge, NodeInstance, Workflow
from axon.engine.runs import RunManager
from axon.sdk import Int, Registry, TextValue
from axon.sdk.node import make_node_decorator


@pytest.fixture()
def registry():
    reg = Registry()
    node = make_node_decorator(reg)
    calls = {"count": 0}

    @node(id="t.const", name="Const", category="T", outputs={"text": "text"},
          params={"n": Int(default=1)})
    def const(ctx, n):
        calls["count"] += 1
        ctx.log("emitting")
        return {"text": TextValue(text=f"v{n}")}

    @node(id="t.upper", name="Upper", category="T", inputs={"text": "text"},
          outputs={"text": "text"})
    def upper(ctx, text):
        return TextValue(text=text.text.upper())  # bare return → single output

    @node(id="t.fail", name="Fail", category="T", inputs={"text": "text"},
          outputs={"text": "text"})
    def fail(ctx, text):
        raise RuntimeError("boom")

    @node(id="t.fresh", name="Fresh", category="T", outputs={"text": "text"}, cacheable=False)
    def fresh(ctx):
        calls["count"] += 1
        return {"text": TextValue(text="fresh")}

    @node(id="t.slow", name="Slow", category="T", inputs={"text": "text"}, outputs={"text": "text"})
    def slow(ctx, text):
        time.sleep(0.05)
        return {"text": text}

    reg.calls = calls
    return reg


def _run(wf, registry, tmp_path, cancel=None):
    events = []
    execute_workflow(
        wf,
        registry,
        Cache(tmp_path / "cache"),
        workspace=tmp_path,
        settings={},
        emit=events.append,
        cancel=cancel or threading.Event(),
        run_id="r1",
    )
    return events


def _linear_wf():
    return Workflow(
        id="w",
        name="w",
        nodes=[NodeInstance(id="a", type="t.const"), NodeInstance(id="b", type="t.upper")],
        edges=[Edge(id="e", source="a", source_socket="text", target="b", target_socket="text")],
    )


def test_linear_run_event_order(registry, tmp_path):
    events = _run(_linear_wf(), registry, tmp_path)
    types = [e.type for e in events]
    assert types[0] == "run_started"
    assert types[-1] == "run_finished"
    assert types.index("node_started") < types.index("node_finished")
    finished = [e for e in events if e.type == "node_finished"]
    assert finished[-1].data["preview"]["text"]["text"] == "V1"
    assert any(e.type == "node_log" for e in events)


def test_second_run_uses_cache(registry, tmp_path):
    _run(_linear_wf(), registry, tmp_path)
    n_calls = registry.calls["count"]
    events = _run(_linear_wf(), registry, tmp_path)
    assert registry.calls["count"] == n_calls  # no new executions
    finished = [e for e in events if e.type == "node_finished"]
    assert all(e.data.get("cached") for e in finished)


def test_failure_skips_downstream_but_runs_independent(registry, tmp_path):
    wf = Workflow(
        id="w", name="w",
        nodes=[
            NodeInstance(id="a", type="t.const"),
            NodeInstance(id="bad", type="t.fail"),
            NodeInstance(id="after", type="t.upper"),
            NodeInstance(id="solo", type="t.const", params={"n": 9}),
        ],
        edges=[
            Edge(id="e1", source="a", source_socket="text", target="bad", target_socket="text"),
            Edge(id="e2", source="bad", source_socket="text", target="after", target_socket="text"),
        ],
    )
    events = _run(wf, registry, tmp_path)
    failed = {e.node_id: e.data for e in events if e.type == "node_failed"}
    assert "bad" in failed and "boom" in failed["bad"]["error"]
    assert failed["after"].get("skipped") is True
    finished_ids = {e.node_id for e in events if e.type == "node_finished"}
    assert "solo" in finished_ids
    run_end = [e for e in events if e.type == "run_finished"][-1]
    assert run_end.data["status"] == "error"


def test_cancellation(registry, tmp_path):
    cancel = threading.Event()
    cancel.set()
    events = _run(_linear_wf(), registry, tmp_path, cancel=cancel)
    assert events[-1].type == "run_cancelled"
    assert not any(e.type == "node_finished" for e in events)


def test_uncacheable_runs_every_time(registry, tmp_path):
    wf = Workflow(id="w", name="w", nodes=[NodeInstance(id="f", type="t.fresh")], edges=[])
    _run(wf, registry, tmp_path)
    before = registry.calls["count"]
    _run(wf, registry, tmp_path)
    assert registry.calls["count"] == before + 1


def test_run_manager_end_to_end(registry, tmp_path):
    events = []
    rm = RunManager(
        registry=registry,
        cache=Cache(tmp_path / "cache"),
        workspace=tmp_path,
        settings_getter=lambda: {},
    )
    rm.subscribe(events.append)
    run_id = rm.start(_linear_wf())
    for _ in range(100):
        if rm.get_run(run_id)["status"] in ("finished", "error"):
            break
        time.sleep(0.05)
    info = rm.get_run(run_id)
    assert info["status"] == "finished"
    assert info["nodes"]["b"]["status"] == "finished"
    assert any(e.type == "run_finished" for e in events)
