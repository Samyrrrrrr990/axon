"""Socket payload containers. Everything that flows over a wire between nodes is one of these.

Each container has a ``type_name`` (the socket type string used in node declarations)
and a ``preview()`` returning a small JSON-safe dict for the UI.
"""

from __future__ import annotations

import base64
import io
import math
from dataclasses import dataclass, field
from typing import Any, ClassVar


def _jsonify(value: Any) -> Any:
    """Coerce numpy scalars / NaN / arbitrary objects into JSON-safe values."""
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        return None if (math.isnan(value) or math.isinf(value)) else value
    if hasattr(value, "item"):  # numpy scalar
        return _jsonify(value.item())
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    return str(value)


@dataclass
class Dataset:
    df: Any  # pandas DataFrame
    target: str | None = None
    meta: dict = field(default_factory=dict)

    type_name: ClassVar[str] = "dataset"

    @property
    def features(self) -> list[str]:
        return [c for c in self.df.columns if c != self.target]

    def preview(self) -> dict:
        head = self.df.head(50)
        return {
            "type": self.type_name,
            "columns": [str(c) for c in self.df.columns],
            "dtypes": {str(c): str(t) for c, t in self.df.dtypes.items()},
            "shape": [int(self.df.shape[0]), int(self.df.shape[1])],
            "target": self.target,
            "rows": _jsonify(head.to_dict(orient="records")),
        }


@dataclass
class Model:
    obj: Any
    framework: str  # sklearn | xgboost | torch | hf
    task: str = ""  # classification | regression | clustering | causal-lm
    meta: dict = field(default_factory=dict)

    type_name: ClassVar[str] = "model"

    def preview(self) -> dict:
        return {
            "type": self.type_name,
            "framework": self.framework,
            "task": self.task,
            "model_class": type(self.obj).__name__,
            "meta": _jsonify(self.meta),
        }


@dataclass
class Metrics:
    values: dict

    type_name: ClassVar[str] = "metrics"

    def preview(self) -> dict:
        return {"type": self.type_name, "values": _jsonify(self.values)}


@dataclass
class TextDocs:
    docs: list[dict]  # each: {"id": str, "text": str, "meta": dict}

    type_name: ClassVar[str] = "docs"

    def preview(self) -> dict:
        sample = [
            {"id": d.get("id", str(i)), "text": str(d.get("text", ""))[:400]}
            for i, d in enumerate(self.docs[:10])
        ]
        return {"type": self.type_name, "count": len(self.docs), "sample": sample}


@dataclass
class Embeddings:
    vectors: Any  # numpy ndarray (n_docs, dim)
    docs: TextDocs

    type_name: ClassVar[str] = "embeddings"

    def preview(self) -> dict:
        return {
            "type": self.type_name,
            "count": int(self.vectors.shape[0]),
            "dim": int(self.vectors.shape[1]),
        }


@dataclass
class VectorStoreRef:
    path: str
    collection: str

    type_name: ClassVar[str] = "vectorstore"

    def preview(self) -> dict:
        return {"type": self.type_name, "collection": self.collection}


@dataclass
class ChartSpec:
    kind: str  # line | bar | scatter | heatmap
    data: list[dict]
    x: str = ""
    y: list[str] = field(default_factory=list)
    title: str = ""
    meta: dict = field(default_factory=dict)

    type_name: ClassVar[str] = "chart"

    def preview(self) -> dict:
        return {
            "type": self.type_name,
            "kind": self.kind,
            "data": _jsonify(self.data[:2000]),
            "x": self.x,
            "y": self.y,
            "title": self.title,
            "meta": _jsonify(self.meta),
        }


@dataclass
class TextValue:
    text: str

    type_name: ClassVar[str] = "text"

    def preview(self) -> dict:
        return {"type": self.type_name, "text": str(self.text)[:8000]}


@dataclass
class ImageRef:
    path: str
    caption: str = ""

    type_name: ClassVar[str] = "image"

    def preview(self) -> dict:
        thumb = None
        try:
            from PIL import Image  # optional; previews degrade gracefully without pillow

            img = Image.open(self.path)
            img.thumbnail((128, 128))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            thumb = base64.b64encode(buf.getvalue()).decode()
        except Exception:
            pass
        return {"type": self.type_name, "path": self.path, "caption": self.caption, "thumbnail": thumb}


@dataclass
class AnyValue:
    value: Any

    type_name: ClassVar[str] = "any"

    def preview(self) -> dict:
        return {"type": self.type_name, "repr": repr(self.value)[:2000]}


SOCKET_TYPES: dict[str, type] = {
    cls.type_name: cls
    for cls in [
        Dataset,
        Model,
        Metrics,
        TextDocs,
        Embeddings,
        VectorStoreRef,
        ChartSpec,
        TextValue,
        ImageRef,
        AnyValue,
    ]
}


def compatible(src_type: str, dst_type: str) -> bool:
    """Whether a wire from a socket of src_type may plug into dst_type."""
    return src_type == dst_type or dst_type == "any" or src_type == "any"
