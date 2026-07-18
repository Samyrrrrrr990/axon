import numpy as np
import pandas as pd

from axon.nodes import data as D


def test_sample_dataset_iris(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    assert ds.df.shape == (150, 5)
    assert ds.target == "target"


def test_sample_dataset_digits(ctx):
    ds = D.sample_dataset(ctx, name="digits")["dataset"]
    assert ds.df.shape[1] == 65  # 64 pixels + target


def test_load_csv(ctx, tmp_path):
    p = tmp_path / "d.csv"
    pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_csv(p, index=False)
    ds = D.load_csv(ctx, path=str(p), delimiter=",", header=True)["dataset"]
    assert list(ds.df.columns) == ["a", "b"]


def test_set_target_and_select_columns(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    ds2 = D.set_target(ctx, dataset=ds, target="target")["dataset"]
    assert ds2.target == "target"
    ds3 = D.select_columns(ctx, dataset=ds2, columns="sepal length (cm), target", mode="keep")["dataset"]
    assert list(ds3.df.columns) == ["sepal length (cm)", "target"]


def test_split_deterministic(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    out1 = D.split(ctx, dataset=ds, test_size=0.2, seed=42)
    out2 = D.split(ctx, dataset=ds, test_size=0.2, seed=42)
    assert out1["train"].df.shape[0] == 120
    assert out1["test"].df.shape[0] == 30
    pd.testing.assert_frame_equal(out1["train"].df, out2["train"].df)


def test_scale_skips_target(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    scaled = D.scale(ctx, dataset=ds, method="standard")["dataset"]
    assert abs(scaled.df[scaled.features[0]].mean()) < 1e-6
    assert set(scaled.df["target"].unique()) == {0, 1, 2}


def test_impute(ctx):
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "t": [0, 1, 0]})
    from axon.sdk import Dataset

    out = D.impute(ctx, dataset=Dataset(df=df, target="t"), strategy="mean")["dataset"]
    assert out.df["a"].isna().sum() == 0
    assert out.df["a"][1] == 2.0


def test_encode_onehot(ctx):
    from axon.sdk import Dataset

    df = pd.DataFrame({"color": ["r", "g", "r"], "t": [0, 1, 0]})
    out = D.encode(ctx, dataset=Dataset(df=df, target="t"), method="onehot")["dataset"]
    assert "color_r" in out.df.columns and "color_g" in out.df.columns
