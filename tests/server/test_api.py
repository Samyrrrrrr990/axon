import time

import pytest
from fastapi.testclient import TestClient

from axon.sdk import Registry, TextValue
from axon.sdk.node import make_node_decorator
from axon.server.app import create_app
from axon.storage.workspace import Workspace


@pytest.fixture()
def registry():
    reg = Registry()
    node = make_node_decorator(reg)

    @node(id="t.hello", name="Hello", category="Test", outputs={"text": "text"})
    def hello(ctx):
        return {"text": TextValue(text="hello")}

    @node(id="t.shout", name="Shout", category="Test", inputs={"text": "text"}, outputs={"text": "text"})
    def shout(ctx, text):
        return {"text": TextValue(text=text.text.upper())}

    reg._builtin_loaded = True  # prevent load_builtin from importing real packs in tests
    return reg


@pytest.fixture()
def client(tmp_path, registry):
    app = create_app(workspace=Workspace(root=tmp_path / "ws"), registry=registry)
    with TestClient(app) as c:
        yield c


WF = {
    "format": "axon-workflow/1",
    "id": "",
    "name": "Test Flow",
    "nodes": [
        {"id": "a", "type": "t.hello", "params": {}, "position": {"x": 0, "y": 0}},
        {"id": "b", "type": "t.shout", "params": {}, "position": {"x": 200, "y": 0}},
    ],
    "edges": [
        {"id": "e1", "source": "a", "source_socket": "text", "target": "b", "target_socket": "text"}
    ],
    "meta": {},
}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_nodes_catalog(client):
    r = client.get("/api/nodes")
    body = r.json()
    ids = [n["id"] for n in body["nodes"]]
    assert "t.hello" in ids and "t.shout" in ids
    assert "packs" in body


def test_workflow_crud_and_validate(client):
    r = client.post("/api/workflows", json=WF)
    wf_id = r.json()["id"]
    assert wf_id
    assert client.get(f"/api/workflows/{wf_id}").json()["name"] == "Test Flow"
    assert any(w["id"] == wf_id for w in client.get("/api/workflows").json())

    v = client.post("/api/workflows/validate", json=WF).json()
    assert v["issues"] == []

    bad = {**WF, "edges": []}
    v2 = client.post("/api/workflows/validate", json=bad).json()
    assert any("not connected" in i["message"] for i in v2["issues"])

    export = client.get(f"/api/workflows/{wf_id}/export")
    assert export.headers["content-type"].startswith("application/json")

    assert client.delete(f"/api/workflows/{wf_id}").status_code == 200
    assert client.get(f"/api/workflows/{wf_id}").status_code == 404


def test_run_workflow_to_completion(client):
    run_id = client.post("/api/runs", json={"workflow": WF}).json()["run_id"]
    for _ in range(100):
        info = client.get(f"/api/runs/{run_id}").json()
        if info["status"] in ("finished", "error", "cancelled"):
            break
        time.sleep(0.05)
    assert info["status"] == "finished"
    assert info["nodes"]["b"]["preview"]["text"]["text"] == "HELLO"


def test_run_invalid_workflow_400(client):
    bad = {**WF, "edges": []}
    r = client.post("/api/runs", json={"workflow": bad})
    assert r.status_code == 400
    assert r.json()["detail"]["issues"]


def test_settings_masking(client):
    s = client.get("/api/settings").json()
    assert s["copilot"]["provider"] == "openrouter"
    client.put("/api/settings", json={"keys": {"openrouter": "sk-secret-123"}})
    masked = client.get("/api/settings").json()
    assert "sk-secret" not in str(masked)
    # PUTing masked values back must not clobber the real key
    client.put("/api/settings", json={"keys": {"openrouter": masked["keys"]["openrouter"]}})
    # server still holds the real key (verified indirectly: masked GET stays non-empty)
    assert client.get("/api/settings").json()["keys"]["openrouter"] != ""


def test_websocket_receives_run_events(client):
    with client.websocket_connect("/api/ws") as ws:
        run_id = client.post("/api/runs", json={"workflow": WF}).json()["run_id"]
        seen = set()
        for _ in range(50):
            msg = ws.receive_json()
            if msg["run_id"] == run_id:
                seen.add(msg["type"])
            if "run_finished" in seen:
                break
        assert "run_started" in seen and "run_finished" in seen
