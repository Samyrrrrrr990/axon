"""Content-addressed node output cache. Re-running a tweaked workflow recomputes only what changed."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path


class Cache:
    def __init__(self, dir: Path):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._warned = False

    def key(self, node_type: str, params: dict, input_keys: list[str], pack_version: str) -> str:
        payload = json.dumps(
            {"type": node_type, "params": params, "inputs": input_keys, "v": pack_version},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.pkl"

    def get(self, key: str) -> dict | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            with path.open("rb") as f:
                return pickle.load(f)
        except Exception:
            path.unlink(missing_ok=True)
            return None

    def put(self, key: str, outputs: dict) -> None:
        path = self._path(key)
        try:
            with path.open("wb") as f:
                pickle.dump(outputs, f)
        except Exception:
            # Some outputs (open model handles, lambdas) don't pickle — skip caching those.
            path.unlink(missing_ok=True)

    def clear(self) -> None:
        for p in self.dir.glob("*.pkl"):
            p.unlink(missing_ok=True)
