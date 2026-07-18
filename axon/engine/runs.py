"""RunManager — starts runs on worker threads, fans out events, tracks live run state."""

from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Callable

from axon.engine.cache import Cache
from axon.engine.events import RunEvent
from axon.engine.executor import execute_workflow
from axon.engine.graph import Workflow
from axon.sdk.registry import Registry


class RunManager:
    def __init__(
        self,
        registry: Registry,
        cache: Cache,
        workspace: Path,
        settings_getter: Callable[[], dict],
    ):
        self.registry = registry
        self.cache = cache
        self.workspace = workspace
        self.settings_getter = settings_getter
        self._subscribers: list[Callable[[RunEvent], None]] = []
        self._runs: dict[str, dict] = {}
        self._cancels: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def subscribe(self, cb: Callable[[RunEvent], None]) -> None:
        self._subscribers.append(cb)

    def unsubscribe(self, cb: Callable[[RunEvent], None]) -> None:
        if cb in self._subscribers:
            self._subscribers.remove(cb)

    def _emit(self, event: RunEvent) -> None:
        self._track(event)
        for cb in list(self._subscribers):
            try:
                cb(event)
            except Exception:
                pass

    def _track(self, e: RunEvent) -> None:
        with self._lock:
            run = self._runs.get(e.run_id)
            if run is None:
                return
            run["events"].append(e.to_json())
            if len(run["events"]) > 2000:
                run["events"] = run["events"][-2000:]
            nodes = run["nodes"]
            if e.type == "node_started":
                nodes[e.node_id] = {"status": "running", "started": e.ts}
            elif e.type == "node_finished":
                info = nodes.setdefault(e.node_id, {})
                info.update(
                    status="finished",
                    cached=e.data.get("cached", False),
                    preview=e.data.get("preview"),
                    duration_ms=int((e.ts - info.get("started", e.ts)) * 1000),
                )
            elif e.type == "node_failed":
                nodes[e.node_id] = {
                    "status": "skipped" if e.data.get("skipped") else "failed",
                    "error": e.data.get("error"),
                    "hint": e.data.get("hint"),
                }
            elif e.type == "run_finished":
                run["status"] = e.data.get("status", "finished")
                run["finished_at"] = e.ts
            elif e.type == "run_cancelled":
                run["status"] = "cancelled"
                run["finished_at"] = e.ts
            elif e.type == "run_failed":
                run["status"] = "error"
                run["finished_at"] = e.ts

    def start(self, wf: Workflow) -> str:
        run_id = uuid.uuid4().hex[:12]
        cancel = threading.Event()
        with self._lock:
            self._runs[run_id] = {
                "id": run_id,
                "workflow_id": wf.id,
                "workflow_name": wf.name,
                "status": "running",
                "started_at": time.time(),
                "finished_at": None,
                "nodes": {},
                "events": [],
            }
            self._cancels[run_id] = cancel

        def work():
            try:
                execute_workflow(
                    wf,
                    self.registry,
                    self.cache,
                    workspace=self.workspace,
                    settings=self.settings_getter(),
                    emit=self._emit,
                    cancel=cancel,
                    run_id=run_id,
                )
            except Exception as exc:
                self._emit(RunEvent("run_failed", run_id, data={"error": str(exc)}))

        threading.Thread(target=work, daemon=True, name=f"axon-run-{run_id}").start()
        return run_id

    def cancel(self, run_id: str) -> bool:
        cancel = self._cancels.get(run_id)
        if cancel is None:
            return False
        cancel.set()
        return True

    def get_run(self, run_id: str) -> dict | None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return None
            return {k: (dict(v) if k == "nodes" else v) for k, v in run.items() if k != "events"} | {
                "nodes": {nid: dict(info) for nid, info in run["nodes"].items()}
            }

    def list_runs(self) -> list[dict]:
        with self._lock:
            return [
                {k: v for k, v in run.items() if k not in ("events", "nodes")}
                for run in sorted(self._runs.values(), key=lambda r: r["started_at"], reverse=True)
            ]
