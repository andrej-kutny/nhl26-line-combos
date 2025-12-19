from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_optimize_forward_line_smoke():
    resp = client.post(
        "/optimize/forward-line",
        json={"constraints": {"min_ovr": 0}, "optimization_target": "ovr", "num_solutions": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "solutions" in data

    if data["solutions"]:
        sol = data["solutions"][0]
        assert sol["players"], "expected at least one player in solution"
        player = sol["players"][0]
        for key in ["id", "player_id", "img", "weight", "height", "salary", "overall", "team", "position"]:
            assert key in player


def test_optimize_defense_pair_smoke():
    resp = client.post(
        "/optimize/defense-pair",
        json={"constraints": {"min_ovr": 0}, "optimization_target": "ovr", "num_solutions": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "solutions" in data

    if data["solutions"]:
        sol = data["solutions"][0]
        assert sol["players"], "expected at least one player in solution"
        player = sol["players"][0]
        for key in ["id", "player_id", "img", "weight", "height", "salary", "overall", "team", "position"]:
            assert key in player

