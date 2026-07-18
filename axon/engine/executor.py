"""Executes a workflow node-by-node in topological order, emitting RunEvents throughout."""

from __future__ import annotations

import threading
import traceback
import uuid
from pathlib import Path
from typing import Callable

import axon
from axon.engine.cache import Cache
from axon.engine.events import RunEvent
from axon.engine.graph import Workflow, topo_order
from axon.sdk.context import NodeContext
from axon.sdk.registry import Registry


def _hint_for(exc: Exception) -> str | None:
    if isinstance(exc, ModuleNotFoundError):
        return (
            f"This node needs the Python package '{exc.name}'. "
            "Install its pack from Settings → Packs."
        )
    text = str(exc)
    if "shapes" in text or "shape" in text and "mismatch" in text:
        return "The data shape doesn't match what this node expects — check upstream columns."
    if "could not convert string to float" in text:
        return "This node needs numeric data. Add an Encode Categorical node before it."
    if "NaN" in text or "missing" in text.lower():
        return "Your data may contain missing values. Add a Handle Missing node upstream."
    return None


def _normalize_outputs(result, output_sockets: dict[str, str]) -> dict:
    if isinstance(result, dict):
        unknown = set(result) - set(output_sockets)
        if unknown:
            raise ValueError(
                f"Node returned unknown output socket(s): {', '.join(sorted(unknown))}. "
                f"Declared outputs: {', '.join(output_sockets)}"
            )
        return result
    if result is None:
        return {}
    if len(output_sockets) == 1:
        return {next(iter(output_sockets)): result}
    raise ValueError("Node with multiple outputs must return a dict keyed by socket name")


def _preview_outputs(outputs: dict) -> dict:
    previews = {}
    for socket, container in outputs.items():
        try:
            previews[socket] = container.preview()
        except Exception:
            previews[socket] = {"type": "unknown", "repr": repr(container)[:500]}
    return previews


def execute_workflow(
    wf: Workflow,
    registry: Registry,
    cache: Cache,
    workspace: Path,
    settings: dict,
    emit: Callable[[RunEvent], None],
    cancel: threading.Event,
    run_id: str,
) -> dict:
    """Synchronous execution; call from a worker thread. Returns {node_id: {socket: container}}."""
    emit(RunEvent("run_started", run_id, data={"workflow_id": wf.id, "name": wf.name}))

    order = topo_order(wf)
    node_by_id = {n.id: n for n in wf.nodes}
    inputs_for: dict[str, list] = {nid: [] for nid in order}  # (input_socket, src_id, src_socket)
    for e in wf.edges:
        if e.target in inputs_for:
            inputs_for[e.target].append((e.target_socket, e.source, e.source_socket))

    results: dict[str, dict] = {}
    cache_keys: dict[str, str] = {}
    failed: set[str] = set()

    for nid in order:
        if cancel.is_set():
            emit(RunEvent("run_cancelled", run_id))
            return results

        inst = node_by_id[nid]
        wiring = inputs_for[nid]

        upstream_ids = {src for (_, src, _) in wiring}
        if upstream_ids & failed:
            failed.add(nid)
            emit(RunEvent("node_failed", run_id, nid, {"skipped": True, "error": "Upstream node failed"}))
            continue

        nd = registry.get(inst.type)
        input_keys = [cache_keys[src] for (_, src, _) in sorted(wiring)]
        if nd.cacheable and all(k is not None for k in input_keys):
            key = cache.key(inst.type, inst.params, input_keys, axon.__version__)
        else:
            key = None

        if key is not None:
            cached = cache.get(key)
            if cached is not None:
                results[nid] = cached
                cache_keys[nid] = key
                emit(RunEvent("node_finished", run_id, nid,
                              {"cached": True, "preview": _preview_outputs(cached)}))
                continue
        cache_keys[nid] = key if key is not None else f"fresh:{uuid.uuid4().hex}"

        emit(RunEvent("node_started", run_id, nid, {"name": nd.name}))
        ctx = NodeContext(
            workspace=workspace,
            settings=settings,
            log_cb=lambda m, nid=nid: emit(RunEvent("node_log", run_id, nid, {"message": m})),
            progress_cb=lambda f, m, nid=nid: emit(
                RunEvent("node_progress", run_id, nid, {"fraction": f, "metrics": m})
            ),
            cancel_event=cancel,
            base_dir=wf.meta.get("base_dir"),
        )
        kwargs = {}
        for (input_socket, src, src_socket) in wiring:
            kwargs[input_socket] = results[src][src_socket]
        for pname, p in nd.params.items():
            kwargs[pname] = inst.params.get(pname, p.default)

        try:
            raw = nd.fn(ctx, **kwargs)
            outputs = _normalize_outputs(raw, nd.outputs)
        except Exception as exc:
            if cancel.is_set():
                emit(RunEvent("run_cancelled", run_id))
                return results
            failed.add(nid)
            tb = traceback.format_exception(exc)
            emit(RunEvent("node_failed", run_id, nid, {
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": "".join(tb[-3:]),
                "hint": _hint_for(exc),
            }))
            continue

        results[nid] = outputs
        if key is not None:
            cache.put(key, outputs)
        emit(RunEvent("node_finished", run_id, nid,
                      {"cached": False, "preview": _preview_outputs(outputs)}))

    if cancel.is_set():
        emit(RunEvent("run_cancelled", run_id))
    else:
        emit(RunEvent("run_finished", run_id,
                      data={"status": "error" if failed else "finished"}))
    return results
