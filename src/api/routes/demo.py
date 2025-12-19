from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException


router = APIRouter()


@router.get("/goal1-stageb", summary="Return Goal 1 Stage B demo JSON artifact")
async def get_goal1_stageb_demo(pos: Literal["fwd", "def"] = "fwd"):
    """
    Serves locally-generated demo artifacts written by `scripts/demo_goal1_stageb.py`.

    This endpoint is intentionally simple for demos: it does not execute the solver.
    """
    repo_root = Path(__file__).resolve().parents[3]
    filename = "demo_goal1_stageb_fwd.json" if pos == "fwd" else "demo_goal1_stageb_def.json"
    path = repo_root / "out" / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Demo artifact not found: {path}. Generate it with "
                "`venv/bin/python scripts/demo_goal1_stageb.py`."
            ),
        )

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in demo artifact: {e}") from e

