"""SQLite run history, populated by subscribing to the RunManager's event stream."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from axon.engine.events import RunEvent

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT,
    workflow_name TEXT,
    status TEXT,
    started_at REAL,
    finished_at REAL
);
CREATE TABLE IF NOT EXISTS run_nodes (
    run_id TEXT,
    node_id TEXT,
    status TEXT,
    started_at REAL,
    duration_ms INTEGER,
    error TEXT,
    PRIMARY KEY (run_id, node_id)
);
"""


class RunHistory:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def record_event(self, e: RunEvent) -> None:
        with self._lock, self._conn() as conn:
            if e.type == "run_started":
                conn.execute(
                    "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, 'running', ?, NULL)",
                    (e.run_id, e.data.get("workflow_id"), e.data.get("name"), e.ts),
                )
            elif e.type == "node_started":
                conn.execute(
                    "INSERT OR REPLACE INTO run_nodes VALUES (?, ?, 'running', ?, NULL, NULL)",
                    (e.run_id, e.node_id, e.ts),
                )
            elif e.type == "node_finished":
                row = conn.execute(
                    "SELECT started_at FROM run_nodes WHERE run_id=? AND node_id=?",
                    (e.run_id, e.node_id),
                ).fetchone()
                started = row["started_at"] if row and row["started_at"] else e.ts
                conn.execute(
                    "INSERT OR REPLACE INTO run_nodes VALUES (?, ?, 'finished', ?, ?, NULL)",
                    (e.run_id, e.node_id, started, int((e.ts - started) * 1000)),
                )
            elif e.type == "node_failed":
                status = "skipped" if e.data.get("skipped") else "failed"
                conn.execute(
                    "INSERT OR REPLACE INTO run_nodes VALUES (?, ?, ?, NULL, NULL, ?)",
                    (e.run_id, e.node_id, status, e.data.get("error")),
                )
            elif e.type in ("run_finished", "run_cancelled", "run_failed"):
                status = {
                    "run_finished": e.data.get("status", "finished"),
                    "run_cancelled": "cancelled",
                    "run_failed": "error",
                }[e.type]
                conn.execute(
                    "UPDATE runs SET status=?, finished_at=? WHERE id=?",
                    (status, e.ts, e.run_id),
                )

    def list_runs(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_run(self, run_id: str) -> dict | None:
        with self._conn() as conn:
            run = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if run is None:
                return None
            nodes = conn.execute(
                "SELECT * FROM run_nodes WHERE run_id=?", (run_id,)
            ).fetchall()
            return {**dict(run), "nodes": [dict(n) for n in nodes]}
