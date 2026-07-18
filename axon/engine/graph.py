"""Workflow graph model (this IS the .axon.json schema), validation, and topological ordering."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Literal

from pydantic import BaseModel, Field

from axon.sdk.containers import compatible
from axon.sdk.registry import Registry


class NodeInstance(BaseModel):
    id: str
    type: str
    params: dict = Field(default_factory=dict)
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0})
    label: str | None = None


class Edge(BaseModel):
    id: str
    source: str
    source_socket: str
    target: str
    target_socket: str


class Workflow(BaseModel):
    format: str = "axon-workflow/1"
    id: str = ""
    name: str = "Untitled"
    nodes: list[NodeInstance] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class Issue(BaseModel):
    level: Literal["error", "warning"]
    node_id: str | None = None
    message: str


class CycleError(Exception):
    pass


def _adjacency(wf: Workflow) -> tuple[dict[str, set[str]], dict[str, int]]:
    downstream: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {n.id: 0 for n in wf.nodes}
    for e in wf.edges:
        if e.target not in indegree or e.source not in indegree:
            continue
        if e.target not in downstream[e.source]:
            downstream[e.source].add(e.target)
            indegree[e.target] += 1
    return downstream, indegree


def topo_order(wf: Workflow) -> list[str]:
    downstream, indegree = _adjacency(wf)
    queue = deque(sorted(nid for nid, d in indegree.items() if d == 0))
    order: list[str] = []
    while queue:
        nid = queue.popleft()
        order.append(nid)
        for nxt in sorted(downstream.get(nid, ())):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if len(order) != len(wf.nodes):
        stuck = sorted(set(indegree) - set(order))
        raise CycleError(f"Workflow contains a cycle involving: {', '.join(stuck)}")
    return order


def validate_workflow(wf: Workflow, registry: Registry) -> list[Issue]:
    issues: list[Issue] = []
    node_by_id = {n.id: n for n in wf.nodes}

    for n in wf.nodes:
        try:
            registry.get(n.type)
        except KeyError:
            issues.append(
                Issue(level="error", node_id=n.id, message=f"Unknown node type '{n.type}'")
            )

    seen_inputs: set[tuple[str, str]] = set()
    connected_inputs: set[tuple[str, str]] = set()
    for e in wf.edges:
        src, dst = node_by_id.get(e.source), node_by_id.get(e.target)
        if src is None or dst is None:
            issues.append(
                Issue(level="error", node_id=None, message=f"Edge {e.id} references a missing node")
            )
            continue
        try:
            src_def, dst_def = registry.get(src.type), registry.get(dst.type)
        except KeyError:
            continue  # already reported above
        if e.source_socket not in src_def.outputs:
            issues.append(
                Issue(
                    level="error",
                    node_id=src.id,
                    message=f"'{src_def.name}' has no output socket '{e.source_socket}'",
                )
            )
            continue
        if e.target_socket not in dst_def.inputs:
            issues.append(
                Issue(
                    level="error",
                    node_id=dst.id,
                    message=f"'{dst_def.name}' has no input socket '{e.target_socket}'",
                )
            )
            continue
        src_type = src_def.outputs[e.source_socket]
        dst_type = dst_def.inputs[e.target_socket]
        if not compatible(src_type, dst_type):
            issues.append(
                Issue(
                    level="error",
                    node_id=dst.id,
                    message=(
                        f"Can't connect '{src_def.name}.{e.source_socket}' ({src_type}) to "
                        f"'{dst_def.name}.{e.target_socket}' ({dst_type})"
                    ),
                )
            )
        key = (e.target, e.target_socket)
        if key in seen_inputs:
            issues.append(
                Issue(
                    level="error",
                    node_id=e.target,
                    message=f"Input '{e.target_socket}' on node {e.target} is already connected",
                )
            )
        seen_inputs.add(key)
        connected_inputs.add(key)

    for n in wf.nodes:
        try:
            nd = registry.get(n.type)
        except KeyError:
            continue
        for socket in nd.inputs:
            if (n.id, socket) not in connected_inputs:
                issues.append(
                    Issue(
                        level="error",
                        node_id=n.id,
                        message=f"'{nd.name}' input '{socket}' is not connected",
                    )
                )

    try:
        topo_order(wf)
    except CycleError as exc:
        issues.append(Issue(level="error", node_id=None, message=str(exc)))

    return issues
