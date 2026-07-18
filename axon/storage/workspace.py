"""The Axon workspace at ~/.axon (or $AXON_HOME): settings, cache, workflows, data, run history."""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_SETTINGS = {
    "copilot": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat-v3.1:free",
    },
    "llm_defaults": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat-v3.1:free",
    },
    "keys": {},
}


class Workspace:
    def __init__(self, root: Path | None = None):
        if root is None:
            root = Path(os.environ.get("AXON_HOME", Path.home() / ".axon"))
        self.root = Path(root)
        self.cache_dir = self.root / "cache"
        self.workflows_dir = self.root / "workflows"
        self.data_dir = self.root / "data"
        self.db_path = self.root / "runs.db"
        self._settings_path = self.root / "settings.json"
        for d in (self.root, self.cache_dir, self.workflows_dir, self.data_dir):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def settings(self) -> dict:
        if self._settings_path.exists():
            try:
                loaded = json.loads(self._settings_path.read_text())
            except Exception:
                loaded = {}
        else:
            loaded = {}
        merged = json.loads(json.dumps(DEFAULT_SETTINGS))
        for key, value in loaded.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    def save_settings(self, settings: dict) -> None:
        self._settings_path.write_text(json.dumps(settings, indent=2))
