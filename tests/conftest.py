import sys
from pathlib import Path

# Make the repo root importable regardless of editable-install state.
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
