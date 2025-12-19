from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.data import get_data_loader


client = TestClient(app)


def test_optimize_validate_forward_returns_active_combos_and_totals():
    loader = get_data_loader()
    forwards = loader.get_forwards()
    assert len(forwards) >= 3
    ids = [int(forwards[0].id), int(forwards[1].id), int(forwards[2].id)]

    resp = client.post("/optimize/validate?position_type=forward", json=ids)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["total_base_ovr"] >= 0
    assert "active_combos" in data


def test_optimize_validate_defense_returns_active_combos_and_totals():
    loader = get_data_loader()
    defense = loader.get_defense()
    assert len(defense) >= 2
    ids = [int(defense[0].id), int(defense[1].id)]

    resp = client.post("/optimize/validate?position_type=defense", json=ids)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["total_base_ovr"] >= 0
    assert "active_combos" in data

