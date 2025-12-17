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


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


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

def _rank_by_effective_salary(lines) -> list:
    """
    Return candidates sorted by (effective salary asc, base OVR desc).

    This is used to try multiple bench picks: the "best" cap-extender is not
    always compatible with the rest of the roster under the current candidate
    pool and constraints, so we try a small top-k list.
    """

    return sorted(lines, key=lambda s: (s.total_salary, -s.total_base_ovr))


def _fixed_facts(picks: Iterable[FixedPick]) -> str:
    return "\n".join([f'select("{p.card_id}", {int(p.slot)}). % {p.label}' for p in picks])

def _force_include_players(
    *,
    players: list,
    required_card_ids: set[str],
    cap: int,
    sort_key,
) -> list:
    """
    Ensure that a candidate pool contains all `required_card_ids`, even if they
    would normally be truncated away by `cap`.

    This is critical for "bench-first": we emit fixed `select(card_id, slot)`
    facts, and those card_ids must also exist in the `player/ovr/salary/...`
    fact base. If a fixed card_id is missing from the pool, the ASP program
    becomes UNSAT.
    """
    if not required_card_ids:
        return players[:cap]

    by_id = {str(p.id): p for p in players}
    required = [by_id[cid] for cid in required_card_ids if cid in by_id]
    missing = sorted([cid for cid in required_card_ids if cid not in by_id])
    if missing:
        # Caller is expected to pre-merge required IDs from the full universe.
        raise RuntimeError(
            "Fixed card_id(s) missing from candidate pool; caller must include them "
            f"from the full player universe first: {missing}"
        )

    # Remove required players from the pool to avoid duplicates, then take the top-k
    # from the remainder.
    remainder = [p for p in players if str(p.id) not in required_card_ids]
    remainder.sort(key=sort_key)

    # Keep all required, then fill up to cap with best remainder.
    combined = required + remainder
    # Stable and deterministic ordering for ASP facts.
    combined.sort(key=sort_key)

    # Ensure truncation never drops required players.
    if len(combined) <= cap:
        return combined
    keep: list = []
    kept_ids: set[str] = set()
    for p in combined:
        pid = str(p.id)
        if pid in required_card_ids or len(keep) < cap:
            if pid not in kept_ids:
                keep.append(p)
                kept_ids.add(pid)
        if len(keep) >= cap and required_card_ids.issubset(kept_ids):
            break
    return keep


