"""
Quick check of how many combos are activatable with current data.

Notes
-----
- This is a *data sanity check*, not an optimization run.
- "Activatable" here means: there exists at least one concrete line/pair (with
  distinct cards) that can satisfy the combo's conditions.
  We approximate this via Hall-style union checks (same logic as in the ASP rules),
  which avoids brute-forcing all player combinations.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running this script via `python nhl26-line-combos/scripts/check_combo_activation.py`
# (or from inside the repo as `python scripts/check_combo_activation.py`) without having to
# manually set PYTHONPATH.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.data_loader import DataLoader, get_data_loader


def main() -> None:
    # Default: use the loader's auto-detection. If you want to force the original
    # CSV dataset (instead of a local nhlhutbuilder snapshot), run:
    #   USE_HUTBUILDER_API=0 python scripts/check_combo_activation.py
    use_hutbuilder_env = os.getenv("USE_HUTBUILDER_API")
    if use_hutbuilder_env is None:
        loader = get_data_loader()
    else:
        loader = DataLoader(use_hutbuilder_api=use_hutbuilder_env.strip() not in {"0", "false", "no"})

    forwards = loader.get_forwards()
    defense = loader.get_defense()
    fwd_combos = loader.get_forward_combos()
    def_combos = loader.get_defense_combos()

    def _conds_str(combo) -> str:
        return " + ".join([f"{cc.type}={cc.key}" for cc in combo.get_conditions()])

    def can_activate_fwd(combo, players):
        conds = combo.get_conditions()
        if len(conds) != 3:
            return False, "expected 3 conditions"

        sets = []
        for cond in conds:
            s = {p.id for p in players if p.matches_condition(cond.type, cond.key)}
            sets.append(s)
        missing = [i + 1 for i, s in enumerate(sets) if not s]
        if missing:
            return False, f"no matching players for condition slot(s) {missing}"

        s1, s2, s3 = sets
        if len(s1 | s2) < 2:
            return False, "Hall violation: |C1∪C2| < 2"
        if len(s1 | s3) < 2:
            return False, "Hall violation: |C1∪C3| < 2"
        if len(s2 | s3) < 2:
            return False, "Hall violation: |C2∪C3| < 2"
        if len(s1 | s2 | s3) < 3:
            return False, "Hall violation: |C1∪C2∪C3| < 3"
        return True, "ok"

    def can_activate_def(combo, players):
        conds = combo.get_conditions()
        if len(conds) != 2:
            return False, "expected 2 conditions"

        sets = []
        for cond in conds:
            s = {p.id for p in players if p.matches_condition(cond.type, cond.key)}
            sets.append(s)
        missing = [i + 1 for i, s in enumerate(sets) if not s]
        if missing:
            return False, f"no matching players for condition slot(s) {missing}"

        if len(sets[0] | sets[1]) < 2:
            return False, "Hall violation: |C1∪C2| < 2"
        return True, "ok"

    activatable_fwd = []
    failed_fwd: list[tuple[int, str, str]] = []
    for c in fwd_combos:
        ok, reason = can_activate_fwd(c, forwards)
        if ok:
            activatable_fwd.append(c)
        else:
            failed_fwd.append((c.id, c.reward_type.value, f"{_conds_str(c)} ({reason})"))

    activatable_def = []
    failed_def: list[tuple[int, str, str]] = []
    for c in def_combos:
        ok, reason = can_activate_def(c, defense)
        if ok:
            activatable_def.append(c)
        else:
            failed_def.append((c.id, c.reward_type.value, f"{_conds_str(c)} ({reason})"))

    print(f"Forward combos: {len(activatable_fwd)}/{len(fwd_combos)} activatable")
    print(f"Defense combos: {len(activatable_def)}/{len(def_combos)} activatable")

    print("\nSample forward combos that activate:")
    for c in activatable_fwd[:10]:
        print(f"  ID {c.id}: {c.reward_type.value} {c.reward_amount} :: {_conds_str(c)}")

    print("\nSample defense combos that activate:")
    for c in activatable_def[:10]:
        print(f"  ID {c.id}: {c.reward_type.value} {c.reward_amount} :: {_conds_str(c)}")

    if failed_fwd:
        print("\nForward combos that do NOT activate (first 15):")
        for cid, rtype, info in failed_fwd[:15]:
            print(f"  ID {cid}: {rtype} :: {info}")
    if failed_def:
        print("\nDefense combos that do NOT activate (first 15):")
        for cid, rtype, info in failed_def[:15]:
            print(f"  ID {cid}: {rtype} :: {info}")


if __name__ == "__main__":
    main()
