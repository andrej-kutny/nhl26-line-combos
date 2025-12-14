"""Quick check of how many combos are activatable with current data."""

from src.core.data_loader import get_data_loader


def main() -> None:
    loader = get_data_loader()
    forwards = loader.get_forwards()
    defense = loader.get_defense()
    fwd_combos = loader.get_forward_combos()
    def_combos = loader.get_defense_combos()

    def can_activate(combo, players):
        for cond in combo.get_conditions():
            if not any(p.matches_condition(cond.type, cond.key) for p in players):
                return False
        return True

    activatable_fwd = [c for c in fwd_combos if can_activate(c, forwards)]
    activatable_def = [c for c in def_combos if can_activate(c, defense)]

    print(f"Forward combos: {len(activatable_fwd)}/{len(fwd_combos)} activatable")
    print(f"Defense combos: {len(activatable_def)}/{len(def_combos)} activatable")

    print("\nSample forward combos that activate:")
    for c in activatable_fwd[:10]:
        conds = " + ".join([f"{cc.type}={cc.key}" for cc in c.get_conditions()])
        print(f"  ID {c.id}: {c.reward_type.value} {c.reward_amount} :: {conds}")

    print("\nSample defense combos that activate:")
    for c in activatable_def[:10]:
        conds = " + ".join([f"{cc.type}={cc.key}" for cc in c.get_conditions()])
        print(f"  ID {c.id}: {c.reward_type.value} {c.reward_amount} :: {conds}")


if __name__ == "__main__":
    main()
