"""Classical ML pack: scikit-learn and XGBoost models, evaluation, prediction."""

from __future__ import annotations

import pandas as pd

from axon.sdk import ChartSpec, Choice, Dataset, Float, Int, Metrics, Model
from axon.sdk.node import node


def _xy(dataset: Dataset):
    if not dataset.target:
        raise ValueError(
            "This dataset has no target column. Add a 'Set Target' node to choose "
            "which column the model should predict."
        )
    X = dataset.df[dataset.features].select_dtypes("number")
    if X.shape[1] == 0:
        raise ValueError("No numeric feature columns. Add an 'Encode Categoricals' node upstream.")
    return X, dataset.df[dataset.target]


def _fit(ctx, estimator, train: Dataset, framework: str, task: str) -> Model:
    X, y = _xy(train)
    estimator.fit(X, y)
    ctx.log(f"Trained {type(estimator).__name__} on {X.shape[0]} rows, {X.shape[1]} features")
    return Model(obj=estimator, framework=framework, task=task,
                 meta={"features": list(X.columns), "target": train.target})


def _predict_frame(model: Model, dataset: Dataset):
    features = model.meta.get("features")
    X = dataset.df[features] if features else dataset.df[dataset.features].select_dtypes("number")
    if model.framework == "torch":
        from axon.nodes.deep import torch_predict  # lazy; only needed for torch models

        return torch_predict(model, X)
    return model.obj.predict(X)


@node(
    id="ml.linear_regression",
    name="Linear Regression",
    category="Classical ML",
    description="The simplest regression model: a straight-line fit.",
    inputs={"train": "dataset"},
    outputs={"model": "model"},
)
def linear_regression(ctx, train):
    from sklearn.linear_model import LinearRegression

    return {"model": _fit(ctx, LinearRegression(), train, "sklearn", "regression")}


@node(
    id="ml.logistic_regression",
    name="Logistic Regression",
    category="Classical ML",
    description="A fast, reliable baseline for classification.",
    inputs={"train": "dataset"},
    outputs={"model": "model"},
    params={"max_iter": Int(default=1000, min=10)},
)
def logistic_regression(ctx, train, max_iter):
    from sklearn.linear_model import LogisticRegression

    return {"model": _fit(ctx, LogisticRegression(max_iter=max_iter), train, "sklearn", "classification")}


@node(
    id="ml.random_forest",
    name="Random Forest",
    category="Classical ML",
    description="An ensemble of decision trees, a strong default for tabular data.",
    inputs={"train": "dataset"},
    outputs={"model": "model"},
    params={
        "task": Choice(["classification", "regression"], default="classification"),
        "n_estimators": Int(default=100, min=1, help="Number of trees"),
        "max_depth": Int(default=0, min=0, help="0 = unlimited"),
        "seed": Int(default=42),
    },
)
def random_forest(ctx, train, task, n_estimators, max_depth, seed):
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

    cls = RandomForestClassifier if task == "classification" else RandomForestRegressor
    estimator = cls(n_estimators=n_estimators, max_depth=max_depth or None, random_state=seed)
    return {"model": _fit(ctx, estimator, train, "sklearn", task)}


@node(
    id="ml.xgboost",
    name="XGBoost",
    category="Classical ML",
    description="Gradient-boosted trees, often the top performer on tabular data.",
    inputs={"train": "dataset"},
    outputs={"model": "model"},
    params={
        "task": Choice(["classification", "regression"], default="classification"),
        "n_estimators": Int(default=100, min=1),
        "learning_rate": Float(default=0.1, min=0.001, max=1.0),
        "seed": Int(default=42),
    },
    pack="ml-boost",
)
def xgboost(ctx, train, task, n_estimators, learning_rate, seed):
    from xgboost import XGBClassifier, XGBRegressor

    cls = XGBClassifier if task == "classification" else XGBRegressor
    estimator = cls(n_estimators=n_estimators, learning_rate=learning_rate, random_state=seed)
    return {"model": _fit(ctx, estimator, train, "xgboost", task)}


@node(
    id="ml.kmeans",
    name="K-Means Clustering",
    category="Classical ML",
    description="Group similar rows into clusters. No target column is needed.",
    inputs={"train": "dataset"},
    outputs={"model": "model", "labeled": "dataset"},
    params={"clusters": Int(default=3, min=2), "seed": Int(default=42)},
)
def kmeans(ctx, train, clusters, seed):
    from sklearn.cluster import KMeans

    X = train.df[train.features].select_dtypes("number")
    estimator = KMeans(n_clusters=clusters, random_state=seed, n_init=10)
    labels = estimator.fit_predict(X)
    labeled = train.df.copy()
    labeled["cluster"] = labels
    model = Model(obj=estimator, framework="sklearn", task="clustering",
                  meta={"features": list(X.columns)})
    return {"model": model, "labeled": Dataset(df=labeled, target=train.target, meta=train.meta)}


@node(
    id="ml.predict",
    name="Predict",
    category="Classical ML",
    description="Apply a trained model to data; adds a 'prediction' column.",
    inputs={"model": "model", "dataset": "dataset"},
    outputs={"dataset": "dataset"},
)
def predict(ctx, model, dataset):
    preds = _predict_frame(model, dataset)
    df = dataset.df.copy()
    df["prediction"] = preds
    return {"dataset": Dataset(df=df, target=dataset.target, meta=dataset.meta)}


@node(
    id="ml.evaluate",
    name="Evaluate",
    category="Classical ML",
    description="Score a model on held-out test data.",
    inputs={"model": "model", "test": "dataset"},
    outputs={"metrics": "metrics"},
)
def evaluate(ctx, model, test):
    import numpy as np
    from sklearn import metrics as skm

    X, y = _xy(test)
    features = model.meta.get("features")
    if features:
        X = test.df[features]
    preds = _predict_frame(model, test)

    if model.task == "classification":
        values = {
            "accuracy": round(float(skm.accuracy_score(y, preds)), 4),
            "precision": round(float(skm.precision_score(y, preds, average="macro", zero_division=0)), 4),
            "recall": round(float(skm.recall_score(y, preds, average="macro", zero_division=0)), 4),
            "f1": round(float(skm.f1_score(y, preds, average="macro", zero_division=0)), 4),
            "n_test": int(len(y)),
        }
    else:
        values = {
            "r2": round(float(skm.r2_score(y, preds)), 4),
            "mae": round(float(skm.mean_absolute_error(y, preds)), 4),
            "rmse": round(float(np.sqrt(skm.mean_squared_error(y, preds))), 4),
            "n_test": int(len(y)),
        }
    ctx.log(f"Metrics: {values}")
    return {"metrics": Metrics(values=values)}


@node(
    id="ml.confusion_matrix",
    name="Confusion Matrix",
    category="Classical ML",
    description="See exactly which classes the model confuses.",
    inputs={"model": "model", "test": "dataset"},
    outputs={"chart": "chart"},
)
def confusion_matrix(ctx, model, test):
    from sklearn.metrics import confusion_matrix as skcm

    _, y = _xy(test)
    preds = _predict_frame(model, test)
    labels = sorted(pd.unique(pd.concat([pd.Series(y), pd.Series(preds)], ignore_index=True)))
    matrix = skcm(y, preds, labels=labels)
    data = [
        {"x": str(labels[j]), "y": str(labels[i]), "value": int(matrix[i][j])}
        for i in range(len(labels))
        for j in range(len(labels))
    ]
    return {
        "chart": ChartSpec(
            kind="heatmap",
            data=data,
            x="predicted",
            y=["actual"],
            title="Confusion Matrix",
            meta={"labels": [str(l) for l in labels]},
        )
    }
