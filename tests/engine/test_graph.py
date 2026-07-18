import pytest

from axon.engine.graph import CycleError, Edge, NodeInstance, Workflow, topo_order, validate_workflow
from axon.sdk import Int, Registry
from axon.sdk.node import make_node_decorator


@pytest.fixture()
def registry():
    reg = Registry()
    node = make_node_decorator(reg)

    @node(id="t.source", name="Source", category="T", outputs={"data": "dataset"})
    def source(ctx):
        return {}

    @node(
        id="t.sink",
        name="Sink",
        category="T",
        inputs={"data": "dataset"},
        outputs={"m": "metrics"},
        params={"k": Int(default=1)},
    )
    def sink(ctx, data, k):
        return {}

    @node(id="t.model", name="M", category="T", outputs={"model": "model"})
    def model(ctx):
        return {}

    return reg


def _wf(nodes, edges):
    return Workflow(id="wf1", name="test", nodes=nodes, edges=edges)


def test_valid_workflow_no_issues(registry):
    wf = _wf(
        [NodeInstance(id="a", type="t.source"), NodeInstance(id="b", type="t.sink")],
        [Edge(id="e1", source="a", source_socket="data", target="b", target_socket="data")],
    )
    assert validate_workflow(wf, registry) == []


def test_unknown_node_type(registry):
    wf = _wf([NodeInstance(id="a", type="t.nope")], [])
    issues = validate_workflow(wf, registry)
    assert any("t.nope" in i.message for i in issues)


def test_type_mismatch_edge(registry):
    wf = _wf(
        [NodeInstance(id="a", type="t.model"), NodeInstance(id="b", type="t.sink")],
        [Edge(id="e1", source="a", source_socket="model", target="b", target_socket="data")],
    )
    issues = validate_workflow(wf, registry)
    msg = " ".join(i.message for i in issues)
    assert "model" in msg and "dataset" in msg


def test_missing_required_input(registry):
    wf = _wf([NodeInstance(id="b", type="t.sink")], [])
    issues = validate_workflow(wf, registry)
    assert any("data" in i.message and i.node_id == "b" for i in issues)


def test_cycle_detected(registry):
    wf = _wf(
        [NodeInstance(id="a", type="t.sink"), NodeInstance(id="b", type="t.sink")],
        [
            Edge(id="e1", source="a", source_socket="m", target="b", target_socket="data"),
            Edge(id="e2", source="b", source_socket="m", target="a", target_socket="data"),
        ],
    )
    issues = validate_workflow(wf, registry)
    assert any("cycle" in i.message.lower() for i in issues)
    with pytest.raises(CycleError):
        topo_order(wf)


def test_duplicate_input_edge(registry):
    wf = _wf(
        [
            NodeInstance(id="a", type="t.source"),
            NodeInstance(id="a2", type="t.source"),
            NodeInstance(id="b", type="t.sink"),
        ],
        [
            Edge(id="e1", source="a", source_socket="data", target="b", target_socket="data"),
            Edge(id="e2", source="a2", source_socket="data", target="b", target_socket="data"),
        ],
    )
    issues = validate_workflow(wf, registry)
    assert any("already connected" in i.message for i in issues)


def test_topo_order(registry):
    wf = _wf(
        [
            NodeInstance(id="c", type="t.sink"),
            NodeInstance(id="a", type="t.source"),
            NodeInstance(id="b", type="t.sink"),
        ],
        [
            Edge(id="e1", source="a", source_socket="data", target="b", target_socket="data"),
            Edge(id="e2", source="b", source_socket="m", target="c", target_socket="data"),
        ],
    )
    order = topo_order(wf)
    assert order.index("a") < order.index("b") < order.index("c")


def test_json_round_trip(registry):
    wf = _wf(
        [NodeInstance(id="a", type="t.source", params={"x": 1}, position={"x": 10, "y": 20})],
        [],
    )
    again = Workflow.model_validate_json(wf.model_dump_json())
    assert again.nodes[0].position == {"x": 10, "y": 20}
    assert again.format == "axon-workflow/1"
