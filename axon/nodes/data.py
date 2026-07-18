"""Data pack: loading, sampling, splitting, and cleaning tabular data."""

from __future__ import annotations

import pandas as pd

from axon.sdk import Bool, Choice, Dataset, FilePath, Float, Int, Str, TextDocs
from axon.sdk.node import node


@node(
    id="data.load_csv",
    name="Load CSV",
    category="Data",
    description="Load a CSV file into a dataset.",
    outputs={"dataset": "dataset"},
    params={
        "path": FilePath(kind="file", help="Path to a .csv file"),
        "delimiter": Str(default=","),
        "header": Bool(default=True, help="First row contains column names"),
    },
)
def load_csv(ctx, path, delimiter, header):
    df = pd.read_csv(ctx.resolve_path(path), sep=delimiter, header=0 if header else None)
    ctx.log(f"Loaded {df.shape[0]} rows × {df.shape[1]} columns")
    return {"dataset": Dataset(df=df)}


@node(
    id="data.load_excel",
    name="Load Excel",
    category="Data",
    description="Load the first sheet of an Excel file.",
    outputs={"dataset": "dataset"},
    params={"path": FilePath(kind="file", help="Path to an .xlsx file"), "sheet": Str(default="")},
)
def load_excel(ctx, path, sheet):
    df = pd.read_excel(ctx.resolve_path(path), sheet_name=sheet or 0)
    return {"dataset": Dataset(df=df)}


@node(
    id="data.sample_dataset",
    name="Sample Dataset",
    category="Data",
    description="Classic datasets for experimenting. No files required.",
    outputs={"dataset": "dataset"},
    params={
        "name": Choice(
            ["iris", "wine", "breast_cancer", "diabetes", "california_housing", "digits"],
            default="iris",
        )
    },
)
def sample_dataset(ctx, name):
    from sklearn import datasets as skd

    loaders = {
        "iris": skd.load_iris,
        "wine": skd.load_wine,
        "breast_cancer": skd.load_breast_cancer,
        "diabetes": skd.load_diabetes,
        "digits": skd.load_digits,
    }
    if name == "california_housing":
        bunch = skd.fetch_california_housing(as_frame=True)
        df = bunch.frame.rename(columns={"MedHouseVal": "target"})
    else:
        bunch = loaders[name](as_frame=name != "digits")
        if name == "digits":
            df = pd.DataFrame(bunch.data, columns=[f"px{i}" for i in range(bunch.data.shape[1])])
            df["target"] = bunch.target
        else:
            df = bunch.frame
    ctx.log(f"{name}: {df.shape[0]} rows × {df.shape[1]} columns")
    return {"dataset": Dataset(df=df, target="target")}


@node(
    id="data.huggingface_dataset",
    name="Hugging Face Dataset",
    category="Data",
    description="Load a text dataset from the Hugging Face Hub.",
    outputs={"docs": "docs"},
    params={
        "name": Str(default="Abirate/english_quotes", help="Dataset name on the Hub"),
        "split": Str(default="train"),
        "text_column": Str(default="quote"),
        "limit": Int(default=200, min=1, help="Max rows to load"),
    },
    pack="finetune",
)
def huggingface_dataset(ctx, name, split, text_column, limit):
    from datasets import load_dataset

    dataset = load_dataset(name, split=split)
    docs = []
    for i, row in enumerate(dataset):
        if i >= limit:
            break
        docs.append({"id": str(i), "text": str(row[text_column]), "meta": {}})
    ctx.log(f"Loaded {len(docs)} documents from {name}")
    return {"docs": TextDocs(docs=docs)}


@node(
    id="data.set_target",
    name="Set Target",
    category="Data",
    description="Choose which column the model should learn to predict.",
    inputs={"dataset": "dataset"},
    outputs={"dataset": "dataset"},
    params={"target": Str(help="Column name to predict", required=True)},
)
def set_target(ctx, dataset, target):
    if target not in dataset.df.columns:
        raise ValueError(f"No column named '{target}'. Columns: {', '.join(map(str, dataset.df.columns))}")
    return {"dataset": Dataset(df=dataset.df, target=target, meta=dataset.meta)}


