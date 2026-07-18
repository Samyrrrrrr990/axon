"""Graph operations — the only thing the copilot is allowed to emit. Never code."""

from __future__ import annotations

import uuid

from axon.engine.graph import Edge, NodeInstance, Workflow


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:6]}"


def apply_ops(wf: Workflow, ops: list[dict]) -> Workflow:
    """Pure: returns a new Workflow with ops applied; the input is untouched."""
    out = wf.model_copy(deep=True)

    for op in ops:
        kind = op.get("op")

        if kind == "add_node":
            node = NodeInstance.model_validate({"id": "", **op["node"]})
            if not node.id or any(n.id == node.id for n in out.nodes):
                node.id = _new_id(node.type.split(".")[-1])
            if node.position == {"x": 0, "y": 0}:
                if out.nodes:
                    rightmost = max(out.nodes, key=lambda n: n.position.get("x", 0))
                    node.position = {
                        "x": rightmost.position.get("x", 0) + 260,
                        "y": rightmost.position.get("y", 0),
                    }
                else:
                    node.position = {"x": 120, "y": 160}
            out.nodes.append(node)

        elif kind == "remove_node":
            node_id = op["node_id"]
            out.nodes = [n for n in out.nodes if n.id != node_id]
            out.edges = [e for e in out.edges if e.source != node_id and e.target != node_id]

        elif kind == "set_params":
            for n in out.nodes:
                if n.id == op["node_id"]:
                    n.params = {**n.params, **op.get("params", {})}
                    break
            else:
                raise ValueError(f"set_params: no node with id '{op['node_id']}'")

        elif kind == "connect":
            edge_data = dict(op["edge"])
            edge_data.setdefault("id", _new_id("e"))
            edge = Edge.model_validate(edge_data)
            # Replace any existing wire into the same input socket.
            out.edges = [
                e for e in out.edges
                if not (e.target == edge.target and e.target_socket == edge.target_socket)
            ]
            out.edges.append(edge)

        elif kind == "disconnect":
            out.edges = [e for e in out.edges if e.id != op["edge_id"]]

        elif kind == "set_name":
            out.name = op["name"]

        else:
            raise ValueError(f"Unknown op '{kind}'")

    return out
