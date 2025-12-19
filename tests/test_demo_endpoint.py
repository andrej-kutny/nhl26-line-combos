from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


@pytest.fixture
def demo_out_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "out"


def _backup_if_exists(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_suffix(path.suffix + ".bak_test")
    path.replace(backup)
    return backup


def _restore_backup(backup: Path | None, target: Path) -> None:
    if backup is None:
        return
    if target.exists():
        target.unlink()
    backup.replace(target)


def test_demo_goal1_stageb_returns_json_when_artifact_exists(demo_out_dir: Path):
    demo_out_dir.mkdir(parents=True, exist_ok=True)
    artifact = demo_out_dir / "demo_goal1_stageb_fwd.json"
    backup = _backup_if_exists(artifact)

    try:
        payload = {"schema_version": 1, "pos": "fwd", "combo_ids": [22], "count": 0, "solutions": []}
        artifact.write_text(json.dumps(payload), encoding="utf-8")

        response = client.get("/demo/goal1-stageb?pos=fwd")
        assert response.status_code == 200
        assert response.json()["schema_version"] == 1
        assert response.json()["pos"] == "fwd"
    finally:
        if artifact.exists():
            artifact.unlink()
        _restore_backup(backup, artifact)


def test_demo_goal1_stageb_404_when_missing(demo_out_dir: Path):
    demo_out_dir.mkdir(parents=True, exist_ok=True)
    artifact = demo_out_dir / "demo_goal1_stageb_def.json"
    backup = _backup_if_exists(artifact)

    try:
        if artifact.exists():
            artifact.unlink()
        response = client.get("/demo/goal1-stageb?pos=def")
        assert response.status_code == 404
    finally:
        _restore_backup(backup, artifact)