@node(
    id="data.select_columns",
    name="Select Columns",
    category="Data",
    description="Keep or drop specific columns.",
    inputs={"dataset": "dataset"},
    outputs={"dataset": "dataset"},
    params={
        "columns": Str(help="Comma-separated column names", required=True),
        "mode": Choice(["keep", "drop"], default="keep"),
    },
)
def select_columns(ctx, dataset, columns, mode):
    cols = [c.strip() for c in columns.split(",") if c.strip()]
    missing = [c for c in cols if c not in dataset.df.columns]
    if missing:
        raise ValueError(f"Columns not found: {', '.join(missing)}")
    df = dataset.df[cols] if mode == "keep" else dataset.df.drop(columns=cols)
    target = dataset.target if dataset.target in df.columns else None
    return {"dataset": Dataset(df=df, target=target, meta=dataset.meta)}


@node(
    id="data.split",
    name="Train / Test Split",
    category="Data",
    description="Split into a training set and a held-out test set.",
    inputs={"dataset": "dataset"},
    outputs={"train": "dataset", "test": "dataset"},
    params={"test_size": Float(default=0.2, min=0.05, max=0.95), "seed": Int(default=42)},
)
def split(ctx, dataset, test_size, seed):
    from sklearn.model_selection import train_test_split

    train_df, test_df = train_test_split(dataset.df, test_size=test_size, random_state=seed)
    ctx.log(f"train: {train_df.shape[0]} rows, test: {test_df.shape[0]} rows")
    return {
        "train": Dataset(df=train_df.reset_index(drop=True), target=dataset.target, meta=dataset.meta),
        "test": Dataset(df=test_df.reset_index(drop=True), target=dataset.target, meta=dataset.meta),
    }


@node(
    id="data.scale",
    name="Scale Features",
    category="Data",
    description="Normalize numeric features so no column dominates.",
    inputs={"dataset": "dataset"},
    outputs={"dataset": "dataset"},
    params={"method": Choice(["standard", "minmax"], default="standard")},
)
def scale(ctx, dataset, method):
    from sklearn.preprocessing import MinMaxScaler, StandardScaler

    df = dataset.df.copy()
    numeric = [c for c in dataset.features if pd.api.types.is_numeric_dtype(df[c])]
    scaler = StandardScaler() if method == "standard" else MinMaxScaler()
    df[numeric] = scaler.fit_transform(df[numeric])
    return {"dataset": Dataset(df=df, target=dataset.target, meta=dataset.meta)}


@node(
    id="data.encode",
    name="Encode Categoricals",
    category="Data",
    description="Turn text categories into numbers models can use.",
    inputs={"dataset": "dataset"},
    outputs={"dataset": "dataset"},
    params={"method": Choice(["onehot", "label"], default="onehot")},
)
def encode(ctx, dataset, method):
    df = dataset.df.copy()
    cat_cols = [
        c
        for c in dataset.features
        if pd.api.types.is_string_dtype(df[c]) or isinstance(df[c].dtype, pd.CategoricalDtype)
    ]
    if not cat_cols:
        ctx.log("No categorical feature columns found; passing data through unchanged")
        return {"dataset": dataset}
    if method == "onehot":
        df = pd.get_dummies(df, columns=cat_cols, dtype=int)
    else:
        for c in cat_cols:
            df[c] = df[c].astype("category").cat.codes
    return {"dataset": Dataset(df=df, target=dataset.target, meta=dataset.meta)}


@node(
    id="data.impute",
    name="Handle Missing",
    category="Data",
    description="Fill in or drop missing values.",
    inputs={"dataset": "dataset"},
    outputs={"dataset": "dataset"},
    params={"strategy": Choice(["mean", "median", "most_frequent", "drop_rows"], default="mean")},
)
def impute(ctx, dataset, strategy):
    df = dataset.df.copy()
    if strategy == "drop_rows":
        df = df.dropna().reset_index(drop=True)
    else:
        for c in df.columns:
            if df[c].isna().any():
                if pd.api.types.is_numeric_dtype(df[c]) and strategy in ("mean", "median"):
                    fill = df[c].mean() if strategy == "mean" else df[c].median()
                else:
                    fill = df[c].mode().iloc[0]
                df[c] = df[c].fillna(fill)
    return {"dataset": Dataset(df=df, target=dataset.target, meta=dataset.meta)}
