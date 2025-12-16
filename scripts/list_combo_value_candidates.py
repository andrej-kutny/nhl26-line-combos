"""
List SAL/AP combo candidates with cheapest matching players.

For each forward (3-slot) or defense (2-slot) combo that rewards SAL or AP,
pick the cheapest distinct players that satisfy the conditions and report:
- total salary
- net gain (SAL bonus minus total salary) for SAL combos
- the chosen players
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Allow running this script directly without requiring manual PYTHONPATH tweaks.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.data_loader import get_data_loader
from src.core.models import ComboCondition, ForwardLineCombo, DefenseLineCombo


@dataclass
class ComboCandidate:
    kind: str  # FWD/DEF
    combo_id: int
    reward_type: str
    reward_amount: int
    total_salary: float
    net_gain: Optional[float]
    players: list
    description: str


def cheapest_forwards(players, combo: ForwardLineCombo) -> Optional[ComboCandidate]:
    conds = combo.get_conditions()
    # Filter out players without salary
    candidates = [p for p in players if p.salary is not None]
    # Greedy search over sorted candidates for each slot
    matches = []
    used_ids = set()
    for cond in conds:
        opts = [p for p in candidates if p.matches_condition(cond.type, cond.key) and p.id not in used_ids]
        if not opts:
            return None
        opts.sort(key=lambda p: p.salary)
        pick = opts[0]
        matches.append(pick)
        used_ids.add(pick.id)
    total_salary = float(sum(p.salary for p in matches if p.salary is not None))
    net = None
    if combo.reward_type.value == "SAL":
        net = combo.reward_amount - total_salary
    desc = " + ".join([f"{c.type}={c.key}" for c in conds])
    return ComboCandidate(
        kind="FWD",
        combo_id=combo.id,
        reward_type=combo.reward_type.value,
        reward_amount=combo.reward_amount,
        total_salary=total_salary,
        net_gain=net,
        players=matches,
        description=desc,
    )


def cheapest_defense(players, combo: DefenseLineCombo) -> Optional[ComboCandidate]:
    conds = combo.get_conditions()
    candidates = [p for p in players if p.salary is not None]
    matches = []
    used_ids = set()
    for cond in conds:
        opts = [p for p in candidates if p.matches_condition(cond.type, cond.key) and p.id not in used_ids]
        if not opts:
            return None
        opts.sort(key=lambda p: p.salary)
        pick = opts[0]
        matches.append(pick)
        used_ids.add(pick.id)
    total_salary = float(sum(p.salary for p in matches if p.salary is not None))
    net = None
    if combo.reward_type.value == "SAL":
        net = combo.reward_amount - total_salary
    desc = " + ".join([f"{c.type}={c.key}" for c in conds])
    return ComboCandidate(
        kind="DEF",
        combo_id=combo.id,
        reward_type=combo.reward_type.value,
        reward_amount=combo.reward_amount,
        total_salary=total_salary,
        net_gain=net,
        players=matches,
        description=desc,
    )


def main() -> None:
    loader = get_data_loader()
    forwards = loader.get_forwards()
    defense = loader.get_defense()
    fwd_combos = loader.get_forward_combos()
    def_combos = loader.get_defense_combos()

    results: List[ComboCandidate] = []

    for c in fwd_combos:
        if c.reward_type.value not in ("SAL", "AP"):
            continue
        cand = cheapest_forwards(forwards, c)
        if cand:
            results.append(cand)

    for c in def_combos:
        if c.reward_type.value not in ("SAL", "AP"):
            continue
        cand = cheapest_defense(defense, c)
        if cand:
            results.append(cand)

    sal_sorted = sorted([r for r in results if r.reward_type == "SAL"], key=lambda r: (r.net_gain or -1e9), reverse=True)
    ap_sorted = sorted([r for r in results if r.reward_type == "AP"], key=lambda r: r.reward_amount, reverse=True)

    print("=== SAL combos (sorted by net gain = bonus - salary) ===")
    for r in sal_sorted[:20]:
        print(f"{r.kind} combo {r.combo_id}: bonus {r.reward_amount} SAL, salary {r.total_salary:.1f}, net {r.net_gain:.1f} :: {r.description}")

    print("\n=== AP combos (sorted by AP bonus) ===")
    for r in ap_sorted[:20]:
        print(f"{r.kind} combo {r.combo_id}: bonus {r.reward_amount} AP, salary {r.total_salary:.1f} :: {r.description}")


if __name__ == "__main__":
    main()
