"""Workflow persistence: one portable .axon.json file per workflow."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from axon.engine.graph import Workflow

FORMAT = "axon-workflow/1"


class WorkflowStore:
    def __init__(self, dir: Path):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, wf_id: str) -> Path:
        return self.dir / f"{wf_id}.axon.json"

    def list(self) -> list[dict]:
        out = []
        for p in sorted(self.dir.glob("*.axon.json")):
            try:
                data = json.loads(p.read_text())
                out.append(
                    {
                        "id": data.get("id", p.stem),
                        "name": data.get("name", "Untitled"),
                        "updated_at": p.stat().st_mtime,
                        "node_count": len(data.get("nodes", [])),
                    }
                )
            except Exception:
                continue
        return sorted(out, key=lambda w: w["updated_at"], reverse=True)

    def get(self, wf_id: str) -> Workflow:
        path = self._path(wf_id)
        if not path.exists():
            raise KeyError(f"No workflow with id {wf_id}")
        return Workflow.model_validate_json(path.read_text())

    def save(self, wf: Workflow) -> Workflow:
        if not wf.id:
            wf.id = uuid.uuid4().hex[:12]
        wf.meta["updated_at"] = time.time()
        wf.meta.pop("base_dir", None)  # never persist machine-local paths
        self._path(wf.id).write_text(wf.model_dump_json(indent=2))
        return wf

    def delete(self, wf_id: str) -> None:
        self._path(wf_id).unlink(missing_ok=True)

    def import_file(self, content: bytes | str | Path) -> Workflow:
        if isinstance(content, Path):
            content = content.read_text()
        if isinstance(content, bytes):
            content = content.decode()
        data = json.loads(content)
        if data.get("format") != FORMAT:
            raise ValueError(
                f"Not an Axon workflow (expected format '{FORMAT}', got '{data.get('format')}')"
            )
        wf = Workflow.model_validate(data)
        wf.id = uuid.uuid4().hex[:12]
        return self.save(wf)

    def export(self, wf_id: str) -> str:
        wf = self.get(wf_id)
        wf.meta.pop("base_dir", None)
        return wf.model_dump_json(indent=2)