def _dedupe_keep_fixed(players: list, *, fixed_card_ids: set[str]) -> list:
    """
    Keep at most one card per underlying player, but never drop a fixed card.

    Full-team ASP already enforces uniqueness via `card_player/2`, but doing this
    here improves feasibility under tight candidate caps (we need enough unique
    players to fill all slots).
    """
    best_by_player: dict[str, object] = {}
    for p in players:
        card_id = str(p.id)
        player_id = getattr(p, "player_id", None)
        key = str(player_id) if player_id is not None else card_id

        existing = best_by_player.get(key)
        if existing is None:
            best_by_player[key] = p
            continue

        existing_card_id = str(existing.id)
        if existing_card_id in fixed_card_ids:
            # Never replace a fixed card.
            continue
        if card_id in fixed_card_ids:
            best_by_player[key] = p
            continue

        if int(p.overall) > int(existing.overall):
            best_by_player[key] = p

    return list(best_by_player.values())


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
    parser.add_argument(
        "--bench-try-top-fwd",
        type=int,
        default=5,
        help="Try up to N different bench FWD line realizations (ranked by effective salary).",
    )
    parser.add_argument(
        "--bench-try-top-def",
        type=int,
        default=5,
        help="Try up to N different bench DEF pair realizations (ranked by effective salary).",
    )
    parser.add_argument(
        "--bench-try-top-def-ap",
        type=int,
        default=3,
        help="Try up to N different bench DEF AP pair realizations (if enabled).",
    )
    parser.add_argument(
        "--bench-time-limit-seconds",
        type=int,
        default=60,
        help="Time limit for Stage B enumeration (per bench line/pair).",
    )
    parser.add_argument(
        "--bench-max-candidates",
        type=int,
        default=250,
        help="Max candidate cards used for Stage B grounding (per position).",
    )
    parser.add_argument(
        "--no-bench-requirements",
        action="store_true",
        help="Disable the 'bench must activate a combo' requirements and do not freeze bench picks (feasibility/debug).",
    )

    parser.add_argument("--num-solutions", type=int, default=1)
    parser.add_argument("--time-limit-seconds", type=int, default=7200)
    parser.add_argument(
        "--feasibility-time-limit-seconds",
        type=int,
        default=30,
        help="Time limit for a fast feasibility check (find any full-team model).",
    )
    parser.add_argument(
        "--optimize-after-feasible",
        action="store_true",
        help="If set, run the full optimization after a feasible model is found.",
    )
    parser.add_argument(
        "--reduce-combos",
        action="store_true",
        help="Only keep bench combo IDs in the fact base (faster feasibility; ignores other combos).",
    )
    parser.add_argument(
        "--solve-time-limit-seconds",
        type=int,
        default=None,
        help="Optional per-attempt time limit for the full-team solve (defaults to --time-limit-seconds).",
    )
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--max-fwd", type=int, default=24)
    parser.add_argument("--max-def", type=int, default=14)
    parser.add_argument("--max-g", type=int, default=4)
    parser.add_argument(
        "--dedupe-by-player",
        action="store_true",
        help="Dedupe candidate pools to keep one card per player_id (helps feasibility under tight caps).",
    )
    parser.add_argument("--min-fwd1", type=int, default=None, help="Override OVR floor for FWD line 1 (slots 1..3).")
    parser.add_argument("--min-fwd2", type=int, default=None, help="Override OVR floor for FWD line 2 (slots 4..6).")
    parser.add_argument("--min-def12", type=int, default=None, help="Override OVR floor for DEF pairs 1–2 (slots 13..16).")
    parser.add_argument("--min-g1", type=int, default=None, help="Override OVR floor for goalie slot 19 (G1).")
    parser.add_argument("--json-out", type=str, default="out/full_team_bench_first.json")
    args = parser.parse_args()

    _log(
        f"[bench-first] start: target={args.target} min_ovr={args.min_ovr} max_salary={args.max_salary} "
        f"time_limit={args.time_limit_seconds}s threads={args.threads}"
    )
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

    if args.no_bench_requirements:
        _log("[bench-first] mode: no-bench-requirements (feasibility/debug)")

    # ------------------------------------------------------------------
    # 1) Ground bench combos into concrete line/pair candidates
    # ------------------------------------------------------------------
    bench_fwd_ranked: list | None = None
    bench_def_sal_ranked: list | None = None
    if not args.no_bench_requirements:
        _log(
            f"[bench-first] enumerate bench FWD combo={args.bench_fwd_combo} "
            f"(max_models={args.bench_max_models}, max_candidates={args.bench_max_candidates})"
        )
        fwd_candidates = solver.enumerate_forward_lines_for_required_combos(
            required_combo_ids=[args.bench_fwd_combo],
            constraints=base_constraints,
            max_models=args.bench_max_models,
            time_limit_seconds=args.bench_time_limit_seconds,
            max_candidates=args.bench_max_candidates,
        )
        if not fwd_candidates:
            raise SystemExit(f"No forward lines found for combo_id={args.bench_fwd_combo}")
        bench_fwd_ranked = _rank_by_effective_salary(fwd_candidates)[: max(1, int(args.bench_try_top_fwd))]

        _log(
            f"[bench-first] enumerate bench DEF SAL combo={args.bench_def_sal_combo} "
            f"(max_models={args.bench_max_models}, max_candidates={args.bench_max_candidates})"
        )
        def_candidates = solver.enumerate_defense_pairs_for_required_combos(
            required_combo_ids=[args.bench_def_sal_combo],
            constraints=base_constraints,
            max_models=args.bench_max_models,
            time_limit_seconds=args.bench_time_limit_seconds,
            max_candidates=args.bench_max_candidates,
        )
        if not def_candidates:
            raise SystemExit(f"No defense pairs found for combo_id={args.bench_def_sal_combo}")
        bench_def_sal_ranked = _rank_by_effective_salary(def_candidates)[: max(1, int(args.bench_try_top_def))]

    bench_def_ap = None
    bench_def_ap_ranked: list | None = None
    if args.bench_def_ap_combo is not None:
        _log(
            f"[bench-first] enumerate bench DEF AP combo={args.bench_def_ap_combo} "
            f"(max_models={args.bench_max_models}, max_candidates={args.bench_max_candidates})"
        )
        ap_candidates = solver.enumerate_defense_pairs_for_required_combos(
            required_combo_ids=[args.bench_def_ap_combo],
            constraints=base_constraints,
            max_models=args.bench_max_models,
            time_limit_seconds=args.bench_time_limit_seconds,
            max_candidates=args.bench_max_candidates,
        )
        if ap_candidates:
            bench_def_ap_ranked = _rank_by_effective_salary(ap_candidates)[: max(1, int(args.bench_try_top_def_ap))]

    def _select_goalies(goalies_universe: list, *, cap: int) -> list:
        has_salary = any(getattr(g, "salary", None) is not None for g in goalies_universe)
        by_ovr = sorted(goalies_universe, key=lambda g: int(g.overall), reverse=True)
        if not has_salary:
            return by_ovr[:cap]

        def salary_key(g) -> tuple[int, int, str]:
            salary = getattr(g, "salary", None)
            s = int(salary) if salary is not None else 10**9
            return (s, -int(g.overall), str(g.id))

        by_salary = sorted(goalies_universe, key=salary_key)
        selected_ids: set[str] = set()
        for g in by_ovr[: min(len(by_ovr), max(10, cap))]:
            selected_ids.add(str(g.id))
        for g in by_salary[: min(len(by_salary), max(10, cap))]:
            selected_ids.add(str(g.id))
        selected = [g for g in by_salary if str(g.id) in selected_ids]
        return selected[:cap]

    # ------------------------------------------------------------------
    # 2) Freeze bench selections into full-team program
    # ------------------------------------------------------------------
    _log("[bench-first] solve full-team (offline)")
    solve_time_limit = args.solve_time_limit_seconds if args.solve_time_limit_seconds is not None else args.time_limit_seconds
    solve_time_limit = int(solve_time_limit) if solve_time_limit is not None else None
    feasibility_time_limit = int(args.feasibility_time_limit_seconds) if args.feasibility_time_limit_seconds is not None else None
    attempts: list[dict] = []
    solutions: list = []
    selected_bench = None

    # If we disable bench requirements, we run a single feasibility check without freezing any picks.
    if args.no_bench_requirements:
        fixed: list[FixedPick] = []
        fixed_facts = "disable_bench_requirements.\n"
        fwd_variants = [None]
        def_variants = [None]
        def_ap_variants = [None]
    else:
        fixed_facts = ""
        # Convention: "bench" forward line is line 3 (slots 7..9), "bench" defense pair is pair 3 (slots 17..18).
        fwd_variants = bench_fwd_ranked
        def_variants = bench_def_sal_ranked
        def_ap_variants = bench_def_ap_ranked if bench_def_ap_ranked is not None else [None]

    for bench_fwd in fwd_variants:
        for bench_def_sal in def_variants:
            for bench_def_ap in def_ap_variants:
                fixed = []
                fixed_facts = "disable_bench_requirements.\n" if args.no_bench_requirements else ""
                if not args.no_bench_requirements:
                    _log(
                        f"[bench-first] attempt: fwd_salary={bench_fwd.total_salary} fwd_ovr={bench_fwd.total_base_ovr} "
                        f"def_salary={bench_def_sal.total_salary} def_ovr={bench_def_sal.total_base_ovr}"
                    )
                    for slot, player in zip((7, 8, 9), bench_fwd.players, strict=True):
                        fixed.append(
                            FixedPick(slot=slot, card_id=str(player.id), label=f"bench_fwd combo={args.bench_fwd_combo}")
                        )
                    for slot, player in zip((17, 18), bench_def_sal.players, strict=True):
                        fixed.append(
                            FixedPick(
                                slot=slot,
                                card_id=str(player.id),
                                label=f"bench_def_sal combo={args.bench_def_sal_combo}",
                            )
                        )
                    if bench_def_ap is not None:
                        for slot, player in zip((15, 16), bench_def_ap.players, strict=True):
                            fixed.append(
                                FixedPick(
                                    slot=slot,
                                    card_id=str(player.id),
                                    label=f"bench_def_ap combo={args.bench_def_ap_combo}",
                                )
                            )
                    fixed_facts = _fixed_facts(fixed)

                # Candidate pools: filtered + target-focused pruning.
                #
                # Important: do NOT remove the fixed card IDs from the fact base.
                forwards = solver.loader.get_forwards()
                defense = solver.loader.get_defense()
                goalies = solver.loader.get_goalies()

                fwd_combos = solver.loader.get_forward_combos()
                def_combos = solver.loader.get_defense_combos()
                if args.reduce_combos and not args.no_bench_requirements:
                    fwd_keep = {int(args.bench_fwd_combo)}
                    def_keep = {int(args.bench_def_sal_combo)}
                    if args.bench_def_ap_combo is not None:
                        def_keep.add(int(args.bench_def_ap_combo))
                    fwd_combos = [c for c in fwd_combos if int(c.id) in fwd_keep]
                    def_combos = [c for c in def_combos if int(c.id) in def_keep]

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
                goalies = solver.loader.filter_players(
                    goalies,
                    min_ovr=base_constraints.min_ovr,
                    team=base_constraints.required_team,
                    nationality=base_constraints.required_nationality,
                    event=base_constraints.required_event,
                    excluded_ids=base_constraints.excluded_player_ids,
                )

                target = OptimizationTarget(args.target)
                forwards_universe = forwards
                defense_universe = defense
                goalies_universe = goalies

                forwards = solver._select_candidates(forwards_universe, fwd_combos, target=target)
                defense = solver._select_candidates(defense_universe, def_combos, target=target)
                goalies = _select_goalies(goalies_universe, cap=max(int(args.max_g), 10))

                # Candidate caps must remain cap-feasible. Even if the *objective*
                # is OVR, truncating purely by OVR often drops the cheap "filler"
                # cards and makes the salary-cap UNSAT.
                cap_sort_target = OptimizationTarget.SALARY if args.max_salary is not None else target
                sort_key = solver._candidate_sort_key(target)
                cap_sort_key = solver._candidate_sort_key(cap_sort_target)

                forwards.sort(key=cap_sort_key)
                defense.sort(key=cap_sort_key)
                goalies.sort(key=cap_sort_key)

                fixed_fwd_ids = {p.card_id for p in fixed if p.slot in (7, 8, 9)}
                fixed_def_ids = {p.card_id for p in fixed if p.slot in (17, 18)}
                fixed_g_ids: set[str] = set()

                fwd_by_id = {str(p.id): p for p in forwards_universe}
                def_by_id = {str(p.id): p for p in defense_universe}
                g_by_id = {str(p.id): p for p in goalies_universe}

                for cid in sorted(fixed_fwd_ids):
                    if cid not in {str(p.id) for p in forwards} and cid in fwd_by_id:
                        forwards.append(fwd_by_id[cid])
                for cid in sorted(fixed_def_ids):
                    if cid not in {str(p.id) for p in defense} and cid in def_by_id:
                        defense.append(def_by_id[cid])
                for cid in sorted(fixed_g_ids):
                    if cid not in {str(p.id) for p in goalies} and cid in g_by_id:
                        goalies.append(g_by_id[cid])

                if args.dedupe_by_player:
                    forwards = _dedupe_keep_fixed(forwards, fixed_card_ids=fixed_fwd_ids)
                    defense = _dedupe_keep_fixed(defense, fixed_card_ids=fixed_def_ids)
                    goalies = _dedupe_keep_fixed(goalies, fixed_card_ids=fixed_g_ids)

                forwards.sort(key=cap_sort_key)
                defense.sort(key=cap_sort_key)
                goalies.sort(key=cap_sort_key)

                forwards = _force_include_players(
                    players=forwards,
                    required_card_ids=fixed_fwd_ids,
                    cap=args.max_fwd,
                    sort_key=cap_sort_key,
                )
                defense = _force_include_players(
                    players=defense,
                    required_card_ids=fixed_def_ids,
                    cap=args.max_def,
                    sort_key=cap_sort_key,
                )
                goalies = _force_include_players(
                    players=goalies,
                    required_card_ids=fixed_g_ids,
                    cap=args.max_g,
                    sort_key=cap_sort_key,
                )

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
                        solver._full_team_floor_facts(
                            min_fwd_line1=args.min_fwd1,
                            min_fwd_line2=args.min_fwd2,
                            min_def_top4=args.min_def12,
                            min_g1=args.min_g1,
                        ),
                        solver._read_rules("base.lp"),
                        solver._read_rules("full_team.lp"),
                    ]
                )

                started = datetime.now(timezone.utc).isoformat()
                _log(
                    f"[bench-first] feasibility: time_limit={feasibility_time_limit}s "
                    f"optimize_after_feasible={bool(args.optimize_after_feasible)}"
                )
                feas_started = datetime.now(timezone.utc).isoformat()
                feas_models, feas_status = solver._solve_any(
                    program,
                    max_models=1,
                    time_limit_seconds=feasibility_time_limit,
                )
                feas_finished = datetime.now(timezone.utc).isoformat()
                _log(f"[bench-first] feasibility: status={feas_status} models={len(feas_models)}")

                feasible_solution = (
                    solver._parse_full_team_model(
                        symbols=feas_models[0],
                        forwards=forwards,
                        defense=defense,
                        goalies=goalies,
                        fwd_combos=fwd_combos,
                        def_combos=def_combos,
                        rank=1,
                    )
                    if feas_models and feas_status == "sat"
                    else None
                )

                parsed: list = []
                if feasible_solution is not None and not args.optimize_after_feasible:
                    parsed = [feasible_solution]
                elif feasible_solution is not None and args.optimize_after_feasible:
                    _log(
                        f"[bench-first] optimizing: time_limit={solve_time_limit}s num_solutions={args.num_solutions}"
                    )
                    models = solver._solve(
                        program,
                        num_solutions=args.num_solutions,
                        model_limit=solver._model_limit(target=target, is_full_team=True),
                        time_limit_seconds=solve_time_limit,
                    )
                    parsed = [
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
                finished = datetime.now(timezone.utc).isoformat()

                attempts.append(
                    {
                        "started_utc": started,
                        "finished_utc": finished,
                        "feasibility": {
                            "started_utc": feas_started,
                            "finished_utc": feas_finished,
                            "status": feas_status,
                            "time_limit_seconds": feasibility_time_limit,
                        },
                        "bench_fwd": bench_fwd.model_dump() if bench_fwd is not None else None,
                        "bench_def_sal": bench_def_sal.model_dump() if bench_def_sal is not None else None,
                        "bench_def_ap": bench_def_ap.model_dump() if bench_def_ap is not None else None,
                        "fixed_slots": [p.__dict__ for p in fixed],
                        "solutions_found": len(parsed),
                        "pool_sizes": {
                            "forwards": len(forwards),
                            "defense": len(defense),
                            "goalies": len(goalies),
                        },
                        "pool_unique_player_ids": {
                            "forwards": len({getattr(p, "player_id", None) for p in forwards}),
                            "defense": len({getattr(p, "player_id", None) for p in defense}),
                            "goalies": len({getattr(p, "player_id", None) for p in goalies}),
                            "total": len(
                                {
                                    getattr(p, "player_id", None)
                                    for p in (list(forwards) + list(defense) + list(goalies))
                                }
                            ),
                        },
                        "candidate_caps": {"max_fwd": args.max_fwd, "max_def": args.max_def, "max_g": args.max_g},
                    }
                )

                if parsed:
                    solutions = parsed
                    selected_bench = {"bench_fwd": bench_fwd, "bench_def_sal": bench_def_sal, "bench_def_ap": bench_def_ap}
                    break
            if solutions:
                break
        if solutions:
            break

    out_path = Path(args.json_out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "attempts": attempts,
        "constraints": base_constraints.model_dump(),
        "target": target.value,
        "bench": {
            "bench_fwd_combo": args.bench_fwd_combo,
            "bench_def_sal_combo": args.bench_def_sal_combo,
            "bench_def_ap_combo": args.bench_def_ap_combo,
            "picked": (
                {
                    "bench_fwd": selected_bench["bench_fwd"].model_dump(),
                    "bench_def_sal": selected_bench["bench_def_sal"].model_dump(),
                    "bench_def_ap": selected_bench["bench_def_ap"].model_dump()
                    if selected_bench["bench_def_ap"] is not None
                    else None,
                }
                if selected_bench is not None
                else None
            ),
        },
        "candidate_caps": {"max_fwd": args.max_fwd, "max_def": args.max_def, "max_g": args.max_g},
        "solutions": [s.model_dump() for s in solutions],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {len(solutions)} solution(s) to {out_path}")
    if selected_bench is not None:
        bf = selected_bench["bench_fwd"]
        bd = selected_bench["bench_def_sal"]
        print(
            f"Bench picks: fwd(combo {args.bench_fwd_combo}) salary={bf.total_salary} base_ovr={bf.total_base_ovr}; "
            f"def(combo {args.bench_def_sal_combo}) salary={bd.total_salary} base_ovr={bd.total_base_ovr}"
        )
        if selected_bench["bench_def_ap"] is not None:
            bap = selected_bench["bench_def_ap"]
            print(
            f"Bench picks: def_ap(combo {args.bench_def_ap_combo}) ap={bap.total_ap} salary={bap.total_salary} "
            f"base_ovr={bap.total_base_ovr}"
        )
    if args.no_bench_requirements:
        print("Bench requirements were disabled (disable_bench_requirements).")
    if solutions:
        best = solutions[0]
        print(
            f"Top full-team: base_ovr={best.total_base_ovr} ovr_bonus={best.ovr_bonus} "
            f"salary={best.total_salary} ap={best.total_ap} active_combos={len(best.active_combos)}"
        )
    else:
        print(
            "No full-team model found under current caps/candidate caps + fixed bench selections "
            f"(feasibility-time-limit={feasibility_time_limit}s)."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
