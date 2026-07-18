import json
import threading
from pathlib import Path

import pytest

from axon.engine.cache import Cache
from axon.engine.executor import execute_workflow
from axon.engine.graph import Workflow, validate_workflow
from axon.sdk.registry import REGISTRY

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
ALL = sorted(EXAMPLES.glob("*.axon.json"))


@pytest.fixture(scope="module", autouse=True)
def _load_registry():
    REGISTRY.load_builtin()


@pytest.mark.parametrize("path", ALL, ids=[p.stem for p in ALL])
def test_example_is_valid(path):
    wf = Workflow.model_validate_json(path.read_text())
    assert wf.format == "axon-workflow/1"
    assert wf.meta.get("description")
    issues = [i for i in validate_workflow(wf, REGISTRY) if i.level == "error"]
    unknown = [i for i in issues if "Unknown node type" in i.message]
    if unknown:
        pytest.skip(f"needs uninstalled pack: {unknown[0].message}")
    assert issues == [], [i.message for i in issues]


def _run(path: Path, tmp_path: Path):
    wf = Workflow.model_validate_json(path.read_text())
    wf.meta["base_dir"] = str(EXAMPLES)
    events = []
    execute_workflow(
        wf, REGISTRY, Cache(tmp_path / "cache"), workspace=tmp_path, settings={},
        emit=events.append, cancel=threading.Event(), run_id="test",
    )
    return events


def test_house_prices_runs_to_completion(tmp_path):
    events = _run(EXAMPLES / "house-prices.axon.json", tmp_path)
    assert events[-1].type == "run_finished"
    assert events[-1].data["status"] == "finished", [
        (e.node_id, e.data.get("error")) for e in events if e.type == "node_failed"
    ]
    metrics = next(
        e.data["preview"]["metrics"]["values"]
        for e in events
        if e.type == "node_finished" and e.node_id == "eval"
    )
    assert metrics["r2"] > 0.5


def test_digit_classifier_runs_to_completion(tmp_path):
    pytest.importorskip("torch")
    events = _run(EXAMPLES / "digit-classifier.axon.json", tmp_path)
    assert events[-1].data.get("status") == "finished", [
        (e.node_id, e.data.get("error")) for e in events if e.type == "node_failed"
    ]
    metrics = next(
        e.data["preview"]["metrics"]["values"]
        for e in events
        if e.type == "node_finished" and e.node_id == "eval"
    )
    assert metrics["accuracy"] > 0.85
