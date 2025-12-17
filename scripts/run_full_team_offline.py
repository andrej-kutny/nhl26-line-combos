"""
Offline full-team optimization runner.

Rationale:
- The full-team search space can be large enough that interactive API calls may
  time out (client-side) or block the server process for too long.
- This script runs the same solver locally with an explicit time limit and
  explicit candidate-pool caps, and writes results to a JSON file for inspection.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _bootstrap_import_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def main() -> int:
    _bootstrap_import_path()

    from src.asp.solver import ASPSolver
    from src.core.models import OptimizationConstraints, OptimizationTarget

    parser = argparse.ArgumentParser(description="Run full-team optimization offline (no API).")
    parser.add_argument("--min-ovr", type=int, default=80)
    parser.add_argument("--max-salary", type=int, default=110)
    parser.add_argument("--max-ap", type=int, default=None)
    parser.add_argument("--target", choices=["ovr", "salary", "ap", "balanced"], default="ovr")
    parser.add_argument("--num-solutions", type=int, default=1)
    parser.add_argument("--time-limit-seconds", type=int, default=7200)
    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        help="Clingo parallel threads (uses --parallel-mode N). Use >1 to utilize multiple CPU cores.",
    )
    parser.add_argument("--max-fwd", type=int, default=24)
    parser.add_argument("--max-def", type=int, default=14)
    parser.add_argument("--max-g", type=int, default=4)
    parser.add_argument("--min-fwd1", type=int, default=None, help="Override OVR floor for FWD line 1 (slots 1..3).")
    parser.add_argument("--min-fwd2", type=int, default=None, help="Override OVR floor for FWD line 2 (slots 4..6).")
    parser.add_argument("--min-def12", type=int, default=None, help="Override OVR floor for DEF pairs 1–2 (slots 13..16).")
    parser.add_argument("--min-g1", type=int, default=None, help="Override OVR floor for goalie slot 19 (G1).")
    parser.add_argument(
        "--json-out",
        type=str,
        default="out/full_team_solution.json",
        help="Output path for JSON (will create parent directory if needed).",
    )
    args = parser.parse_args()

    solver = ASPSolver(
        clingo_threads=args.threads,
        max_fullteam_forwards=args.max_fwd,
        max_fullteam_defense=args.max_def,
        max_fullteam_goalies=args.max_g,
    )

    constraints = OptimizationConstraints(
        min_ovr=args.min_ovr,
        max_salary=args.max_salary,
        max_ap=args.max_ap,
        require_center=False,
    )
    target = OptimizationTarget(args.target)

    started = datetime.now(timezone.utc).isoformat()
    solutions = solver.optimize_full_team(
        constraints=constraints,
        target=target,
        num_solutions=args.num_solutions,
        time_limit_seconds=args.time_limit_seconds,
        min_fwd_line1=args.min_fwd1,
        min_fwd_line2=args.min_fwd2,
        min_def_top4=args.min_def12,
        min_g1=args.min_g1,
    )
    finished = datetime.now(timezone.utc).isoformat()

    out_path = Path(args.json_out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "started_utc": started,
        "finished_utc": finished,
        "constraints": constraints.model_dump(),
        "target": target.value,
        "candidate_caps": {"max_fwd": args.max_fwd, "max_def": args.max_def, "max_g": args.max_g},
        "solutions": [s.model_dump() for s in solutions],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {len(solutions)} solution(s) to {out_path}")
    if solutions:
        best = solutions[0]
        print(
            f"Top solution: base_ovr={best.total_base_ovr} ovr_bonus={best.ovr_bonus} "
            f"salary={best.total_salary} ap={best.total_ap} active_combos={len(best.active_combos)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
