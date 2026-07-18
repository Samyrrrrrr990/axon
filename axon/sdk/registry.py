"""Node registry: every @node decoration lands here; the catalog feeds the UI and the copilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from axon.sdk.params import Param


@dataclass
class NodeDef:
    id: str
    name: str
    category: str
    fn: Callable
    description: str = ""
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    params: dict[str, Param] = field(default_factory=dict)
    pack: str = "core"
    cacheable: bool = True


class Registry:
    def __init__(self):
        self._nodes: dict[str, NodeDef] = {}
        self._builtin_loaded = False

    def register(self, nd: NodeDef) -> None:
        if nd.id in self._nodes:
            raise ValueError(f"Node id already registered: {nd.id}")
        self._nodes[nd.id] = nd

    def get(self, node_id: str) -> NodeDef:
        if node_id not in self._nodes:
            known = ", ".join(sorted(self._nodes)) or "(none)"
            raise KeyError(f"Unknown node type '{node_id}'. Known: {known}")
        return self._nodes[node_id]

    def all(self) -> list[NodeDef]:
        return list(self._nodes.values())

    def catalog(self) -> list[dict]:
        return [
            {
                "id": nd.id,
                "name": nd.name,
                "category": nd.category,
                "description": nd.description,
                "pack": nd.pack,
                "cacheable": nd.cacheable,
                "inputs": dict(nd.inputs),
                "outputs": dict(nd.outputs),
                "params": {k: p.schema() for k, p in nd.params.items()},
            }
            for nd in self._nodes.values()
        ]

    def load_builtin(self) -> None:
        """Import every built-in node module so decorators run. Idempotent."""
        if self._builtin_loaded:
            return
        self._builtin_loaded = True
        import axon.nodes  # noqa: F401  (module's import loop does the registering)


REGISTRY = Registry()
