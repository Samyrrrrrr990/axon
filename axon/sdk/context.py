"""Execution context handed to every node function as its first argument."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable


class NodeContext:
    def __init__(
        self,
        workspace: Path | None,
        settings: dict,
        log_cb: Callable[[str], None] | None = None,
        progress_cb: Callable[[float, dict | None], None] | None = None,
        cancel_event: threading.Event | None = None,
    ):
        self.workspace = workspace
        self.settings = settings
        self._log_cb = log_cb or (lambda m: None)
        self._progress_cb = progress_cb or (lambda f, m: None)
        self._cancel_event = cancel_event or threading.Event()

    def log(self, message: str) -> None:
        self._log_cb(str(message))

    def progress(self, fraction: float, metrics: dict | None = None) -> None:
        """Report progress in [0,1]; metrics (e.g. {'epoch': 3, 'loss': 0.42}) stream to live charts."""
        self._progress_cb(float(fraction), metrics)

    @property
    def cancelled(self) -> bool:
        return self._cancel_event.is_set()
