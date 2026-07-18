"""The @node decorator: declare a node's sockets and params, and the UI is generated from them."""

from __future__ import annotations

from typing import Callable

from axon.sdk.containers import SOCKET_TYPES
from axon.sdk.params import Param
from axon.sdk.registry import REGISTRY, NodeDef, Registry


def make_node_decorator(registry: Registry) -> Callable:
    def node(
        *,
        id: str,
        name: str,
        category: str,
        description: str = "",
        inputs: dict[str, str] | None = None,
        outputs: dict[str, str] | None = None,
        params: dict[str, Param] | None = None,
        pack: str = "core",
        cacheable: bool = True,
    ):
        inputs = inputs or {}
        outputs = outputs or {}
        params = params or {}
        for socket_name, type_name in {**inputs, **outputs}.items():
            if type_name not in SOCKET_TYPES:
                raise ValueError(
                    f"Node '{id}' socket '{socket_name}' has unknown type '{type_name}'. "
                    f"Valid types: {', '.join(sorted(SOCKET_TYPES))}"
                )

        def decorate(fn: Callable) -> Callable:
            nd = NodeDef(
                id=id,
                name=name,
                category=category,
                description=description or (fn.__doc__ or "").strip(),
                fn=fn,
                inputs=inputs,
                outputs=outputs,
                params=params,
                pack=pack,
                cacheable=cacheable,
            )
            registry.register(nd)
            fn.node_def = nd
            return fn

        return decorate

    return node


# The default decorator used by all built-in packs.
node = make_node_decorator(REGISTRY)
