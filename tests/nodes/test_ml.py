from axon.nodes import data as D
from axon.nodes import ml as M


def _iris_split(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    return D.split(ctx, dataset=ds, test_size=0.3, seed=1)


def test_random_forest_classification(ctx):
    parts = _iris_split(ctx)
    model = M.random_forest(ctx, train=parts["train"], task="classification",
                            n_estimators=30, max_depth=0, seed=7)["model"]
    metrics = M.evaluate(ctx, model=model, test=parts["test"])["metrics"]
    assert metrics.values["accuracy"] > 0.8


def test_linear_and_logistic(ctx):
    parts = _iris_split(ctx)
    linear = M.linear_regression(ctx, train=parts["train"])["model"]
    assert linear.framework == "sklearn"
    logistic = M.logistic_regression(ctx, train=parts["train"], max_iter=500)["model"]
    m = M.evaluate(ctx, model=logistic, test=parts["test"])["metrics"]
    assert m.values["accuracy"] > 0.8


def test_regression_metrics(ctx):
    ds = D.sample_dataset(ctx, name="diabetes")["dataset"]
    parts = D.split(ctx, dataset=ds, test_size=0.3, seed=1)
    model = M.random_forest(ctx, train=parts["train"], task="regression",
                            n_estimators=30, max_depth=0, seed=7)["model"]
    metrics = M.evaluate(ctx, model=model, test=parts["test"])["metrics"].values
    assert "r2" in metrics and "rmse" in metrics


def test_predict_adds_column(ctx):
    parts = _iris_split(ctx)
    model = M.logistic_regression(ctx, train=parts["train"], max_iter=500)["model"]
    out = M.predict(ctx, model=model, dataset=parts["test"])["dataset"]
    assert "prediction" in out.df.columns


def test_kmeans(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    out = M.kmeans(ctx, train=ds, clusters=3, seed=0)
    assert "cluster" in out["labeled"].df.columns
    assert out["labeled"].df["cluster"].nunique() == 3


def test_confusion_matrix_chart(ctx):
    parts = _iris_split(ctx)
    model = M.logistic_regression(ctx, train=parts["train"], max_iter=500)["model"]
    chart = M.confusion_matrix(ctx, model=model, test=parts["test"])["chart"]
    assert chart.kind == "heatmap"
    assert len(chart.data) == 9  # 3 classes -> 3x3 cells
