"""Lazy dependency packs — heavy ML libraries install on demand, not at first launch."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from typing import Callable

from axon.engine.events import RunEvent

PACKS: dict[str, dict] = {
    "ml-boost": {
        "modules": ["xgboost"],
        "label": "Boosted Trees (XGBoost)",
        "size_hint": "~200 MB",
    },
    "deep": {
        "modules": ["torch"],
        "label": "Deep Learning (PyTorch)",
        "size_hint": "~2 GB",
    },
    "finetune": {
        "modules": ["transformers", "peft", "datasets"],
        "label": "Fine-tuning (Transformers + PEFT)",
        "size_hint": "~2.5 GB",
    },
    "rag": {
        "modules": ["chromadb", "sentence_transformers"],
        "label": "RAG & Embeddings (Chroma + Sentence-Transformers)",
        "size_hint": "~500 MB",
    },
}


def pack_status() -> dict[str, dict]:
    out = {}
    for name, info in PACKS.items():
        installed = all(importlib.util.find_spec(m) is not None for m in info["modules"])
        out[name] = {"installed": installed, "label": info["label"], "size_hint": info["size_hint"]}
    return out


def install_pack(name: str, emit: Callable[[RunEvent], None]) -> bool:
    if name not in PACKS:
        raise KeyError(f"Unknown pack '{name}'")

    def _stream(cmd: list[str]) -> int:
        emit(RunEvent("pack_install_progress", "packs", None,
                      {"pack": name, "line": "$ " + " ".join(cmd)}))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            emit(RunEvent("pack_install_progress", "packs", None,
                          {"pack": name, "line": line.rstrip()}))
        return proc.wait()

    code = _stream(["uv", "pip", "install", "--python", sys.executable, f"axon[{name}] @ ."])
    if code != 0:
        code = _stream([sys.executable, "-m", "pip", "install", f".[{name}]"])
    done = code == 0 and pack_status()[name]["installed"]
    emit(RunEvent("pack_install_progress", "packs", None,
                  {"pack": name, "done": True, "success": done}))
    return done
