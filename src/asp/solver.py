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
        max_candidates_total: int = 350,
        max_candidates_global: int = 200,
        max_candidates_per_condition: int = 25,
        max_fullteam_forwards: int = 24,
        max_fullteam_defense: int = 14,
        max_fullteam_goalies: int = 4,
    ) -> None:
        self.loader = get_data_loader()
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
        forwards = self._select_candidates(forwards, combos)

        program = "\n".join(
            [
                self._generate_facts(
                    players=forwards,
                    combos=combos,
                    constraints=constraints,
                    is_forward=True,
                ),
                self._read_rules("base.lp"),
                self._read_rules("forward_line.lp"),
            ]
        )

        models = self._solve(program, num_solutions=num_solutions)
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
        defense = self._select_candidates(defense, combos)

        program = "\n".join(
            [
                self._generate_facts(
                    players=defense,
                    combos=combos,
                    constraints=constraints,
                    is_forward=False,
                ),
                self._read_rules("base.lp"),
                self._read_rules("defense_pair.lp"),
            ]
        )

        models = self._solve(program, num_solutions=num_solutions)
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

        forwards = self._select_candidates(forwards, fwd_combos)
        defense = self._select_candidates(defense, def_combos)
        goalies = goalies[:10]  # cap goalies to reduce search space

        forwards.sort(key=lambda p: p.overall, reverse=True)
        defense.sort(key=lambda p: p.overall, reverse=True)
        goalies.sort(key=lambda p: p.overall, reverse=True)

        forwards = forwards[: self.max_fullteam_forwards]
        defense = defense[: self.max_fullteam_defense]
        goalies = goalies[: self.max_fullteam_goalies]

        program = "\n".join(
            [
                self._generate_full_team_facts(
                    forwards=forwards,
                    defense=defense,
                    goalies=goalies,
                    fwd_combos=fwd_combos,
                    def_combos=def_combos,
                    constraints=constraints,
                ),
                self._read_rules("base.lp"),
                self._read_rules("full_team.lp"),
            ]
        )

        models = self._solve(program, num_solutions=num_solutions)
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

    def _select_candidates(self, players: list, combos: list) -> list:
        """
        Reduce search space by selecting a candidate subset.

        Strategy:
        - Include top N players by OVR globally
        - Include top K players per combo condition (team/nationality/event)
        - Cap total candidates to max_candidates_total by OVR
        """
        if len(players) <= self.max_candidates_total:
            return players

        players_sorted = sorted(players, key=lambda p: p.overall, reverse=True)
        selected_ids: set[str] = set()

        for p in players_sorted[: self.max_candidates_global]:
            selected_ids.add(str(p.id))

        for combo in combos:
            for cond in combo.get_conditions():
                matching = [p for p in players if p.matches_condition(cond.type, cond.key)]
                matching.sort(key=lambda p: p.overall, reverse=True)
                for p in matching[: self.max_candidates_per_condition]:
                    selected_ids.add(str(p.id))

        selected = [p for p in players_sorted if str(p.id) in selected_ids]
        if len(selected) > self.max_candidates_total:
            selected = selected[: self.max_candidates_total]
        return selected

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

    def _generate_facts(
        self,
        *,
        players: list,
        combos: list,
        constraints: OptimizationConstraints,
        is_forward: bool,
    ) -> str:
        lines: list[str] = []

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
            if p.sub_position:
                lines.append(f"sub_pos({self._clingo_str(str(p.id))}, {self._clingo_str(p.sub_position.lower())}).")
            if p.salary is not None:
                lines.append(f"salary({self._clingo_str(str(p.id))}, {int(p.salary)}).")
            if p.ability_points is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(p.ability_points)}).")

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
    ) -> str:
        lines: list[str] = []

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
            if p.sub_position:
                lines.append(f"sub_pos({self._clingo_str(str(p.id))}, {self._clingo_str(p.sub_position.lower())}).")
            if p.salary is not None:
                lines.append(f"salary({self._clingo_str(str(p.id))}, {int(p.salary)}).")
            if p.ability_points is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(p.ability_points)}).")

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
            if p.ability_points is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(p.ability_points)}).")

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
            if p.ability_points is not None:
                lines.append(f"ap({self._clingo_str(str(p.id))}, {int(p.ability_points)}).")

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

    def _solve(self, program: str, *, num_solutions: int) -> list[list]:
        if not self.is_available():
            raise RuntimeError(
                "Clingo is not available. Install dependencies from "
                "`nhl26-line-combos-main/requirements.txt` in a Python version "
                "supported by `clingo`."
            )

        import clingo  # type: ignore

        ctl = clingo.Control(
            [
                "--warn=none",
                "--opt-mode=optN",
                "--models",
                str(num_solutions),
            ]
        )
        ctl.add("base", [], program)
        ctl.ground([("base", [])])

        models: list[list] = []
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                models.append(model.symbols(shown=True))
                if len(models) >= num_solutions:
                    break
        return models

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
                    selected_by_slot[slot] = Player(
                        id=str(p.id),
                        player_id=p.player_id,
                        first_name=p.first_name,
                        last_name=p.last_name,
                        event=p.event,
                        overall=p.overall,
                        nationality=p.nationality,
                        league=p.league,
                        team=p.team,
                        position=position,
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
                        event=p.event,
                        overall=p.overall,
                        nationality=p.nationality,
                        league=p.league,
                        team=p.team,
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
