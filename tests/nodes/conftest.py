import threading

import pytest

from axon.sdk.context import NodeContext


@pytest.fixture()
def ctx(tmp_path):
    return NodeContext(
        workspace=tmp_path,
        settings={},
        log_cb=lambda m: None,
        progress_cb=lambda f, m: None,
        cancel_event=threading.Event(),
    )


@pytest.fixture()
def recording_ctx(tmp_path):
    events = []
    context = NodeContext(
        workspace=tmp_path,
        settings={},
        log_cb=lambda m: events.append(("log", m)),
        progress_cb=lambda f, m: events.append(("progress", f, m)),
        cancel_event=threading.Event(),
    )
    context.events = events
    return context
