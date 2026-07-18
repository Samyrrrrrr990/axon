import json

from axon.sdk.params import Bool, Choice, FilePath, Float, Int, Json, Secret, Str, Text


def test_int_schema():
    schema = Int(default=5, min=1, help="count").schema()
    assert schema == {
        "kind": "int",
        "default": 5,
        "min": 1,
        "max": None,
        "help": "count",
        "required": False,
    }


def test_float_schema():
    schema = Float(default=0.1, min=0.0, max=1.0).schema()
    assert schema["kind"] == "float"
    assert schema["default"] == 0.1
    assert schema["max"] == 1.0


def test_str_and_text():
    assert Str(default="x").schema()["kind"] == "string"
    assert Text(default="body").schema() == {
        "kind": "text",
        "default": "body",
        "help": "",
        "required": False,
    }


def test_bool():
    assert Bool(default=True).schema()["default"] is True


def test_choice():
    schema = Choice(["a", "b"], default="a").schema()
    assert schema["kind"] == "choice"
    assert schema["options"] == ["a", "b"]
    assert schema["default"] == "a"


def test_filepath():
    schema = FilePath(kind="directory", must_exist=False).schema()
    assert schema["kind"] == "filepath"
    assert schema["path_kind"] == "directory"
    assert schema["must_exist"] is False


def test_secret_and_json():
    assert Secret(help="api key").schema()["kind"] == "secret"
    assert Json(default={"a": 1}).schema()["default"] == {"a": 1}


def test_all_schemas_json_serializable():
    for p in [Int(default=1), Float(default=1.0), Str(), Text(), Bool(default=False),
              Choice(["x"], default="x"), FilePath(), Secret(), Json()]:
        json.dumps(p.schema())
