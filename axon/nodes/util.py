"""Utility pack — the code escape hatch, charts, viewers, and file output."""

from __future__ import annotations

import pickle

from axon.sdk import AnyValue, ChartSpec, Choice, FilePath, Str, Text, TextValue
from axon.sdk.node import node


@node(
    id="util.python_code",
    name="Python Code",
    category="Utility",
    description="The escape hatch: run any Python. Inputs are a, b, c; set `result`.",
    inputs={"a": "any", "b": "any", "c": "any"},
    outputs={"result": "any"},
    params={
        "code": Text(
            default="# a, b, c are your connected inputs (pd and np are imported)\nresult = a",
            help="Set a variable named `result`",
        )
    },
)
def python_code(ctx, a, b, c, code):
    import numpy as np
    import pandas as pd

    namespace = {"a": a, "b": b, "c": c, "pd": pd, "np": np, "ctx": ctx}
    exec(compile(code, "<python-code-node>", "exec"), namespace)
    if "result" not in namespace:
        raise ValueError("Your code must set a variable named `result`.")
    value = namespace["result"]
    return {"result": value if hasattr(value, "preview") else AnyValue(value=value)}


@node(
    id="util.chart",
    name="Chart",
    category="Utility",
    description="Plot columns of a dataset.",
    inputs={"dataset": "dataset"},
    outputs={"chart": "chart"},
    params={
        "x": Str(help="Column for the x-axis", required=True),
        "y": Str(help="Column(s) for the y-axis, comma-separated", required=True),
        "kind": Choice(["line", "bar", "scatter"], default="line"),
        "title": Str(default=""),
    },
)
def chart(ctx, dataset, x, y, kind, title):
    y_cols = [c.strip() for c in y.split(",") if c.strip()]
    for col in [x, *y_cols]:
        if col not in dataset.df.columns:
            raise ValueError(f"No column named '{col}'. Columns: {', '.join(map(str, dataset.df.columns))}")
    df = dataset.df[[x, *y_cols]].head(2000)
    return {
        "chart": ChartSpec(kind=kind, data=df.to_dict(orient="records"), x=x, y=y_cols, title=title)
    }


@node(
    id="util.view_table",
    name="View Table",
    category="Utility",
    description="Inspect a dataset's rows.",
    inputs={"dataset": "dataset"},
    outputs={},
)
def view_table(ctx, dataset):
    return None


@node(
    id="util.view_metrics",
    name="View Metrics",
    category="Utility",
    description="Display metric values.",
    inputs={"metrics": "metrics"},
    outputs={},
)
def view_metrics(ctx, metrics):
    return None


@node(
    id="util.view_image",
    name="View Image",
    category="Utility",
    description="Display an image.",
    inputs={"image": "image"},
    outputs={},
)
def view_image(ctx, image):
    return None


@node(
    id="util.text_input",
    name="Text Input",
    category="Utility",
    description="A piece of text to feed into the graph — a prompt, a question, a task.",
    outputs={"text": "text"},
    params={"text": Text(default="", help="The text to emit")},
)
def text_input(ctx, text):
    return {"text": TextValue(text=text)}


@node(
    id="util.text_output",
    name="Text Output",
    category="Utility",
    description="Display text produced by the graph.",
    inputs={"text": "text"},
    outputs={},
)
def text_output(ctx, text):
    return None


@node(
    id="util.save_file",
    name="Save File",
    category="Utility",
    description="Write a dataset (csv), text (txt), or any object (pickle) to disk.",
    inputs={"value": "any"},
    outputs={},
    params={"path": FilePath(must_exist=False, help="Where to save", required=True)},
)
def save_file(ctx, value, path):
    target = ctx.resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(value, "df"):
        value.df.to_csv(target, index=False)
    elif hasattr(value, "text"):
        target.write_text(value.text)
    else:
        payload = value.value if hasattr(value, "value") else value
        with open(target, "wb") as f:
            pickle.dump(payload, f)
    ctx.log(f"Saved to {target}")
    return None
