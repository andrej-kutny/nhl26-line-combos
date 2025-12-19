from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations
from typing import Iterable, Sequence

from ..core.data import get_data_loader
from ..core.models import (
    ActiveCombo,
    LineSolution,
    OptimizationConstraints,
    OptimizationTarget,
    Player,
    Position,
    RewardType,
)


def _combo_description(conditions: Sequence) -> str:
    parts: list[str] = []
    for cond in conditions:
        parts.append(f"{str(cond.type).upper()}={str(cond.key).upper()}")
    return " + ".join(parts)


def combo_activates(players: Sequence, combo) -> bool:
    """
    Order-independent combo activation: returns True iff there exists a bijection
    between combo conditions and players such that all conditions are satisfied.
    """
    conditions = combo.get_conditions()
    if len(players) != len(conditions):
        return False

    for perm in permutations(players, len(players)):
        if all(p.matches_condition(c.type, c.key) for p, c in zip(perm, conditions, strict=True)):
            return True
    return False


@dataclass(frozen=True)
class _ScoredLine:
    solution: LineSolution
    score_key: tuple


class Goal2BruteForceSolver:
    """
    Simple Goal 2 solver (interactive suggestions) that brute-forces combinations
    over a capped candidate pool and scores them. This avoids blocking demo work
    on a full ASP implementation.
    """

    def __init__(self, *, data_dir: str = "data/") -> None:
        self.loader = get_data_loader(data_dir)
        self.last_candidates_evaluated = 0
        self.last_combinations_evaluated = 0

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

        forwards = _dedupe_best_card_per_player(forwards)
        forwards = _cap_candidates(forwards, target=target, limit=60)

        scored = _score_lines(
            position=Position.FORWARD,
            candidates=forwards,
            combos=combos,
            constraints=constraints,
            target=target,
            k=num_solutions,
        )
        self.last_candidates_evaluated = len(forwards)
        self.last_combinations_evaluated = _n_choose_k(len(forwards), 3)
        return [s.solution for s in scored]

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
        defense = _dedupe_best_card_per_player(defense)
        defense = _cap_candidates(defense, target=target, limit=90)

        scored = _score_lines(
            position=Position.DEFENSE,
            candidates=defense,
            combos=combos,
            constraints=constraints,
            target=target,
            k=num_solutions,
        )
        self.last_candidates_evaluated = len(defense)
        self.last_combinations_evaluated = _n_choose_k(len(defense), 2)
        return [s.solution for s in scored]

    def optimize_full_team(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        raise NotImplementedError("Full-team optimization is not implemented in the brute-force demo solver.")

    def validate_line(self, player_ids: list[int], position_type: str) -> dict:
        position_type = position_type.lower().strip()
        if position_type == "forward":
            candidates = self.loader.get_forwards()
            combos = self.loader.get_forward_combos()
            expected_count = 3
        elif position_type == "defense":
            candidates = self.loader.get_defense()
            combos = self.loader.get_defense_combos()
            expected_count = 2
        else:
            return {"valid": False, "error": "position_type must be 'forward' or 'defense'"}

        if len(player_ids) != expected_count:
            return {"valid": False, "error": f"Expected {expected_count} players, got {len(player_ids)}"}

        # Allow lookup by either card id or player_id; prefer best overall card.
        player_map: dict[str, object] = {}
        for p in candidates:
            keys = [str(getattr(p, "id"))]
            pid = getattr(p, "player_id", None)
            if pid is not None:
                keys.append(str(pid))
            for key in keys:
                existing = player_map.get(key)
                if existing is None or int(getattr(p, "overall", 0)) > int(getattr(existing, "overall", 0)):
                    player_map[key] = p

        selected: list[object] = []
        for pid in player_ids:
            key = str(pid)
            if key not in player_map:
                return {"valid": False, "error": f"Player ID not found: {pid}"}
            selected.append(player_map[key])

        active: list[dict] = []
        ovr_bonus = 0
        sal_bonus = 0
        ap_bonus = 0
        for combo in combos:
            if not combo_activates(selected, combo):
                continue
            active.append(
                {
                    "id": int(combo.id),
                    "reward_type": combo.reward_type.value,
                    "reward_amount": int(combo.reward_amount),
                    "description": _combo_description(combo.get_conditions()),
                }
            )
            if combo.reward_type == RewardType.OVR:
                ovr_bonus += int(combo.reward_amount)
            elif combo.reward_type == RewardType.SAL:
                sal_bonus += int(combo.reward_amount)
            elif combo.reward_type == RewardType.AP:
                ap_bonus += int(combo.reward_amount)

        total_ovr = sum(int(getattr(p, "overall", 0)) for p in selected)
        base_salary = sum(float(getattr(p, "salary", 0.0)) for p in selected)
        base_ap = 0

        return {
            "valid": True,
            "players": [
                {
                    "id": int(getattr(p, "id")),
                    "player_id": int(getattr(p, "player_id", getattr(p, "id"))),
                    "name": f"{getattr(p, 'first_name', '')} {getattr(p, 'last_name', '')}".strip(),
                    "overall": int(getattr(p, "overall", 0)),
                    "team": str(getattr(p, "team", "")),
                    "nationality": str(getattr(p, "nationality", "")),
                    "event": str(getattr(p, "event", "")),
                    "salary": float(getattr(p, "salary", 0.0)),
                    "position": str(getattr(p, "position", "")),
                }
                for p in selected
            ],
            "total_base_ovr": total_ovr,
            "ovr_bonus": ovr_bonus,
            "effective_ovr": total_ovr + ovr_bonus,
            "base_salary": base_salary,
            "salary_bonus": sal_bonus,
            "salary_eff": base_salary - sal_bonus,
            "base_ap": base_ap,
            "ap_bonus": ap_bonus,
            "ap_eff": base_ap - ap_bonus,
            "active_combos": active,
        }


def _dedupe_best_card_per_player(players: Iterable) -> list:
    best_by_player: dict[int, object] = {}
    for p in players:
        pid = int(getattr(p, "player_id", getattr(p, "id")))
        existing = best_by_player.get(pid)
        if existing is None or int(getattr(p, "overall", 0)) > int(getattr(existing, "overall", 0)):
            best_by_player[pid] = p
    return list(best_by_player.values())


def _cap_candidates(players: list, *, target: OptimizationTarget, limit: int) -> list:
    if not players:
        return []
    if target == OptimizationTarget.SALARY:
        players.sort(key=lambda p: (float(getattr(p, "salary", 0.0)), -int(getattr(p, "overall", 0))))
    else:
        players.sort(key=lambda p: (-int(getattr(p, "overall", 0)), float(getattr(p, "salary", 0.0))))
    return players[:limit]

def _n_choose_k(n: int, k: int) -> int:
    if k < 0 or n < 0 or k > n:
        return 0
    if k == 0:
        return 1
    if k == 1:
        return n
    if k == 2:
        return (n * (n - 1)) // 2
    if k == 3:
        return (n * (n - 1) * (n - 2)) // 6
    # Not needed for this module.
    raise ValueError("Unsupported k")


def _score_key_for_target(
    *,
    target: OptimizationTarget,
    effective_ovr: int,
    salary_eff: float,
    ap_eff: int,
) -> tuple:
    if target == OptimizationTarget.OVR:
        return (-effective_ovr, salary_eff, ap_eff)
    if target == OptimizationTarget.SALARY:
        return (salary_eff, -effective_ovr, ap_eff)
    if target == OptimizationTarget.AP:
        return (ap_eff, -effective_ovr, salary_eff)
    # balanced
    return (-effective_ovr, salary_eff, ap_eff)


def _score_lines(
    *,
    position: Position,
    candidates: list,
    combos: list,
    constraints: OptimizationConstraints,
    target: OptimizationTarget,
    k: int,
) -> list[_ScoredLine]:
    n = 3 if position == Position.FORWARD else 2
    out: list[_ScoredLine] = []

    for idx, combo_players in enumerate(combinations(candidates, n), start=1):
        # Ensure no duplicate player_id inside the line
        pids = [int(getattr(p, "player_id", getattr(p, "id"))) for p in combo_players]
        if len(set(pids)) != len(pids):
            continue

        if position == Position.FORWARD and constraints.require_center:
            if not any(str(getattr(p, "position", "")).upper() == "C" for p in combo_players):
                continue

        active: list[ActiveCombo] = []
        ovr_bonus = 0
        sal_bonus = 0
        ap_bonus = 0

        for combo in combos:
            if not combo_activates(combo_players, combo):
                continue
            desc = _combo_description(combo.get_conditions())
            active.append(
                ActiveCombo(
                    id=int(combo.id),
                    reward_type=combo.reward_type,
                    reward_amount=int(combo.reward_amount),
                    description=desc,
                )
            )
            if combo.reward_type == RewardType.OVR:
                ovr_bonus += int(combo.reward_amount)
            elif combo.reward_type == RewardType.SAL:
                sal_bonus += int(combo.reward_amount)
            elif combo.reward_type == RewardType.AP:
                ap_bonus += int(combo.reward_amount)

        total_base_ovr = sum(int(getattr(p, "overall", 0)) for p in combo_players)
        base_salary = sum(float(getattr(p, "salary", 0.0)) for p in combo_players)
        base_ap = 0

        salary_eff = base_salary - sal_bonus
        ap_eff = base_ap - ap_bonus
        effective_ovr = total_base_ovr + ovr_bonus

        if constraints.max_salary is not None and salary_eff > float(constraints.max_salary):
            continue
        if constraints.max_ap is not None and ap_eff > int(constraints.max_ap):
            continue

        solution_players = [
            Player(
                id=int(p.id),
                player_id=int(p.player_id),
                first_name=getattr(p, "first_name", ""),
                last_name=getattr(p, "last_name", ""),
                img=str(getattr(p, "img", "")),
                event=str(getattr(p, "event", "")),
                nationality=str(getattr(p, "nationality", "")),
                league=str(getattr(p, "league", "")),
                team=str(getattr(p, "team", "")),
                weight=float(getattr(p, "weight", 0.0)),
                height=int(getattr(p, "height", 0)),
                salary=float(getattr(p, "salary", 0.0)),
                overall=int(getattr(p, "overall", 0)),
                position=str(getattr(p, "position", position.value)),
            )
            for p in combo_players
        ]

        sol = LineSolution(
            rank=0,  # filled after sorting
            players=solution_players,
            total_base_ovr=total_base_ovr,
            ovr_bonus=ovr_bonus,
            effective_ovr=effective_ovr,
            total_salary=salary_eff,
            total_ap=ap_eff,
            active_combos=active,
        )
        score_key = _score_key_for_target(
            target=target,
            effective_ovr=effective_ovr,
            salary_eff=salary_eff,
            ap_eff=ap_eff,
        )
        out.append(_ScoredLine(solution=sol, score_key=score_key))

    out.sort(key=lambda s: s.score_key)
    out = out[:k]
    for i, s in enumerate(out, start=1):
        s.solution.rank = i
    return out
