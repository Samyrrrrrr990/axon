"""Run events: the single stream that feeds the WebSocket, run history, and CLI output."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

# Event types:
#   run_started, node_started, node_log, node_progress, node_finished, node_failed,
#   run_finished, run_failed, run_cancelled, pack_install_progress


@dataclass
class RunEvent:
    type: str
    run_id: str
    node_id: str | None = None
    data: dict = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_json(self) -> dict:
        return {
            "type": self.type,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "data": self.data,
            "ts": self.ts,
        }
