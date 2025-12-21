"""
Goal 1 — Stage B enumeration helper.

This script "grounds" a chosen set of combo IDs against the concrete player
dataset and enumerates line realizations that satisfy ALL required combos.

Typical use-case:
1) Pick a small set of high-value combos (Stage A / abstraction).
2) Enumerate concrete lines/pairs that can realize them in the current dataset.

We do not commit the scraped player snapshot itself; instead, we version the
scripts/schema and let everyone regenerate `data/nhlhutbuilder_players_api_dedup.csv`
locally for reproducibility.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STAGEB_OUTPUT_SCHEMA_VERSION = 1


def _bootstrap_import_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _parse_combo_ids(value: str) -> list[int]:
    raw = [p.strip() for p in value.split(",") if p.strip()]
    if not raw:
        return []
    ids: list[int] = []
    for p in raw:
        try:
            ids.append(int(p))
        except ValueError as e:
            raise argparse.ArgumentTypeError(f"Invalid combo id: {p!r}") from e
    return ids


def build_stageb_payload(
    *,
    pos: str,
    combo_ids: list[int],
    constraints: dict,
    solutions: list[dict],
) -> dict:
    return {
        "schema_version": STAGEB_OUTPUT_SCHEMA_VERSION,
        "pos": pos,
        "combo_ids": combo_ids,
        "constraints": constraints,
        "count": len(solutions),
        "solutions": solutions,
    }


def main() -> int:
    _bootstrap_import_path()

    from src.asp.solver import ASPSolver
    from src.core.models import OptimizationConstraints

    parser = argparse.ArgumentParser(
        description="Enumerate concrete lines/pairs for a required set of combo IDs (Goal 1 — Stage B)."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/",
        help="Path to the dataset directory to load (default: data/).",
    )
    parser.add_argument(
        "--pos",
        required=True,
        choices=["fwd", "def"],
        help="Which combo family to use: fwd (3-player forward line) or def (2-player defense pair).",
    )
    parser.add_argument(
        "--combo-ids",
        required=True,
        type=_parse_combo_ids,
        help="Comma-separated combo IDs, e.g. --combo-ids 28,18",
    )
    parser.add_argument("--min-ovr", type=int, default=0)
    parser.add_argument("--max-salary", type=int, default=None)
    parser.add_argument("--max-ap", type=int, default=None)
    parser.add_argument("--require-center", action="store_true", default=False)
    parser.add_argument(
        "--max-models",
        type=int,
        default=50,
        help="How many models to enumerate. Use 0 to enumerate all (can be very large).",
    )
    parser.add_argument(
        "--time-limit-seconds",
        type=int,
        default=None,
        help="Optional time limit for enumeration (solving only; grounding is still upfront).",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Optional cap on candidate cards used for grounding (per position).",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Optional path to write full results as JSON.",
    )
    args = parser.parse_args()

    solver = ASPSolver(data_dir=args.data_dir)
    constraints = OptimizationConstraints(
        min_ovr=args.min_ovr,
        max_salary=args.max_salary,
        max_ap=args.max_ap,
        require_center=args.require_center,
    )

    if args.pos == "fwd":
        results = solver.enumerate_forward_lines_for_required_combos(
            required_combo_ids=args.combo_ids,
            constraints=constraints,
            max_models=args.max_models,
            time_limit_seconds=args.time_limit_seconds,
            max_candidates=args.max_candidates,
        )
    else:
        results = solver.enumerate_defense_pairs_for_required_combos(
            required_combo_ids=args.combo_ids,
            constraints=constraints,
            max_models=args.max_models,
            time_limit_seconds=args.time_limit_seconds,
            max_candidates=args.max_candidates,
        )

    print(f"Enumerated {len(results)} model(s) for {args.pos} combo_ids={args.combo_ids}")
    for sol in results[: min(10, len(results))]:
        names = ", ".join([p.full_name for p in sol.players])
        sal_bonus = sum(c.reward_amount for c in sol.active_combos if c.reward_type.value == "SAL")
        ap_bonus = sum(c.reward_amount for c in sol.active_combos if c.reward_type.value == "AP")
        base_salary = sol.total_salary + sal_bonus
        base_ap = sol.total_ap + ap_bonus
        print(
            f"- #{sol.rank}: base_ovr={sol.total_base_ovr} ovr_bonus={sol.ovr_bonus} "
            f"salary_eff={sol.total_salary} (base={base_salary}, bonus={sal_bonus}) "
            f"ap_eff={sol.total_ap} (base={base_ap}, bonus={ap_bonus}) "
            f"players=[{names}] active_combos={len(sol.active_combos)}"
        )

    if results:
        best_salary = min(results, key=lambda s: (s.total_salary, -s.total_base_ovr))
        best_ovr = max(results, key=lambda s: (s.total_base_ovr + s.ovr_bonus, -s.total_salary))
        best_ap = min(results, key=lambda s: (s.total_ap, -s.total_base_ovr))

        def _fmt(sol) -> str:
            names = ", ".join([p.full_name for p in sol.players])
            sal_bonus = sum(c.reward_amount for c in sol.active_combos if c.reward_type.value == "SAL")
            ap_bonus = sum(c.reward_amount for c in sol.active_combos if c.reward_type.value == "AP")
            base_salary = sol.total_salary + sal_bonus
            base_ap = sol.total_ap + ap_bonus
            return (
                f"base_ovr={sol.total_base_ovr} ovr_bonus={sol.ovr_bonus} "
                f"salary_eff={sol.total_salary} (base={base_salary}, bonus={sal_bonus}) "
                f"ap_eff={sol.total_ap} (base={base_ap}, bonus={ap_bonus}) "
                f"active_combos={len(sol.active_combos)} players=[{names}]"
            )

        print("")
        print("Best (effective salary / cap gain):", _fmt(best_salary))
        print("Best (effective AP / AP gain):", _fmt(best_ap))
        print("Best (effective OVR):", _fmt(best_ovr))

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        payload = build_stageb_payload(
            pos=args.pos,
            combo_ids=args.combo_ids,
            constraints=constraints.model_dump(),
            solutions=[r.model_dump() for r in results],
        )
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote JSON to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
