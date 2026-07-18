import threading

import pytest

torch = pytest.importorskip("torch")

from axon.nodes import data as D
from axon.nodes import deep as DL
from axon.nodes import ml as M
from axon.sdk.context import NodeContext


def _iris_split(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    return D.split(ctx, dataset=ds, test_size=0.3, seed=1)


def test_mlp_arch_spec(ctx):
    arch = DL.mlp(ctx, hidden="64,32", activation="relu", dropout=0.1)["arch"]
    assert arch.value == {"kind": "mlp", "hidden": [64, 32], "activation": "relu", "dropout": 0.1}


def test_cnn_arch_spec(ctx):
    arch = DL.cnn(ctx, channels="8,16", kernel=3)["arch"]
    assert arch.value["kind"] == "cnn"
    assert arch.value["channels"] == [8, 16]


def test_trainer_learns_and_streams_progress(recording_ctx):
    parts = _iris_split(recording_ctx)
    arch = DL.mlp(recording_ctx, hidden="32", activation="relu", dropout=0.0)["arch"]
    model = DL.trainer(
        recording_ctx, train=parts["train"], arch=arch,
        epochs=8, lr=0.05, batch_size=16, task="classification", seed=0,
    )["model"]
    progress = [e for e in recording_ctx.events if e[0] == "progress" and e[2]]
    assert len(progress) >= 8
    losses = [e[2]["loss"] for e in progress]
    assert losses[-1] < losses[0]
    metrics = DL.evaluate(recording_ctx, model=model, test=parts["test"])["metrics"]
    assert metrics.values["accuracy"] > 0.6


def test_trainer_regression(ctx):
    ds = D.sample_dataset(ctx, name="diabetes")["dataset"]
    parts = D.split(ctx, dataset=ds, test_size=0.3, seed=1)
    arch = DL.mlp(ctx, hidden="32", activation="relu", dropout=0.0)["arch"]
    model = DL.trainer(ctx, train=parts["train"], arch=arch, epochs=3, lr=0.01,
                       batch_size=32, task="regression", seed=0)["model"]
    metrics = DL.evaluate(ctx, model=model, test=parts["test"])["metrics"]
    assert "rmse" in metrics.values


def test_predict_handles_torch_models(ctx):
    parts = _iris_split(ctx)
    arch = DL.mlp(ctx, hidden="32", activation="relu", dropout=0.0)["arch"]
    model = DL.trainer(ctx, train=parts["train"], arch=arch, epochs=3, lr=0.05,
                       batch_size=16, task="classification", seed=0)["model"]
    out = M.predict(ctx, model=model, dataset=parts["test"])["dataset"]
    assert "prediction" in out.df.columns


def test_trainer_cancellation(tmp_path):
    cancel = threading.Event()
    ctx = NodeContext(workspace=tmp_path, settings={}, cancel_event=cancel)
    parts = _iris_split(ctx)
    arch = DL.mlp(ctx, hidden="16", activation="relu", dropout=0.0)["arch"]
    cancel.set()
    model = DL.trainer(ctx, train=parts["train"], arch=arch, epochs=50, lr=0.01,
                       batch_size=8, task="classification", seed=0)["model"]
    assert model.meta.get("epochs_completed", 50) < 50


def test_export_pickle(ctx, tmp_path):
    parts = _iris_split(ctx)
    arch = DL.mlp(ctx, hidden="16", activation="relu", dropout=0.0)["arch"]
    model = DL.trainer(ctx, train=parts["train"], arch=arch, epochs=2, lr=0.05,
                       batch_size=16, task="classification", seed=0)["model"]
    out = DL.export(ctx, model=model, format="pickle", path=str(tmp_path / "model.pkl"))
    assert (tmp_path / "model.pkl").exists()
