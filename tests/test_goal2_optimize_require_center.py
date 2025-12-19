from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_optimize_forward_line_require_center_enforced():
    resp = client.post(
        "/optimize/forward-line",
        json={
            "constraints": {"min_ovr": 0, "require_center": True},
            "optimization_target": "ovr",
            "num_solutions": 1,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    if data["solutions"]:
        players = data["solutions"][0]["players"]
        assert any(str(p.get("position", "")).upper() == "C" for p in players)

