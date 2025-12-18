from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable, Optional

from ..core.data_loader import get_data_loader
from ..core.models import (
    ActiveCombo,
    LineSolution,
    OptimizationConstraints,
    OptimizationTarget,
    Player,
    Position,
)


class ASPSolver:
    """
    Clingo-backed solver for NHL 26 line optimization.

    This is intentionally written to be importable even when the `clingo` Python
    package is not installed; methods that require Clingo will raise a clear
    error at runtime.
    """

    def __init__(
        self,
        *,
        data_dir: str = "data/",
        clingo_threads: int = 1,
        max_candidates_total: int = 350,
        max_candidates_global: int = 200,
        max_candidates_per_condition: int = 25,
        max_fullteam_forwards: int = 24,
        max_fullteam_defense: int = 14,
        max_fullteam_goalies: int = 4,
    ) -> None:
        self.loader = get_data_loader(data_dir)
        self.clingo_threads = max(1, int(clingo_threads))
        self.max_candidates_total = max_candidates_total
        self.max_candidates_global = max_candidates_global
        self.max_candidates_per_condition = max_candidates_per_condition
        self.max_fullteam_forwards = max_fullteam_forwards
        self.max_fullteam_defense = max_fullteam_defense
        self.max_fullteam_goalies = max_fullteam_goalies

    @staticmethod
    def is_available() -> bool:
        """Return True if the `clingo` Python package is importable."""
        return importlib.util.find_spec("clingo") is not None

    # ---------------------------------------------------------------------
    # Public API used by FastAPI routes
    # ---------------------------------------------------------------------

    def optimize_forward_line(
            self,
            constraints: OptimizationConstraints,
            target: OptimizationTarget,
            num_solutions: int = 5,
        ) -> list[LineSolution]:
        forwards = self.loader.get_forwards()
        combos = self.loader.get_forward_combos()

        forwards = self.loader.filter_players(
            forwards,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )
        forwards = self._dedupe_best_card_per_player(forwards)

        forwards = self._select_candidates(forwards, combos, target=target)

        program = "\n".join(
            [
                self._generate_facts(
                    players=forwards,
                    combos=combos,
                    constraints=constraints,
                    is_forward=True,
                    target=target,
                ),
                self._read_rules("base.lp"),
                self._read_rules("forward_line.lp"),
            ]
        )

        models = self._solve(
            program,
            num_solutions=num_solutions,
            model_limit=self._model_limit(target=target, is_full_team=False),
        )
        return [
            self._parse_line_model(
                symbols=model,
                players=forwards,
                combos=combos,
                position=Position.FORWARD,
                expected_slots=(1, 2, 3),
                rank=i + 1,
            )
            for i, model in enumerate(models)
        ]

    def optimize_defense_pair(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        defense = self.loader.get_defense()
        combos = self.loader.get_defense_combos()

        defense = self.loader.filter_players(
            defense,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )
        defense = self._dedupe_best_card_per_player(defense)

        defense = self._select_candidates(defense, combos, target=target)

        program = "\n".join(
            [
                self._generate_facts(
                    players=defense,
                    combos=combos,
                    constraints=constraints,
                    is_forward=False,
                    target=target,
                ),
                self._read_rules("base.lp"),
                self._read_rules("defense_pair.lp"),
            ]
        )

        models = self._solve(
            program,
            num_solutions=num_solutions,
            model_limit=self._model_limit(target=target, is_full_team=False),
        )
        return [
            self._parse_line_model(
                symbols=model,
                players=defense,
                combos=combos,
                position=Position.DEFENSE,
                expected_slots=(1, 2),
                rank=i + 1,
            )
            for i, model in enumerate(models)
        ]

    def optimize_full_team(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
        time_limit_seconds: int | None = None,
        *,
        min_fwd_line1: int | None = None,
        min_fwd_line2: int | None = None,
        min_def_top4: int | None = None,
        min_g1: int | None = None,
    ) -> list[LineSolution]:
        forwards = self.loader.get_forwards()
        defense = self.loader.get_defense()
        goalies = self.loader.get_goalies()

        forwards = self.loader.filter_players(
            forwards,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )
        defense = self.loader.filter_players(
            defense,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )
        # Goalies: ignore require_center etc.

        forwards = self._dedupe_best_card_per_player(forwards)
        defense = self._dedupe_best_card_per_player(defense)
        goalies = self._dedupe_best_card_per_player(goalies)

        fwd_combos = self.loader.get_forward_combos()
        def_combos = self.loader.get_defense_combos()

        forwards = self._select_candidates(forwards, fwd_combos, target=target)
        defense = self._select_candidates(defense, def_combos, target=target)
        goalies = goalies[:10]  # cap goalies to reduce search space

        # Keep the full-team candidate pool focused. For bonus-oriented targets we
        # prefer cheaper cards to keep the cap feasible; for OVR we prefer raw OVR.
        sort_key = self._candidate_sort_key(target)
        forwards.sort(key=sort_key)
        defense.sort(key=sort_key)
        goalies.sort(key=sort_key)

        forwards = forwards[: self.max_fullteam_forwards]
        defense = defense[: self.max_fullteam_defense]
        goalies = goalies[: self.max_fullteam_goalies]

        floor_facts = self._full_team_floor_facts(
            min_fwd_line1=min_fwd_line1,
            min_fwd_line2=min_fwd_line2,
            min_def_top4=min_def_top4,
            min_g1=min_g1,
        )

        program = "\n".join(
            [
                self._generate_full_team_facts(
                    forwards=forwards,
                    defense=defense,
                    goalies=goalies,
                    fwd_combos=fwd_combos,
                    def_combos=def_combos,
                    constraints=constraints,
                    target=target,
                ),
                floor_facts,
                self._read_rules("base.lp"),
                self._read_rules("full_team.lp"),
            ]
        )

        models = self._solve(
            program,
            num_solutions=num_solutions,
            model_limit=self._model_limit(target=target, is_full_team=True),
            time_limit_seconds=time_limit_seconds,
        )
        return [
            self._parse_full_team_model(
                symbols=model,
                forwards=forwards,
                defense=defense,
                goalies=goalies,
                fwd_combos=fwd_combos,
                def_combos=def_combos,
                rank=i + 1,
            )
            for i, model in enumerate(models)
        ]

    def validate_line(
        self,
        player_ids: list[int],
        position_type: str,  # "forward" or "defense"
    ) -> dict:
        if position_type == "forward":
            players = self.loader.get_forwards()
            combos = self.loader.get_forward_combos()
            expected_count = 3
        else:
            players = self.loader.get_defense()
            combos = self.loader.get_defense_combos()
            expected_count = 2

        if len(player_ids) != expected_count:
            return {
                "valid": False,
                "error": f"Expected {expected_count} players, got {len(player_ids)}",
            }

        player_map = {}
        for p in players:
            # Allow lookup by either card_id or player_id
            keys = [str(p.id)]
            if p.player_id is not None:
                keys.append(str(p.player_id))
            for key in keys:
                existing = player_map.get(key)
                if existing is None or p.overall > existing.overall:
                    player_map[key] = p

        selected = []
        for pid in player_ids:
            pid_key = str(pid)
            if pid_key not in player_map:
                return {"valid": False, "error": f"Player ID not found: {pid}"}
            selected.append(player_map[pid_key])

        active = []
        for combo in combos:
            conditions = combo.get_conditions()
            matches = 0
            for i, cond in enumerate(conditions):
                if i < len(selected) and selected[i].matches_condition(cond.type, cond.key):
                    matches += 1
            if matches == len(conditions):
                active.append(
                    {
                        "id": combo.id,
                        "reward_type": combo.reward_type.value,
                        "reward_amount": combo.reward_amount,
                    }
                )

        total_ovr = sum(p.overall for p in selected)
        ovr_bonus = sum(
            c["reward_amount"] for c in active if c["reward_type"] == "OVR"
        )

        return {
            "valid": True,
            "players": [
                {
                    "id": p.id,
                    "name": f"{p.first_name} {p.last_name}",
                    "overall": p.overall,
                    "team": p.team,
                    "nationality": p.nationality,
                }
                for p in selected
            ],
            "total_base_ovr": total_ovr,
            "ovr_bonus": ovr_bonus,
            "effective_ovr": total_ovr + ovr_bonus,
            "active_combos": active,
        }

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _dedupe_best_card_per_player(players: list) -> list:
        """Keep only the highest-OVR row per player ID."""
        best: dict[object, object] = {}
        for p in players:
            key = p.player_id if p.player_id is not None else p.id
            existing = best.get(key)
            if existing is None or p.overall > existing.overall:
                best[key] = p
        return list(best.values())

    def _select_candidates(self, players: list, combos: list, *, target: OptimizationTarget) -> list:
        """
        Reduce search space by selecting a candidate subset.

        Strategy:
        - Always include a small set of top-OVR players (keeps quality for any target)
        - Include a target-focused global slice (cheap cards for salary/balanced/ap)
        - Include top K players per combo condition (target-focused)
        - Cap total candidates to max_candidates_total (target-focused)
        """
        # For OVR optimization we still need a cap-feasible pool for full-team.
        # If we only keep the top tail by OVR, we often drop the cheap "filler"
        # cards that make the salary cap satisfiable.
        #
        # Heuristic: keep top-by-OVR (quality) + top-by-cheapest (feasibility) +
        # a few per combo-condition to avoid missing rare keys.
        if target == OptimizationTarget.OVR:
            by_ovr = sorted(players, key=lambda p: int(p.overall), reverse=True)
            has_salary = any(getattr(p, "salary", None) is not None for p in players)

            selected_ids: set[str] = set()

            top_ovr_n = min(80, len(by_ovr))
            for p in by_ovr[:top_ovr_n]:
                selected_ids.add(str(p.id))

            if has_salary:
                def salary_key(p) -> tuple[int, int, str]:
                    salary = getattr(p, "salary", None)
                    s = int(salary) if salary is not None else 10**9
                    return (s, -int(p.overall), str(p.id))

                by_salary = sorted(players, key=salary_key)
                top_salary_n = min(80, len(by_salary))
                for p in by_salary[:top_salary_n]:
                    selected_ids.add(str(p.id))

                for combo in combos:
                    for cond in combo.get_conditions():
                        matching = [p for p in players if p.matches_condition(cond.type, cond.key)]
                        matching.sort(key=salary_key)
                        for p in matching[:8]:
                            selected_ids.add(str(p.id))

            # Deterministic ordering: by OVR first.
            selected = [p for p in by_ovr if str(p.id) in selected_ids]
            return selected[: min(len(selected), 160)]

        max_total = self.max_candidates_total
        max_global = self.max_candidates_global
        max_per_condition = self.max_candidates_per_condition

        # Bonus-oriented targets get a much smaller candidate pool to keep the
        # search space tractable under optimization (especially for SALARY/BALANCED).
        max_total = min(max_total, 160)
        max_global = min(max_global, 120)
        max_per_condition = min(max_per_condition, 12)

        if len(players) <= max_total:
            return players

        by_ovr = sorted(players, key=lambda p: p.overall, reverse=True)
        sort_key = self._candidate_sort_key(target)
        by_target = sorted(players, key=sort_key)
        selected_ids: set[str] = set()

        if target == OptimizationTarget.OVR:
            global_primary = by_ovr[: max_global]
            global_fallback = []
        else:
            global_primary = by_target[: max_global]
            global_fallback = by_ovr[: min(25, max_global)]

        for p in global_primary + global_fallback:
            selected_ids.add(str(p.id))

        for combo in combos:
            for cond in combo.get_conditions():
                matching = [p for p in players if p.matches_condition(cond.type, cond.key)]
                matching.sort(key=sort_key)
                for p in matching[: max_per_condition]:
                    selected_ids.add(str(p.id))

        base_order = by_ovr if target == OptimizationTarget.OVR else by_target
        selected = [p for p in base_order if str(p.id) in selected_ids]
        if len(selected) > max_total:
            selected = selected[: max_total]
        return selected

    @staticmethod
    def _candidate_sort_key(target: OptimizationTarget):
        """
        Sort key for candidate selection.

        For bonus-oriented targets we want to keep the candidate pool "cap-feasible"
        by preferring cheaper cards (and then higher OVR as a tie-break).
        """

        def key(p) -> tuple:
            salary = getattr(p, "salary", None)
            ap = getattr(p, "ability_points", None)
            salary_key = int(salary) if salary is not None else 10**9
            ap_key = int(ap) if ap is not None else 10**9

            if target == OptimizationTarget.OVR:
                return (-int(p.overall), salary_key, ap_key, str(p.id))
            if target == OptimizationTarget.SALARY:
                return (salary_key, -int(p.overall), ap_key, str(p.id))
            if target == OptimizationTarget.AP:
                return (ap_key, -int(p.overall), salary_key, str(p.id))
            return (salary_key, ap_key, -int(p.overall), str(p.id))

        return key

    @staticmethod
    def _model_limit(*, target: OptimizationTarget, is_full_team: bool) -> int | None:
        """
        Keep API responsive under expensive objectives.

        For bonus-oriented targets we typically do not need proven optimality.
        Instead, we cap the number of models explored and return the best model
        encountered so far. This keeps the API responsive and avoids long
        optimality proofs.
        """
        if target == OptimizationTarget.OVR:
            return None
        return 50 if is_full_team else 250

    @staticmethod
    def _read_rules(filename: str) -> str:
        path = Path(__file__).parent / "rules" / filename
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _symbol_value(sym):
        """
        Extract a Python value from a clingo Symbol (supports numbers and strings).
        """
        try:
            return sym.number
        except Exception:
            pass
        try:
            return sym.string
        except Exception:
            pass
        return str(sym)

    @staticmethod
    def _clingo_str(value: str) -> str:
        safe = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()
        return f'"{safe}"'

    @staticmethod
    def _full_team_floor_facts(
        *,
        min_fwd_line1: int | None = None,
        min_fwd_line2: int | None = None,
        min_def_top4: int | None = None,
        min_g1: int | None = None,
    ) -> str:
        """
        Optional, tunable OVR floors for `full_team.lp`.

        These are injected as simple facts and override the defaults defined in
        the ASP file via negation-as-failure.
        """
        lines: list[str] = []
        if min_fwd_line1 is not None:
            lines.append(f"min_fwd_line1({int(min_fwd_line1)}).")
        if min_fwd_line2 is not None:
            lines.append(f"min_fwd_line2({int(min_fwd_line2)}).")
        if min_def_top4 is not None:
            lines.append(f"min_def_top4({int(min_def_top4)}).")
        if min_g1 is not None:
            lines.append(f"min_g1({int(min_g1)}).")
        return "\n".join(lines)

    def _generate_facts(
        self,
        *,
        players: list,
        combos: list,
        constraints: OptimizationConstraints,
        is_forward: bool,
        target: OptimizationTarget,
    ) -> str:
        lines: list[str] = []
        lines.append(f"opt_target({self._clingo_str(target.value.lower())}).")

        for p in players:
            lines.append(
                "player("
                f"{self._clingo_str(str(p.id))}, {p.overall}, "
                f"{self._clingo_str(str(p.team).lower())}, "
                f"{self._clingo_str(str(p.nationality).lower())}, "
                f"{self._clingo_str(str(p.event).lower())}"
                ")."
            )
            if p.player_id is not None:
                lines.append(
                    f"card_player({self._clingo_str(str(p.id))}, {self._clingo_str(str(p.player_id))})."
                )
            # Extra safety: depending on the upstream dataset, `player_id` can be card-specific
            # (or otherwise insufficient) and may allow selecting multiple cards for the same
            # real-world person. We therefore also emit a canonical identity key derived from
            # (first_name, last_name, nationality) and enforce its uniqueness in `base.lp`.
            first_name = getattr(p, "first_name", None)
            last_name = getattr(p, "last_name", None)
            nationality = getattr(p, "nationality", None)
            if first_name and last_name and nationality:
                canon_key = (
                    f"{str(first_name).strip().lower()}|"
                    f"{str(last_name).strip().lower()}|"
                    f"{str(nationality).strip().lower()}"
                )
                lines.append(
                    f"card_canon({self._clingo_str(str(p.id))}, {self._clingo_str(canon_key)})."
                )

        if is_forward:
            for c in combos:
                conds = c.get_conditions()
                lines.append(
                    "fwd_combo("
                    f"{c.id}, {c.reward_amount}, {c.reward_type.value.lower()}, "
                    f"{self._clingo_str(str(conds[0].type).lower())}, {self._clingo_str(str(conds[0].key).lower())}, "
                    f"{self._clingo_str(str(conds[1].type).lower())}, {self._clingo_str(str(conds[1].key).lower())}, "
                    f"{self._clingo_str(str(conds[2].type).lower())}, {self._clingo_str(str(conds[2].key).lower())}"
                    ")."
                )
        else:
            for c in combos:
                conds = c.get_conditions()
                lines.append(
                    "def_combo("
                    f"{c.id}, {c.reward_amount}, {c.reward_type.value.lower()}, "
                    f"{self._clingo_str(str(conds[0].type).lower())}, {self._clingo_str(str(conds[0].key).lower())}, "
                    f"{self._clingo_str(str(conds[1].type).lower())}, {self._clingo_str(str(conds[1].key).lower())}"
                    ")."
                )

        if constraints.min_ovr > 0:
            lines.append(f"min_ovr({constraints.min_ovr}).")

        for pid in constraints.excluded_player_ids:
            lines.append(f"excluded({self._clingo_str(str(pid))}).")

        if constraints.required_team:
            lines.append(f"required_team({self._clingo_str(constraints.required_team.lower())}).")
        if constraints.required_nationality:
            lines.append(
                f"required_nationality({self._clingo_str(constraints.required_nationality.lower())})."
            )
        if constraints.required_event:
            lines.append(f"required_event({self._clingo_str(constraints.required_event.lower())}).")

        if constraints.require_center:
            lines.append("require_center.")

        if constraints.max_salary is not None:
            lines.append(f"max_salary({int(constraints.max_salary)}).")
        if constraints.max_ap is not None:
            lines.append(f"max_ap({int(constraints.max_ap)}).")

        for p in players:
            sub_pos = getattr(p, "sub_position", None)
            if not sub_pos:
                pos = getattr(p, "position", None)
                if pos and str(pos).upper() not in {"FWD", "DEF", "G"}:
                    sub_pos = pos
            if sub_pos:
                lines.append(
                    f"sub_pos({self._clingo_str(str(p.id))}, {self._clingo_str(str(sub_pos).lower())})."
                )
            if p.salary is not None:
                lines.append(f"salary({self._clingo_str(str(p.id))}, {int(p.salary)}).")
            ap = getattr(p, "ability_points", None)
            if ap is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(ap)}).")

        return "\n".join(lines)

    def _generate_full_team_facts(
        self,
        *,
        forwards: list,
        defense: list,
        goalies: list,
        fwd_combos: list,
        def_combos: list,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
    ) -> str:
        lines: list[str] = []
        lines.append(f"opt_target({self._clingo_str(target.value.lower())}).")

        # Players with position tags and common attributes
        for p in forwards:
            lines.append(
                "player("
                f"{self._clingo_str(str(p.id))}, {p.overall}, "
                f"{self._clingo_str(str(p.team).lower())}, "
                f"{self._clingo_str(str(p.nationality).lower())}, "
                f"{self._clingo_str(str(p.event).lower())}"
                ")."
            )
            lines.append(f"forward({self._clingo_str(str(p.id))}).")
            if p.player_id is not None:
                lines.append(
                    f"card_player({self._clingo_str(str(p.id))}, {self._clingo_str(str(p.player_id))})."
                )
            sub_pos = getattr(p, "sub_position", None)
            if not sub_pos:
                pos = getattr(p, "position", None)
                if pos and str(pos).upper() not in {"FWD", "DEF", "G"}:
                    sub_pos = pos
            if sub_pos:
                lines.append(
                    f"sub_pos({self._clingo_str(str(p.id))}, {self._clingo_str(str(sub_pos).lower())})."
                )
            if p.salary is not None:
                lines.append(f"salary({self._clingo_str(str(p.id))}, {int(p.salary)}).")
            ap = getattr(p, "ability_points", None)
            if ap is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(ap)}).")

        for p in defense:
            lines.append(
                "player("
                f"{self._clingo_str(str(p.id))}, {p.overall}, "
                f"{self._clingo_str(str(p.team).lower())}, "
                f"{self._clingo_str(str(p.nationality).lower())}, "
                f"{self._clingo_str(str(p.event).lower())}"
                ")."
            )
            lines.append(f"defense_player({self._clingo_str(str(p.id))}).")
            if p.player_id is not None:
                lines.append(
                    f"card_player({self._clingo_str(str(p.id))}, {self._clingo_str(str(p.player_id))})."
                )
            if p.salary is not None:
                lines.append(f"salary({self._clingo_str(str(p.id))}, {int(p.salary)}).")
            ap = getattr(p, "ability_points", None)
            if ap is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(ap)}).")

        for p in goalies:
            lines.append(
                "player("
                f"{self._clingo_str(str(p.id))}, {p.overall}, "
                f"{self._clingo_str(str(p.team).lower())}, "
                f"{self._clingo_str(str(p.nationality).lower())}, "
                f"{self._clingo_str(str(p.event).lower())}"
                ")."
            )
            lines.append(f"goalie({self._clingo_str(str(p.id))}).")
            if p.player_id is not None:
                lines.append(
                    f"card_player({self._clingo_str(str(p.id))}, {self._clingo_str(str(p.player_id))})."
                )
            if p.salary is not None:
                lines.append(f"salary({self._clingo_str(str(p.id))}, {int(p.salary)}).")
            ap = getattr(p, "ability_points", None)
            if ap is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(ap)}).")

        # Combo facts
        for c in fwd_combos:
            conds = c.get_conditions()
            lines.append(
                "fwd_combo("
                f"{c.id}, {c.reward_amount}, {c.reward_type.value.lower()}, "
                f"{self._clingo_str(str(conds[0].type).lower())}, {self._clingo_str(str(conds[0].key).lower())}, "
                f"{self._clingo_str(str(conds[1].type).lower())}, {self._clingo_str(str(conds[1].key).lower())}, "
                f"{self._clingo_str(str(conds[2].type).lower())}, {self._clingo_str(str(conds[2].key).lower())}"
                ")."
            )
        for c in def_combos:
            conds = c.get_conditions()
            lines.append(
                "def_combo("
                f"{c.id}, {c.reward_amount}, {c.reward_type.value.lower()}, "
                f"{self._clingo_str(str(conds[0].type).lower())}, {self._clingo_str(str(conds[0].key).lower())}, "
                f"{self._clingo_str(str(conds[1].type).lower())}, {self._clingo_str(str(conds[1].key).lower())}"
                ")."
            )

        if constraints.min_ovr > 0:
            lines.append(f"min_ovr({constraints.min_ovr}).")
        for pid in constraints.excluded_player_ids:
            lines.append(f"excluded({self._clingo_str(str(pid))}).")
        if constraints.required_team:
            lines.append(f"required_team({self._clingo_str(constraints.required_team.lower())}).")
        if constraints.required_nationality:
            lines.append(
                f"required_nationality({self._clingo_str(constraints.required_nationality.lower())})."
            )
        if constraints.required_event:
            lines.append(f"required_event({self._clingo_str(constraints.required_event.lower())}).")
        if constraints.require_center:
            lines.append("require_center.")
        if constraints.max_salary is not None:
            lines.append(f"max_salary({int(constraints.max_salary)}).")
        if constraints.max_ap is not None:
            lines.append(f"max_ap({int(constraints.max_ap)}).")

        return "\n".join(lines)

    def _solve(
        self,
        program: str,
        *,
        num_solutions: int,
        model_limit: int | None = None,
        time_limit_seconds: int | None = None,
    ) -> list[list]:
        if not self.is_available():
            raise RuntimeError(
                "Clingo is not available. Install dependencies from "
                "`nhl26-line-combos-main/requirements.txt` in a Python version "
                "supported by `clingo`."
            )

        import clingo  # type: ignore
        import threading

        # NOTE:
        # On macOS with clingo 5.8.0, iterating a SolveHandle (yield_=True) while
        # using parallel-mode > 1 can crash with:
        #   RuntimeError: thread::join failed: Invalid argument
        #
        # Using `on_model` callbacks with `yield_=False` keeps the run stable,
        # while still allowing multi-threaded solving.
        def run_with_threads(threads: int) -> list[list]:
            models: list[list] = []
            best_cost: tuple[int, ...] | None = None
            ctl_ref: list["clingo.Control | None"] = [None]

            def on_model(model: "clingo.Model") -> bool:
                nonlocal best_cost, models
                cost = tuple(model.cost)
                symbols = model.symbols(shown=True)

                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    models = [symbols]
                elif cost == best_cost and len(models) < num_solutions:
                    models.append(symbols)

                if getattr(model, "optimality_proven", False) and best_cost is not None:
                    if len(models) >= num_solutions:
                        return False
                return True

            solve_error: list[BaseException] = []

            def run_solve() -> None:
                try:
                    ctl_args = [
                        "--warn=none",
                        "--opt-mode=optN",
                        "--models=0",
                        f"--parallel-mode={int(threads)}",
                    ]
                    ctl = clingo.Control(ctl_args)
                    ctl_ref[0] = ctl
                    if model_limit is not None:
                        ctl.configuration.solve.solve_limit = str(int(model_limit))
                    ctl.add("base", [], program)
                    ctl.ground([("base", [])])
                    ctl.solve(on_model=on_model, yield_=False)
                except BaseException as e:  # noqa: BLE001 - surface clingo errors to caller
                    solve_error.append(e)

            worker = threading.Thread(target=run_solve, daemon=True)
            worker.start()

            if time_limit_seconds is not None and int(time_limit_seconds) > 0:
                worker.join(float(time_limit_seconds))
                if worker.is_alive():
                    if ctl_ref[0] is not None:
                        ctl_ref[0].interrupt()
                    # Give clingo a moment to react; if it doesn't, we still return
                    # whatever best model we collected so far.
                    worker.join(1.0)
            else:
                worker.join()

            if solve_error:
                raise solve_error[0]
            return models

        try:
            return run_with_threads(self.clingo_threads)
        except RuntimeError as e:
            # On some macOS builds, parallel mode occasionally fails with:
            #   RuntimeError: thread::join failed: Invalid argument
            # Retry single-threaded to keep offline runs usable.
            if self.clingo_threads > 1 and "thread::join failed" in str(e):
                return run_with_threads(1)
            raise

    def _enumerate(
        self,
        program: str,
        *,
        max_models: int,
        model_limit: int | None = None,
        time_limit_seconds: int | None = None,
    ) -> list[list]:
        """
        Enumerate stable models (no optimization assumptions).

        This is used for Goal 1 style enumeration tasks where we want to list
        multiple concrete line realizations for a fixed set of required combos.
        """
        if not self.is_available():
            raise RuntimeError(
                "Clingo is not available. Install dependencies from "
                "`requirements.txt` in a Python version supported by `clingo`."
            )

        import clingo  # type: ignore
        import threading

        def run_with_threads(threads: int) -> list[list]:
            models_arg = "--models=0" if max_models == 0 else f"--models={int(max_models)}"
            models: list[list] = []
            ctl_ref: list["clingo.Control | None"] = [None]

            def on_model(model: "clingo.Model") -> bool:
                nonlocal models
                models.append(model.symbols(shown=True))
                if max_models != 0 and len(models) >= max_models:
                    return False
                return True

            solve_error: list[BaseException] = []

            def run_solve() -> None:
                try:
                    ctl_args = ["--warn=none", models_arg, f"--parallel-mode={int(threads)}"]
                    ctl = clingo.Control(ctl_args)
                    ctl_ref[0] = ctl
                    if model_limit is not None:
                        ctl.configuration.solve.solve_limit = str(int(model_limit))
                    ctl.add("base", [], program)
                    ctl.ground([("base", [])])
                    ctl.solve(on_model=on_model, yield_=False)
                except BaseException as e:  # noqa: BLE001
                    solve_error.append(e)

            worker = threading.Thread(target=run_solve, daemon=True)
            worker.start()

            if time_limit_seconds is not None and int(time_limit_seconds) > 0:
                worker.join(float(time_limit_seconds))
                if worker.is_alive():
                    if ctl_ref[0] is not None:
                        ctl_ref[0].interrupt()
                    worker.join(1.0)
            else:
                worker.join()

            if solve_error:
                raise solve_error[0]
            return models

        try:
            return run_with_threads(self.clingo_threads)
        except RuntimeError as e:
            if self.clingo_threads > 1 and "thread::join failed" in str(e):
                return run_with_threads(1)
            raise

    def _solve_any(
        self,
        program: str,
        *,
        max_models: int = 1,
        time_limit_seconds: int | None = None,
    ) -> tuple[list[list], str]:
        """
        Find any stable model quickly (ignores optimization).

        This is useful as a feasibility check when the program contains
        `#maximize` statements but we don't want to wait for optimality proofs.
        """
        if not self.is_available():
            raise RuntimeError(
                "Clingo is not available. Install dependencies from "
                "`requirements.txt` in a Python version supported by `clingo`."
            )

        import clingo  # type: ignore

        def run_with_threads(threads: int) -> tuple[list[list], str]:
            models: list[list] = []

            models_arg = "--models=0" if int(max_models) == 0 else f"--models={int(max_models)}"
            ctl_args = [
                "--warn=none",
                "--opt-mode=ignore",
                models_arg,
                f"--parallel-mode={int(threads)}",
            ]

            def on_model(model: "clingo.Model") -> bool:
                models.append(model.symbols(shown=True))
                if int(max_models) != 0 and len(models) >= int(max_models):
                    return False
                return True

            ctl = clingo.Control(ctl_args)
            ctl.add("base", [], program)
            ctl.ground([("base", [])])
            if time_limit_seconds is not None and int(time_limit_seconds) > 0:
                with ctl.solve(on_model=on_model, async_=True, yield_=False) as handle:
                    finished = handle.wait(float(time_limit_seconds))
                    if not finished:
                        handle.cancel()
                        handle.wait()
                    res = handle.get()
            else:
                res = ctl.solve(on_model=on_model, yield_=False)
            if res.unsatisfiable:
                return models, "unsat"
            if res.unknown or res.interrupted:
                return models, "unknown"
            return models, "sat"

        try:
            return run_with_threads(self.clingo_threads)
        except RuntimeError as e:
            if self.clingo_threads > 1 and "thread::join failed" in str(e):
                return run_with_threads(1)
            raise

    def enumerate_forward_lines_for_required_combos(
        self,
        *,
        required_combo_ids: Iterable[int],
        constraints: OptimizationConstraints,
        max_models: int = 100,
        time_limit_seconds: int | None = None,
        max_candidates: int | None = None,
    ) -> list[LineSolution]:
        """
        Goal 1 (Stage B): enumerate concrete forward lines that satisfy a set of
        required forward combo IDs.

        This does not optimize; it enumerates up to `max_models` stable models.
        """
        forwards = self.loader.get_forwards()
        combos = self.loader.get_forward_combos()
        combo_map = {c.id: c for c in combos}

        required = [combo_map[cid] for cid in required_combo_ids if cid in combo_map]
        missing = [cid for cid in required_combo_ids if cid not in combo_map]
        if missing:
            raise ValueError(f"Unknown forward combo IDs: {missing}")

        forwards = self.loader.filter_players(
            forwards,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )

        # Safe pruning: for every required combo, each selected player must match
        # at least one of its conditions (otherwise the injective match is impossible).
        candidate_ids: set[str] | None = None
        for combo in required:
            eligible_for_combo = {
                str(p.id)
                for p in forwards
                if any(p.matches_condition(cond.type, cond.key) for cond in combo.get_conditions())
            }
            candidate_ids = eligible_for_combo if candidate_ids is None else candidate_ids & eligible_for_combo
        if candidate_ids is not None:
            forwards = [p for p in forwards if str(p.id) in candidate_ids]

        if max_candidates is not None and int(max_candidates) > 0:
            def bench_sort_key(p) -> tuple[int, int]:
                salary = getattr(p, "salary", None)
                salary_i = int(salary) if salary is not None else 10_000
                return (salary_i, -int(p.overall))

            forwards.sort(key=bench_sort_key)
            forwards = forwards[: int(max_candidates)]

        required_facts = "\n".join([f"required_combo({int(c.id)})." for c in required])
        program = "\n".join(
            [
                self._generate_facts(
                    players=forwards,
                    combos=combos,
                    constraints=constraints,
                    is_forward=True,
                    target=OptimizationTarget.OVR,
                ),
                required_facts,
                self._read_rules("base.lp"),
                self._read_rules("goal1_stageb_forward.lp"),
            ]
        )

        models = self._enumerate(
            program,
            max_models=max_models,
            time_limit_seconds=time_limit_seconds,
        )
        return [
            self._parse_line_model(
                symbols=model,
                players=forwards,
                combos=combos,
                position=Position.FORWARD,
                expected_slots=(1, 2, 3),
                rank=i + 1,
            )
            for i, model in enumerate(models)
        ]

    def enumerate_defense_pairs_for_required_combos(
        self,
        *,
        required_combo_ids: Iterable[int],
        constraints: OptimizationConstraints,
        max_models: int = 100,
        time_limit_seconds: int | None = None,
        max_candidates: int | None = None,
    ) -> list[LineSolution]:
        """
        Goal 1 (Stage B): enumerate concrete defense pairs that satisfy a set of
        required defense combo IDs.
        """
        defense = self.loader.get_defense()
        combos = self.loader.get_defense_combos()
        combo_map = {c.id: c for c in combos}

        required = [combo_map[cid] for cid in required_combo_ids if cid in combo_map]
        missing = [cid for cid in required_combo_ids if cid not in combo_map]
        if missing:
            raise ValueError(f"Unknown defense combo IDs: {missing}")

        defense = self.loader.filter_players(
            defense,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )

        candidate_ids: set[str] | None = None
        for combo in required:
            eligible_for_combo = {
                str(p.id)
                for p in defense
                if any(p.matches_condition(cond.type, cond.key) for cond in combo.get_conditions())
            }
            candidate_ids = eligible_for_combo if candidate_ids is None else candidate_ids & eligible_for_combo
        if candidate_ids is not None:
            defense = [p for p in defense if str(p.id) in candidate_ids]

        if max_candidates is not None and int(max_candidates) > 0:
            def bench_sort_key(p) -> tuple[int, int]:
                salary = getattr(p, "salary", None)
                salary_i = int(salary) if salary is not None else 10_000
                return (salary_i, -int(p.overall))

            defense.sort(key=bench_sort_key)
            defense = defense[: int(max_candidates)]

        required_facts = "\n".join([f"required_combo({int(c.id)})." for c in required])
        program = "\n".join(
            [
                self._generate_facts(
                    players=defense,
                    combos=combos,
                    constraints=constraints,
                    is_forward=False,
                    target=OptimizationTarget.OVR,
                ),
                required_facts,
                self._read_rules("base.lp"),
                self._read_rules("goal1_stageb_defense.lp"),
            ]
        )

        models = self._enumerate(
            program,
            max_models=max_models,
            time_limit_seconds=time_limit_seconds,
        )
        return [
            self._parse_line_model(
                symbols=model,
                players=defense,
                combos=combos,
                position=Position.DEFENSE,
                expected_slots=(1, 2),
                rank=i + 1,
            )
            for i, model in enumerate(models)
        ]

    def _parse_line_model(
        self,
        *,
        symbols: list,
        players: list,
        combos: list,
        position: Position,
        expected_slots: tuple[int, ...],
        rank: int,
    ) -> LineSolution:
        player_map = {str(p.id): p for p in players}
        combo_map = {c.id: c for c in combos}

        selected_by_slot: dict[int, Player] = {}
        active_combos: list[ActiveCombo] = []
        total_base_ovr: Optional[int] = None
        total_ovr_bonus: Optional[int] = None
        total_salary: Optional[int] = None
        total_salary_bonus: Optional[int] = None
        total_ap: Optional[int] = None
        total_ap_bonus: Optional[int] = None

        for atom in symbols:
            name = atom.name
            args = atom.arguments

            if name == "select":
                pid = self._symbol_value(args[0])
                slot = self._symbol_value(args[1])
                pid_key = str(pid)
                if pid_key in player_map:
                    p = player_map[pid_key]
                    sub_pos = getattr(p, "sub_position", None)
                    if not sub_pos:
                        pos = getattr(p, "position", None)
                        if pos and str(pos).upper() not in {"FWD", "DEF", "G"}:
                            sub_pos = pos
                    selected_by_slot[slot] = Player(
                        id=int(getattr(p, "id", 0) or 0),
                        player_id=int(getattr(p, "player_id", 0) or 0),
                        first_name=str(getattr(p, "first_name", "") or ""),
                        last_name=str(getattr(p, "last_name", "") or ""),
                        img=str(getattr(p, "img", "") or ""),
                        event=str(getattr(p, "event", "") or ""),
                        nationality=str(getattr(p, "nationality", "") or ""),
                        league=str(getattr(p, "league", "") or ""),
                        team=str(getattr(p, "team", "") or ""),
                        weight=float(getattr(p, "weight", 0.0) or 0.0),
                        height=int(getattr(p, "height", 0) or 0),
                        salary=float(getattr(p, "salary", 0.0) or 0.0),
                        overall=int(getattr(p, "overall", 0) or 0),
                        position=str(position),
                    )

            elif name == "combo_active":
                cid = self._symbol_value(args[0])
                if cid in combo_map:
                    c = combo_map[cid]
                    active_combos.append(
                        ActiveCombo(
                            id=c.id,
                            reward_type=c.reward_type,
                            reward_amount=c.reward_amount,
                            description=self._describe_combo(c),
                        )
                    )

            elif name == "total_base_ovr":
                total_base_ovr = self._symbol_value(args[0])

            elif name == "total_ovr_bonus":
                total_ovr_bonus = self._symbol_value(args[0])
            elif name == "total_salary":
                total_salary = self._symbol_value(args[0])
            elif name == "total_salary_bonus":
                total_salary_bonus = self._symbol_value(args[0])
            elif name == "total_ap":
                total_ap = self._symbol_value(args[0])
            elif name == "total_ap_bonus":
                total_ap_bonus = self._symbol_value(args[0])

        ordered_players = [selected_by_slot[s] for s in expected_slots if s in selected_by_slot]

        if total_base_ovr is None:
            total_base_ovr = sum(p.overall for p in ordered_players)
        if total_ovr_bonus is None:
            total_ovr_bonus = sum(
                c.reward_amount for c in active_combos if c.reward_type.value == "OVR"
            )
        if total_salary is None:
            total_salary = sum(getattr(p, "salary", 0) or 0 for p in ordered_players)
        if total_salary_bonus is None:
            total_salary_bonus = sum(
                c.reward_amount for c in active_combos if c.reward_type.value == "SAL"
            )
        if total_ap is None:
            total_ap = sum(getattr(p, "ability_points", 0) or 0 for p in ordered_players)
        if total_ap_bonus is None:
            total_ap_bonus = sum(
                c.reward_amount for c in active_combos if c.reward_type.value == "AP"
            )

        return LineSolution(
            rank=rank,
            players=ordered_players,
            total_base_ovr=total_base_ovr,
            ovr_bonus=total_ovr_bonus,
            effective_ovr=total_base_ovr + total_ovr_bonus,
            total_salary=total_salary - total_salary_bonus,
            total_ap=total_ap - total_ap_bonus,
            active_combos=active_combos,
        )

    @staticmethod
    def _describe_combo(combo) -> str:
        conditions = combo.get_conditions()
        return " + ".join([f"{c.type}={c.key}" for c in conditions])

    def _parse_full_team_model(
        self,
        *,
        symbols: list,
        forwards: list,
        defense: list,
        goalies: list,
        fwd_combos: list,
        def_combos: list,
        rank: int,
    ) -> LineSolution:
        player_map = {str(p.id): p for p in forwards + defense + goalies}
        fwd_combo_map = {c.id: c for c in fwd_combos}
        def_combo_map = {c.id: c for c in def_combos}

        selected_by_slot: dict[int, Player] = {}
        active_combos: list[ActiveCombo] = []
        total_base_ovr: Optional[int] = None
        total_ovr_bonus: Optional[int] = None
        total_salary: Optional[int] = None
        total_salary_bonus: Optional[int] = None
        total_ap: Optional[int] = None
        total_ap_bonus: Optional[int] = None

        for atom in symbols:
            name = atom.name
            args = atom.arguments

            if name == "select":
                pid = self._symbol_value(args[0])
                slot = self._symbol_value(args[1])
                pos = (
                    Position.FORWARD
                    if slot <= 12
                    else Position.DEFENSE
                    if slot <= 18
                    else Position.GOALIE
                )
                pid_key = str(pid)
                if pid_key in player_map:
                    p = player_map[pid_key]
                    selected_by_slot[slot] = Player(
                        id=str(p.id),
                        player_id=p.player_id,
                        first_name=p.first_name,
                        last_name=p.last_name,
                        sub_position=getattr(p, "sub_position", None),
                        event=p.event,
                        overall=p.overall,
                        nationality=p.nationality,
                        league=p.league,
                        team=p.team,
                        salary=getattr(p, "salary", None),
                        ability_points=getattr(p, "ability_points", None),
                        position=pos,
                    )

            elif name in ("combo_active", "combo_active_fwd", "combo_active_def"):
                cid = self._symbol_value(args[0])
                combo = fwd_combo_map.get(cid) or def_combo_map.get(cid)
                if combo:
                    active_combos.append(
                        ActiveCombo(
                            id=combo.id,
                            reward_type=combo.reward_type,
                            reward_amount=combo.reward_amount,
                            description=self._describe_combo(combo),
                        )
                    )

            elif name == "total_base_ovr":
                total_base_ovr = self._symbol_value(args[0])

            elif name == "total_ovr_bonus":
                total_ovr_bonus = self._symbol_value(args[0])
            elif name == "total_salary":
                total_salary = self._symbol_value(args[0])
            elif name == "total_salary_bonus":
                total_salary_bonus = self._symbol_value(args[0])
            elif name == "total_ap":
                total_ap = self._symbol_value(args[0])
            elif name == "total_ap_bonus":
                total_ap_bonus = self._symbol_value(args[0])

        ordered_players = [p for _, p in sorted(selected_by_slot.items(), key=lambda x: x[0])]

        if total_base_ovr is None:
            total_base_ovr = sum(p.overall for p in ordered_players)
        if total_ovr_bonus is None:
            total_ovr_bonus = sum(
                c.reward_amount for c in active_combos if c.reward_type.value == "OVR"
            )
        if total_salary is None:
            total_salary = sum(getattr(p, "salary", 0) or 0 for p in ordered_players)
        if total_salary_bonus is None:
            total_salary_bonus = sum(
                c.reward_amount for c in active_combos if c.reward_type.value == "SAL"
            )
        if total_ap is None:
            total_ap = sum(getattr(p, "ability_points", 0) or 0 for p in ordered_players)
        if total_ap_bonus is None:
            total_ap_bonus = sum(
                c.reward_amount for c in active_combos if c.reward_type.value == "AP"
            )

        return LineSolution(
            rank=rank,
            players=ordered_players,
            total_base_ovr=total_base_ovr,
            ovr_bonus=total_ovr_bonus,
            effective_ovr=total_base_ovr + total_ovr_bonus,
            total_salary=total_salary - total_salary_bonus,
            total_ap=total_ap - total_ap_bonus,
            active_combos=active_combos,
        )
