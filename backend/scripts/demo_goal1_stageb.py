"""
Demo runner: Goal 1 Stage B (enumeration / grounding).

Produces stable JSON artifacts under `out/` (gitignored) that can be used by a
backend/frontend demo without needing to run ASP live in the request path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _parse_ids(value: str) -> list[int]:
    raw = [p.strip() for p in value.split(",") if p.strip()]
    if not raw:
        return []
    out: list[int] = []
    for p in raw:
        out.append(int(p))
    return out


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from scripts.goal1_stageb_enumerate import build_stageb_payload
    from src.asp.solver import ASPSolver
    from src.core.models import OptimizationConstraints

    parser = argparse.ArgumentParser(description="Generate Goal 1 Stage B demo artifacts (JSON).")
    parser.add_argument("--data-dir", type=str, default="data/", help="Dataset directory (default: data/).")
    parser.add_argument(
        "--out-dir",
        type=str,
        default="out/",
        help="Output directory for demo artifacts (default: out/).",
    )
    parser.add_argument(
        "--fwd-combo-ids",
        type=_parse_ids,
        default=[22],
        help="Comma-separated forward combo ids (default: 22).",
    )
    parser.add_argument(
        "--def-combo-ids",
        type=_parse_ids,
        default=[31],
        help="Comma-separated defense combo ids (default: 31).",
    )
    parser.add_argument("--min-ovr", type=int, default=0)
    parser.add_argument("--max-salary", type=int, default=None)
    parser.add_argument("--max-ap", type=int, default=None)
    parser.add_argument("--require-center", action="store_true", default=False)
    parser.add_argument("--max-models", type=int, default=50)
    parser.add_argument("--time-limit-seconds", type=int, default=None)
    parser.add_argument("--max-candidates", type=int, default=None)
    args = parser.parse_args()

    constraints = OptimizationConstraints(
        min_ovr=args.min_ovr,
        max_salary=args.max_salary,
        max_ap=args.max_ap,
        require_center=args.require_center,
    )

    solver = ASPSolver(data_dir=args.data_dir)

    out_dir = Path(args.out_dir).expanduser().resolve()
    fwd_out = out_dir / "demo_goal1_stageb_fwd.json"
    def_out = out_dir / "demo_goal1_stageb_def.json"

    fwd_solutions = solver.enumerate_forward_lines_for_required_combos(
        required_combo_ids=args.fwd_combo_ids,
        constraints=constraints,
        max_models=args.max_models,
        time_limit_seconds=args.time_limit_seconds,
        max_candidates=args.max_candidates,
    )
    def_solutions = solver.enumerate_defense_pairs_for_required_combos(
        required_combo_ids=args.def_combo_ids,
        constraints=constraints,
        max_models=args.max_models,
        time_limit_seconds=args.time_limit_seconds,
        max_candidates=args.max_candidates,
    )

    _write_json(
        fwd_out,
        build_stageb_payload(
            pos="fwd",
            combo_ids=list(args.fwd_combo_ids),
            constraints=constraints.model_dump(),
            solutions=[s.model_dump() for s in fwd_solutions],
        ),
    )
    _write_json(
        def_out,
        build_stageb_payload(
            pos="def",
            combo_ids=list(args.def_combo_ids),
            constraints=constraints.model_dump(),
            solutions=[s.model_dump() for s in def_solutions],
        ),
    )

    print(f"Wrote: {fwd_out}")
    print(f"Wrote: {def_out}")
    print(f"Counts: fwd={len(fwd_solutions)} def={len(def_solutions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
