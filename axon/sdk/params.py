"""Parameter declarations for nodes. Each renders to a JSON schema the UI turns into a form field."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Param:
    default: Any = None
    help: str = ""
    required: bool = False

    kind = "param"

    def schema(self) -> dict:
        return {
            "kind": self.kind,
            "default": self.default,
            "help": self.help,
            "required": self.required,
        }


@dataclass
class Int(Param):
    default: int = 0
    min: int | None = None
    max: int | None = None

    kind = "int"

    def schema(self) -> dict:
        return {**super().schema(), "min": self.min, "max": self.max}


@dataclass
class Float(Param):
    default: float = 0.0
    min: float | None = None
    max: float | None = None

    kind = "float"

    def schema(self) -> dict:
        return {**super().schema(), "min": self.min, "max": self.max}


@dataclass
class Str(Param):
    default: str = ""

    kind = "string"


@dataclass
class Text(Param):
    """Multiline string; rendered as a textarea (mono font for code-ish params)."""

    default: str = ""

    kind = "text"


@dataclass
class Bool(Param):
    default: bool = False

    kind = "bool"


@dataclass
class Choice(Param):
    options: list[str] = field(default_factory=list)
    default: str = ""

    kind = "choice"

    def __init__(self, options: list[str], default: str | None = None, help: str = "", required: bool = False):
        self.options = list(options)
        self.default = default if default is not None else (self.options[0] if self.options else "")
        self.help = help
        self.required = required

    def schema(self) -> dict:
        return {**super().schema(), "options": self.options}


@dataclass
class FilePath(Param):
    default: str = ""
    kind_of_path: str = "file"
    must_exist: bool = True

    kind = "filepath"

    def __init__(self, kind: str = "file", must_exist: bool = True, default: str = "", help: str = "", required: bool = False):
        self.kind_of_path = kind
        self.must_exist = must_exist
        self.default = default
        self.help = help
        self.required = required

    def schema(self) -> dict:
        return {**super().schema(), "path_kind": self.kind_of_path, "must_exist": self.must_exist}


@dataclass
class Secret(Param):
    default: str = ""

    kind = "secret"


@dataclass
class Json(Param):
    default: Any = None

    kind = "json"
