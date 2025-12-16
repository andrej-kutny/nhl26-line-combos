"""
Bench-first full-team runner (offline).

Intent
------
This script operationalizes the "bench-first" idea:
1) Pick a small set of high-value combos (e.g., SAL/AP extenders).
2) Ground them into concrete bench lines/pairs using Goal 1 Stage B enumeration.
3) Freeze those bench selections into the full-team ASP program and let Clingo
   maximize OVR for the remaining slots under the effective caps.

Why offline
-----------
Full-team solving can be slow and should not be invoked via the interactive API.
This script gives explicit control over:
- time limit,
- candidate pool caps,
- clingo parallelism,
- and writes a JSON artifact for inspection.

Notes on "salary" / "ap" values
-------------------------------
Our `LineSolution.total_salary` and `LineSolution.total_ap` are *effective* values:
  effective_salary = total_salary - salary_bonus
  effective_ap     = total_ap - ap_bonus

So negative numbers are possible and simply mean "the bonuses exceed the base cost".
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _bootstrap_import_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _parse_ids(value: str) -> list[int]:
    raw = [p.strip() for p in value.split(",") if p.strip()]
    return [int(p) for p in raw]


@dataclass(frozen=True)
class FixedPick:
    slot: int
    card_id: str
    label: str


def _best_by_effective_salary(lines) -> object:
    # Minimize effective salary first (more cap gain), then maximize OVR.
    return min(lines, key=lambda s: (s.total_salary, -s.total_base_ovr))


def _fixed_facts(picks: Iterable[FixedPick]) -> str:
    return "\n".join([f'select("{p.card_id}", {int(p.slot)}). % {p.label}' for p in picks])


def main() -> int:
    _bootstrap_import_path()

    from src.asp.solver import ASPSolver
    from src.core.models import OptimizationConstraints, OptimizationTarget

    parser = argparse.ArgumentParser(description="Offline full-team run with bench-first frozen combo lines.")
    parser.add_argument("--min-ovr", type=int, default=80)
    parser.add_argument("--max-salary", type=int, default=110)
    parser.add_argument("--max-ap", type=int, default=None)
    parser.add_argument("--target", choices=["ovr", "salary", "ap", "balanced"], default="ovr")

    parser.add_argument("--bench-fwd-combo", type=int, default=28, help="Forward bench combo_id to force on FWD line 3")
    parser.add_argument("--bench-def-sal-combo", type=int, default=37, help="Defense bench SAL combo_id to force on DEF pair 3")
    parser.add_argument(
        "--bench-def-ap-combo",
        type=int,
        default=None,
        help="Optional second defense bench combo_id (e.g., CHI+CHI AP extender).",
    )
    parser.add_argument("--bench-max-models", type=int, default=200)

    parser.add_argument("--num-solutions", type=int, default=1)
    parser.add_argument("--time-limit-seconds", type=int, default=7200)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--max-fwd", type=int, default=24)
    parser.add_argument("--max-def", type=int, default=14)
    parser.add_argument("--max-g", type=int, default=4)
    parser.add_argument("--json-out", type=str, default="out/full_team_bench_first.json")
    args = parser.parse_args()

    solver = ASPSolver(
        clingo_threads=args.threads,
        max_fullteam_forwards=args.max_fwd,
        max_fullteam_defense=args.max_def,
        max_fullteam_goalies=args.max_g,
    )

    base_constraints = OptimizationConstraints(
        min_ovr=args.min_ovr,
        max_salary=args.max_salary,
        max_ap=args.max_ap,
        require_center=False,
    )

    # ------------------------------------------------------------------
    # 1) Ground bench combos into concrete line/pair candidates
    # ------------------------------------------------------------------
    fwd_candidates = solver.enumerate_forward_lines_for_required_combos(
        required_combo_ids=[args.bench_fwd_combo],
        constraints=base_constraints,
        max_models=args.bench_max_models,
    )
    if not fwd_candidates:
        raise SystemExit(f"No forward lines found for combo_id={args.bench_fwd_combo}")
    bench_fwd = _best_by_effective_salary(fwd_candidates)

    def_candidates = solver.enumerate_defense_pairs_for_required_combos(
        required_combo_ids=[args.bench_def_sal_combo],
        constraints=base_constraints,
        max_models=args.bench_max_models,
    )
    if not def_candidates:
        raise SystemExit(f"No defense pairs found for combo_id={args.bench_def_sal_combo}")
    bench_def_sal = _best_by_effective_salary(def_candidates)

    bench_def_ap = None
    if args.bench_def_ap_combo is not None:
        ap_candidates = solver.enumerate_defense_pairs_for_required_combos(
            required_combo_ids=[args.bench_def_ap_combo],
            constraints=base_constraints,
            max_models=args.bench_max_models,
        )
        if ap_candidates:
            bench_def_ap = _best_by_effective_salary(ap_candidates)

    # ------------------------------------------------------------------
    # 2) Freeze bench selections into full-team program
    # ------------------------------------------------------------------
    # Convention: "bench" forward line is line 3 (slots 7..9), "bench" defense pair is pair 3 (slots 17..18).
    fixed: list[FixedPick] = []

    for slot, player in zip((7, 8, 9), bench_fwd.players, strict=True):
        fixed.append(FixedPick(slot=slot, card_id=str(player.id), label=f"bench_fwd combo={args.bench_fwd_combo}"))

    for slot, player in zip((17, 18), bench_def_sal.players, strict=True):
        fixed.append(FixedPick(slot=slot, card_id=str(player.id), label=f"bench_def_sal combo={args.bench_def_sal_combo}"))

    # Optional second defense bench pair: we place it on pair 2 (slots 15..16) because pair 3 is already used.
    # If your current `full_team.lp` enforces a hard OVR floor on slots 15..16, this may fail (by design).
    if bench_def_ap is not None:
        for slot, player in zip((15, 16), bench_def_ap.players, strict=True):
            fixed.append(FixedPick(slot=slot, card_id=str(player.id), label=f"bench_def_ap combo={args.bench_def_ap_combo}"))

    fixed_facts = _fixed_facts(fixed)

    # Recreate the full-team candidate pools similarly to `ASPSolver.optimize_full_team`,
    # but remove any already-fixed card IDs to shrink the search space.
    forwards = solver.loader.get_forwards()
    defense = solver.loader.get_defense()
    goalies = solver.loader.get_goalies()

    fixed_ids = {p.card_id for p in fixed}
    forwards = [p for p in forwards if str(p.id) not in fixed_ids]
    defense = [p for p in defense if str(p.id) not in fixed_ids]
    goalies = [p for p in goalies if str(p.id) not in fixed_ids]

    fwd_combos = solver.loader.get_forward_combos()
    def_combos = solver.loader.get_defense_combos()

    forwards = solver.loader.filter_players(
        forwards,
        min_ovr=base_constraints.min_ovr,
        team=base_constraints.required_team,
        nationality=base_constraints.required_nationality,
        event=base_constraints.required_event,
        excluded_ids=base_constraints.excluded_player_ids,
    )
    defense = solver.loader.filter_players(
        defense,
        min_ovr=base_constraints.min_ovr,
        team=base_constraints.required_team,
        nationality=base_constraints.required_nationality,
        event=base_constraints.required_event,
        excluded_ids=base_constraints.excluded_player_ids,
    )

    forwards = solver._dedupe_best_card_per_player(forwards)
    defense = solver._dedupe_best_card_per_player(defense)
    goalies = solver._dedupe_best_card_per_player(goalies)

    target = OptimizationTarget(args.target)
    forwards = solver._select_candidates(forwards, fwd_combos, target=target)
    defense = solver._select_candidates(defense, def_combos, target=target)
    goalies = goalies[:10]

    sort_key = solver._candidate_sort_key(target)
    forwards.sort(key=sort_key)
    defense.sort(key=sort_key)
    goalies.sort(key=sort_key)

    forwards = forwards[: args.max_fwd]
    defense = defense[: args.max_def]
    goalies = goalies[: args.max_g]

    program = "\n".join(
        [
            solver._generate_full_team_facts(
                forwards=forwards,
                defense=defense,
                goalies=goalies,
                fwd_combos=fwd_combos,
                def_combos=def_combos,
                constraints=base_constraints,
                target=target,
            ),
            fixed_facts,
            solver._read_rules("base.lp"),
            solver._read_rules("full_team.lp"),
        ]
    )

    started = datetime.now(timezone.utc).isoformat()
    models = solver._solve(
        program,
        num_solutions=args.num_solutions,
        model_limit=solver._model_limit(target=target, is_full_team=True),
        time_limit_seconds=args.time_limit_seconds,
    )
    finished = datetime.now(timezone.utc).isoformat()

    solutions = [
        solver._parse_full_team_model(
            symbols=m,
            forwards=forwards,
            defense=defense,
            goalies=goalies,
            fwd_combos=fwd_combos,
            def_combos=def_combos,
            rank=i + 1,
        )
        for i, m in enumerate(models)
    ]

    out_path = Path(args.json_out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "started_utc": started,
        "finished_utc": finished,
        "constraints": base_constraints.model_dump(),
        "target": target.value,
        "bench": {
            "bench_fwd_combo": args.bench_fwd_combo,
            "bench_def_sal_combo": args.bench_def_sal_combo,
            "bench_def_ap_combo": args.bench_def_ap_combo,
            "fixed_slots": [p.__dict__ for p in fixed],
            "bench_fwd": bench_fwd.model_dump(),
            "bench_def_sal": bench_def_sal.model_dump(),
            "bench_def_ap": bench_def_ap.model_dump() if bench_def_ap is not None else None,
        },
        "candidate_caps": {"max_fwd": args.max_fwd, "max_def": args.max_def, "max_g": args.max_g},
        "solutions": [s.model_dump() for s in solutions],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {len(solutions)} solution(s) to {out_path}")
    print(
        f"Bench picks: fwd(combo {args.bench_fwd_combo}) salary={bench_fwd.total_salary} base_ovr={bench_fwd.total_base_ovr}; "
        f"def(combo {args.bench_def_sal_combo}) salary={bench_def_sal.total_salary} base_ovr={bench_def_sal.total_base_ovr}"
    )
    if bench_def_ap is not None:
        print(
            f"Bench picks: def_ap(combo {args.bench_def_ap_combo}) ap={bench_def_ap.total_ap} salary={bench_def_ap.total_salary} "
            f"base_ovr={bench_def_ap.total_base_ovr}"
        )
    if solutions:
        best = solutions[0]
        print(
            f"Top full-team: base_ovr={best.total_base_ovr} ovr_bonus={best.ovr_bonus} "
            f"salary={best.total_salary} ap={best.total_ap} active_combos={len(best.active_combos)}"
        )
    else:
        print("No full-team solution found under current caps/candidate caps + fixed bench selections.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

