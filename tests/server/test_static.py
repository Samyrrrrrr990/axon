from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from axon.server.app import create_app
from axon.storage.workspace import Workspace

DIST = Path(__file__).resolve().parents[2] / "web" / "dist"


@pytest.mark.skipif(not DIST.is_dir(), reason="web/dist not built")
def test_serves_spa_index(tmp_path):
    app = create_app(workspace=Workspace(root=tmp_path / "ws"))
    with TestClient(app) as client:
        r = client.get("/")
        assert r.status_code == 200
        assert "Axon" in r.text
        # SPA fallback: unknown paths also return the app shell
        r2 = client.get("/some/client/route")
        assert r2.status_code == 200
        assert "Axon" in r2.text
