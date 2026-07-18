"""The Axon server: REST + WebSocket API plus the built web UI, all on one port."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

import axon
from axon.engine.cache import Cache
from axon.engine.events import RunEvent
from axon.engine.graph import Workflow, validate_workflow
from axon.engine.runs import RunManager
from axon.sdk.registry import REGISTRY, Registry
from axon.server.packs import install_pack, pack_status
from axon.storage.history import RunHistory
from axon.storage.workflows import WorkflowStore
from axon.storage.workspace import Workspace

MASK = "••••••••"


class WSHub:
    """Fans RunEvents (produced on worker threads) out to websocket clients (on the event loop)."""

    def __init__(self):
        self.clients: set[WebSocket] = set()
        self.loop: asyncio.AbstractEventLoop | None = None

    def emit_threadsafe(self, event: RunEvent) -> None:
        if self.loop is None or not self.clients:
            return
        payload = json.dumps(event.to_json())
        self.loop.call_soon_threadsafe(lambda: asyncio.ensure_future(self._send_all(payload)))

    async def _send_all(self, payload: str) -> None:
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)


def create_app(workspace: Workspace | None = None, registry: Registry | None = None) -> FastAPI:
    ws = workspace or Workspace()
    reg = registry or REGISTRY
    reg.load_builtin()

    cache = Cache(ws.cache_dir)
    store = WorkflowStore(ws.workflows_dir)
    history = RunHistory(ws.db_path)
    hub = WSHub()
    runs = RunManager(reg, cache, ws.root, settings_getter=lambda: ws.settings)
    runs.subscribe(history.record_event)
    runs.subscribe(hub.emit_threadsafe)

    app = FastAPI(title="Axon", version=axon.__version__)
    app.state.workspace = ws
    app.state.runs = runs

    @app.on_event("startup")
    async def _capture_loop():
        hub.loop = asyncio.get_running_loop()

    # ---- meta ----

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": axon.__version__}

    @app.get("/api/nodes")
    def nodes():
        return {"nodes": reg.catalog(), "packs": pack_status()}

    # ---- workflows ----

    @app.get("/api/workflows")
    def list_workflows():
        return store.list()

    @app.post("/api/workflows")
    def create_workflow(wf: Workflow):
        return store.save(wf).model_dump()

    @app.get("/api/workflows/{wf_id}")
    def get_workflow(wf_id: str):
        try:
            return store.get(wf_id).model_dump()
        except KeyError:
            raise HTTPException(404, f"No workflow {wf_id}")

    @app.put("/api/workflows/{wf_id}")
    def update_workflow(wf_id: str, wf: Workflow):
        wf.id = wf_id
        return store.save(wf).model_dump()

    @app.delete("/api/workflows/{wf_id}")
    def delete_workflow(wf_id: str):
        store.delete(wf_id)
        return {"ok": True}

    @app.post("/api/workflows/validate")
    def validate(wf: Workflow):
        issues = validate_workflow(wf, reg)
        return {"issues": [i.model_dump() for i in issues]}

    @app.post("/api/workflows/import")
    async def import_workflow(file: UploadFile):
        try:
            wf = store.import_file(await file.read())
        except (ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(400, str(exc))
        return wf.model_dump()

    @app.get("/api/workflows/{wf_id}/export")
    def export_workflow(wf_id: str):
        try:
            content = store.export(wf_id)
        except KeyError:
            raise HTTPException(404, f"No workflow {wf_id}")
        return Response(
            content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{wf_id}.axon.json"'},
        )

    # ---- runs ----

    @app.post("/api/runs")
    def start_run(body: dict):
        if body.get("workflow"):
            wf = Workflow.model_validate(body["workflow"])
        elif body.get("workflow_id"):
            try:
                wf = store.get(body["workflow_id"])
            except KeyError:
                raise HTTPException(404, "No such workflow")
        else:
            raise HTTPException(400, "Provide workflow or workflow_id")
        issues = [i for i in validate_workflow(wf, reg) if i.level == "error"]
        if issues:
            raise HTTPException(400, {"issues": [i.model_dump() for i in issues]})
        return {"run_id": runs.start(wf)}

    @app.get("/api/runs")
    def list_runs():
        live = {r["id"]: r for r in runs.list_runs()}
        stored = history.list_runs()
        merged = list(live.values()) + [r for r in stored if r["id"] not in live]
        return merged[:50]

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str):
        info = runs.get_run(run_id) or history.get_run(run_id)
        if info is None:
            raise HTTPException(404, "No such run")
        return info

    @app.post("/api/runs/{run_id}/cancel")
    def cancel_run(run_id: str):
        return {"cancelled": runs.cancel(run_id)}

    # ---- settings ----

    def _mask(settings: dict) -> dict:
        masked = json.loads(json.dumps(settings))
        for k, v in masked.get("keys", {}).items():
            if v:
                masked["keys"][k] = MASK
        return masked

    @app.get("/api/settings")
    def get_settings():
        return _mask(ws.settings)

    @app.put("/api/settings")
    def put_settings(update: dict):
        current = ws.settings
        for key, value in update.items():
            if key == "keys":
                for kname, kval in value.items():
                    if kval != MASK:  # masked value = unchanged
                        current["keys"][kname] = kval
            elif isinstance(value, dict) and isinstance(current.get(key), dict):
                current[key].update(value)
            else:
                current[key] = value
        ws.save_settings(current)
        return _mask(current)

    # ---- packs ----

    @app.post("/api/packs/{name}/install", status_code=202)
    def packs_install(name: str):
        if name not in pack_status():
            raise HTTPException(404, f"Unknown pack {name}")
        threading.Thread(
            target=lambda: install_pack(name, hub.emit_threadsafe), daemon=True
        ).start()
        return {"installing": name}

    # ---- examples ----

    def _examples_dir() -> Path:
        return Path(__file__).resolve().parents[2] / "examples"

    @app.get("/api/examples")
    def list_examples():
        out = []
        d = _examples_dir()
        if d.is_dir():
            for p in sorted(d.glob("*.axon.json")):
                try:
                    data = json.loads(p.read_text())
                    out.append(
                        {
                            "name": p.stem,
                            "title": data.get("name", p.stem),
                            "description": data.get("meta", {}).get("description", ""),
                            "domain": data.get("meta", {}).get("domain", ""),
                            "requires_packs": data.get("meta", {}).get("requires_packs", []),
                            "requires_keys": data.get("meta", {}).get("requires_keys", []),
                            "node_count": len(data.get("nodes", [])),
                        }
                    )
                except Exception:
                    continue
        return out

    @app.post("/api/examples/{name}/open")
    def open_example(name: str):
        path = _examples_dir() / f"{name}.axon.json"
        if not path.exists():
            raise HTTPException(404, f"No example {name}")
        wf = store.import_file(path)
        wf.meta["base_dir"] = str(_examples_dir())
        store.save(wf)
        return wf.model_dump()

    # ---- websocket ----

    @app.websocket("/api/ws")
    async def websocket(sock: WebSocket):
        await sock.accept()
        hub.clients.add(sock)
        try:
            while True:
                await sock.receive_text()  # keepalive pings; content ignored
        except WebSocketDisconnect:
            pass
        finally:
            hub.clients.discard(sock)

    # ---- static frontend ----

    dist = Path(__file__).resolve().parents[2] / "web" / "dist"
    if dist.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}")
        def spa(path: str, request: Request):
            file = dist / path
            if path and file.is_file():
                return FileResponse(file)
            return FileResponse(dist / "index.html")

    return app
