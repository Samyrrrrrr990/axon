import json

from axon.engine.events import RunEvent
from axon.engine.graph import NodeInstance, Workflow
from axon.storage.history import RunHistory
from axon.storage.workflows import WorkflowStore
from axon.storage.workspace import Workspace


def test_workspace_creates_dirs_and_default_settings(tmp_path):
    ws = Workspace(root=tmp_path / "home")
    assert ws.cache_dir.is_dir()
    assert ws.workflows_dir.is_dir()
    assert ws.data_dir.is_dir()
    assert ws.settings["copilot"]["provider"] == "openrouter"
    assert "free" in ws.settings["copilot"]["model"]


def test_workspace_settings_round_trip(tmp_path):
    ws = Workspace(root=tmp_path / "home")
    s = ws.settings
    s["keys"]["openrouter"] = "sk-test"
    ws.save_settings(s)
    ws2 = Workspace(root=tmp_path / "home")
    assert ws2.settings["keys"]["openrouter"] == "sk-test"


def test_workspace_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("AXON_HOME", str(tmp_path / "custom"))
    ws = Workspace()
    assert str(ws.root).endswith("custom")


def test_workflow_store_crud(tmp_path):
    store = WorkflowStore(tmp_path)
    wf = Workflow(name="My Flow", nodes=[NodeInstance(id="a", type="t.x")], edges=[])
    saved = store.save(wf)
    assert saved.id
    assert store.get(saved.id).name == "My Flow"
    assert [w["id"] for w in store.list()] == [saved.id]
    saved.name = "Renamed"
    store.save(saved)
    assert store.get(saved.id).name == "Renamed"
    store.delete(saved.id)
    assert store.list() == []


def test_import_assigns_fresh_id_and_export_no_abs_paths(tmp_path):
    store = WorkflowStore(tmp_path)
    wf = Workflow(id="original", name="Shared", nodes=[], edges=[])
    imported = store.import_file(wf.model_dump_json().encode())
    assert imported.id != "original"
    out = store.export(imported.id)
    assert "/Users/" not in out and "\\\\" not in out
    assert json.loads(out)["format"] == "axon-workflow/1"


def test_import_rejects_bad_format(tmp_path):
    store = WorkflowStore(tmp_path)
    try:
        store.import_file(b'{"format": "something-else", "nodes": []}')
        raise AssertionError("should have raised")
    except ValueError as exc:
        assert "format" in str(exc)


def test_run_history_records_events(tmp_path):
    h = RunHistory(tmp_path / "runs.db")
    events = [
        RunEvent("run_started", "r1", data={"workflow_id": "w1", "name": "Flow"}),
        RunEvent("node_started", "r1", "a", {"name": "Load"}),
        RunEvent("node_finished", "r1", "a", {"cached": False}),
        RunEvent("node_failed", "r1", "b", {"error": "boom"}),
        RunEvent("run_finished", "r1", data={"status": "error"}),
    ]
    for e in events:
        h.record_event(e)
    runs = h.list_runs()
    assert len(runs) == 1
    assert runs[0]["status"] == "error"
    detail = h.get_run("r1")
    statuses = {n["node_id"]: n["status"] for n in detail["nodes"]}
    assert statuses == {"a": "finished", "b": "failed"}
