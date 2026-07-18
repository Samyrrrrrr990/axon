import pytest

from axon.nodes import data as D
from axon.nodes import util as U
from axon.sdk import Metrics, TextValue


def test_python_code_node(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    out = U.python_code(ctx, a=ds, b=None, c=None, code="result = a.df.shape[0] * 2")
    assert out["result"].value == 300


def test_python_code_error_reports_line(ctx):
    with pytest.raises(Exception) as err:
        U.python_code(ctx, a=None, b=None, c=None, code="x = 1\nboom()")
    assert "boom" in str(err.value)


def test_python_code_requires_result(ctx):
    with pytest.raises(ValueError, match="result"):
        U.python_code(ctx, a=None, b=None, c=None, code="x = 1")


def test_chart_node(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    chart = U.chart(ctx, dataset=ds, x="sepal length (cm)",
                    y="sepal width (cm)", kind="scatter", title="Iris")["chart"]
    assert chart.kind == "scatter"
    assert len(chart.data) == 150
    assert chart.y == ["sepal width (cm)"]


def test_text_nodes(ctx):
    out = U.text_input(ctx, text="hello world")["text"]
    assert isinstance(out, TextValue)
    U.text_output(ctx, text=out)  # returns nothing, must not raise


def test_view_nodes_pass_through(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    assert U.view_table(ctx, dataset=ds) is None
    assert U.view_metrics(ctx, metrics=Metrics(values={"a": 1})) is None


def test_save_file(ctx, tmp_path):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    path = tmp_path / "out.csv"
    U.save_file(ctx, value=ds, path=str(path))
    assert path.exists() and path.stat().st_size > 100
