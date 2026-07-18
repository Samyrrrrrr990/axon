import pytest

from axon.copilot.ops import apply_ops
from axon.engine.graph import Edge, NodeInstance, Workflow


def _wf():
    return Workflow(
        id="w1", name="Flow",
        nodes=[NodeInstance(id="load", type="data.sample_dataset", params={"name": "iris"},
                            position={"x": 100, "y": 100})],
        edges=[],
    )


def test_add_node_and_connect():
    wf = apply_ops(_wf(), [
        {"op": "add_node", "node": {"id": "split", "type": "data.split", "params": {"test_size": 0.3}}},
        {"op": "connect", "edge": {"source": "load", "source_socket": "dataset",
                                   "target": "split", "target_socket": "dataset"}},
    ])
    assert [n.id for n in wf.nodes] == ["load", "split"]
    assert wf.edges[0].source == "load" and wf.edges[0].id


def test_add_node_auto_id_and_position():
    wf = apply_ops(_wf(), [{"op": "add_node", "node": {"type": "util.view_table"}}])
    added = wf.nodes[-1]
    assert added.id and added.id != "load"
    assert added.position["x"] != 0 or added.position["y"] != 0


def test_set_params_merges():
    wf = apply_ops(_wf(), [{"op": "set_params", "node_id": "load", "params": {"name": "wine"}}])
    assert wf.nodes[0].params["name"] == "wine"


def test_remove_node_drops_its_edges():
    wf = apply_ops(_wf(), [
        {"op": "add_node", "node": {"id": "split", "type": "data.split"}},
        {"op": "connect", "edge": {"source": "load", "source_socket": "dataset",
                                   "target": "split", "target_socket": "dataset"}},
        {"op": "remove_node", "node_id": "split"},
    ])
    assert len(wf.nodes) == 1
    assert wf.edges == []


def test_disconnect_and_rename():
    wf = apply_ops(_wf(), [
        {"op": "add_node", "node": {"id": "s", "type": "data.split"}},
        {"op": "connect", "edge": {"id": "e9", "source": "load", "source_socket": "dataset",
                                   "target": "s", "target_socket": "dataset"}},
        {"op": "disconnect", "edge_id": "e9"},
        {"op": "set_name", "name": "Better Flow"},
    ])
    assert wf.edges == []
    assert wf.name == "Better Flow"


def test_unknown_op_raises():
    with pytest.raises(ValueError, match="explode"):
        apply_ops(_wf(), [{"op": "explode"}])


def test_pure_function_original_untouched():
    original = _wf()
    apply_ops(original, [{"op": "set_name", "name": "Changed"}])
    assert original.name == "Flow"
