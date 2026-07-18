import json

import numpy as np
import pandas as pd

from axon.sdk.containers import (
    SOCKET_TYPES,
    AnyValue,
    ChartSpec,
    Dataset,
    Metrics,
    Model,
    TextDocs,
    TextValue,
    compatible,
)


def _iris_like():
    return pd.DataFrame(
        {"a": [1.0, 2.0, np.nan], "b": [3, 4, 5], "label": ["x", "y", "x"]}
    )


def test_dataset_preview_shape():
    ds = Dataset(df=_iris_like(), target="label")
    p = ds.preview()
    assert p["type"] == "dataset"
    assert p["columns"] == ["a", "b", "label"]
    assert p["shape"] == [3, 3]
    assert p["target"] == "label"
    json.dumps(p)  # NaN must be sanitized


def test_dataset_features_property():
    ds = Dataset(df=_iris_like(), target="label")
    assert ds.features == ["a", "b"]


def test_metrics_preview_round_trip():
    m = Metrics(values={"accuracy": np.float64(0.95), "n": 3})
    out = json.dumps(m.preview())
    assert "0.95" in out


def test_model_preview():
    m = Model(obj=object(), framework="sklearn", task="classification")
    p = m.preview()
    assert p["framework"] == "sklearn"
    json.dumps(p)


def test_chart_spec_preview_is_self():
    c = ChartSpec(kind="line", data=[{"x": 1, "y": 2}], x="x", y=["y"], title="t")
    p = c.preview()
    assert p["kind"] == "line"
    assert p["data"] == [{"x": 1, "y": 2}]
    json.dumps(p)


def test_text_docs_and_value():
    docs = TextDocs(docs=[{"id": "1", "text": "hello", "meta": {}}])
    assert docs.preview()["count"] == 1
    assert TextValue(text="hi").preview()["text"] == "hi"


def test_compatibility_rules():
    assert compatible("dataset", "dataset")
    assert compatible("dataset", "any")
    assert compatible("any", "model")
    assert not compatible("model", "dataset")


def test_socket_types_registry():
    assert SOCKET_TYPES["dataset"] is Dataset
    assert SOCKET_TYPES["any"] is AnyValue
    for name, cls in SOCKET_TYPES.items():
        assert cls.type_name == name
