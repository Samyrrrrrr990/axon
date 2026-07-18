"""Built-in node packs. Importing this module registers every available node.

Modules whose heavy dependencies aren't installed are skipped gracefully;
their nodes simply don't appear until the pack is installed from Settings.
"""

import importlib

UNAVAILABLE: dict[str, str] = {}

for _mod in ["data", "ml", "util", "deep", "finetune", "llm"]:
    try:
        importlib.import_module(f"axon.nodes.{_mod}")
    except ImportError as exc:  # pragma: no cover - depends on installed packs
        UNAVAILABLE[_mod] = str(exc)
