from axon.engine.cache import Cache
from axon.sdk import TextValue


def test_same_config_same_key(tmp_path):
    c = Cache(tmp_path)
    k1 = c.key("t.node", {"a": 1}, ["up1"], "0.1.0")
    k2 = c.key("t.node", {"a": 1}, ["up1"], "0.1.0")
    assert k1 == k2


def test_param_change_changes_key(tmp_path):
    c = Cache(tmp_path)
    assert c.key("t.node", {"a": 1}, [], "0.1.0") != c.key("t.node", {"a": 2}, [], "0.1.0")


def test_upstream_change_changes_key(tmp_path):
    c = Cache(tmp_path)
    assert c.key("t.node", {}, ["k1"], "0.1.0") != c.key("t.node", {}, ["k2"], "0.1.0")


def test_put_get_round_trip(tmp_path):
    c = Cache(tmp_path)
    key = c.key("t.node", {}, [], "0.1.0")
    c.put(key, {"out": TextValue(text="hello")})
    got = c.get(key)
    assert got["out"].text == "hello"


def test_get_missing_returns_none(tmp_path):
    assert Cache(tmp_path).get("nope") is None


def test_unpicklable_output_skips_cache(tmp_path):
    c = Cache(tmp_path)
    key = c.key("t.node", {}, [], "0.1.0")
    c.put(key, {"out": lambda: 1})  # lambdas don't pickle
    assert c.get(key) is None


def test_clear(tmp_path):
    c = Cache(tmp_path)
    key = c.key("t.n", {}, [], "0")
    c.put(key, {"out": TextValue(text="x")})
    c.clear()
    assert c.get(key) is None
