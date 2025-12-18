import clingo
import pytest

from tests.data.asp_g1a import DEF_AP_C, DEF_SAL_C, DEF_OVR_C, FWD_AP_C, FWD_OVR_C, FWD_SAL_C

class TestASP_G1A:
    def solve(self, files, extra_rules="", consts=None, ctl_opts=None):
        opts = list(ctl_opts or [])
        if consts:
            for k, v in consts.items():
                opts.append(f"-c {k}={v}")
        
        ctl = clingo.Control(opts)
        for f in files:
            ctl.load(f)
        
        if extra_rules.strip():
            ctl.add("extra", [], extra_rules)
            ctl.ground([("base", []), ("extra", [])])
        else:
            ctl.ground([("base", [])])

        models = []
        opt_cost = None
        
        def on_model(m):
            nonlocal opt_cost
            symbols = m.symbols(shown=True)
            
            if m.cost:
                current_cost = tuple(m.cost)
                if opt_cost is None or current_cost < opt_cost:
                    # New better solution found (clingo minimizes cost vector)
                    opt_cost = current_cost
                    models.clear()
                    models.append(symbols)
                elif current_cost == opt_cost:
                    # Same optimal cost
                    models.append(symbols)
            else:
                models.append(symbols)
                
        res = ctl.solve(on_model=on_model)
        # For non-optimizing runs (e.g. threshold lookup), all models are valid solutions.
        # For optimizing runs, 'models' contains only the optimal ones.
        return res, models, opt_cost, len(models)

    def test_works(self):
        for target in ["src/asp/g1a_abstraction/target_optimise.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"]:
            for pos, datasets in [["def", [DEF_AP_C, DEF_SAL_C, DEF_OVR_C]], ["fwd", [FWD_SAL_C, FWD_AP_C, FWD_OVR_C]]]:
                for dataset in datasets:
                    # print(f"Testing {pos} {target} dataset: \n{dataset}")
                    res, models, cost, models_c = self.solve(
                        ["src/asp/g1a_abstraction/rules.lp", f"src/asp/g1a_abstraction/{pos}_rules.lp", target], 
                        extra_rules=dataset,
                        ctl_opts=["0"]
                    )
                    assert res.satisfiable
                    # print(f"Models: {models_c}")
                    # print(f"Cost: {cost}")

    def test_logic_rules(self):
        # 1. Simple list of combos - check total reward accumulation
        # C1: P1=SWE, P2=FIN (1 AP)
        # C2: P1=HV71, P2=HEJ (2 AP)
        # C3: P1=HV71, P2=HEJ (3 AP)
        # P1 needs: SWE, HV71. P2 needs: FIN, HEJ. (Compatible)
        # Total Reward = 1+2+3 = 6.
        rules_simple = """
        defense_combo(1, 1, "AP", nationality("SWE"), nationality("FIN")).
        defense_combo(2, 2, "AP", team("HV71"), event("HEJ")).
        defense_combo(3, 3, "AP", team("HV71"), event("HEJ")).
        """
        res, models, cost, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_optimise.lp"],
            extra_rules=rules_simple,
            ctl_opts=["0"]
        )
        assert res.satisfiable
        # Cost is [-Reward, Attributes]. We want Reward=6.
        # cost[0] should be -6.
        assert cost[0] == -6

    def test_conflicting_combos(self):
        # 2. Conflicting combos - only 1 can activate
        # Each combo requires 2 Events. 
        # Since we have 2 players, max total events = 2.
        # C1 requires (Event A, Event B). Consumes all slots.
        # C2 requires (Event C, Event D). Consumes all slots.
        # Cannot activate both.
        rules_conflict = """
        defense_combo(1, 10, "AP", event("A"), event("B")).
        defense_combo(2, 10, "AP", event("C"), event("D")).
        """
        res, models, cost, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_optimise.lp"],
            extra_rules=rules_conflict,
            ctl_opts=["0"]
        )
        assert res.satisfiable
        assert cost[0] == -10

    def test_weights_and_preference(self):
        # 3. Weights and Preferences
        # C1, C2, C3 require (Event A, Event B). Reward 1 each. Total 3.
        # C4 requires (Event C, Event D). Reward 5.
        # Conflict: Total capacity 2 events. Can't do both sets.
        rules_pref = """
        defense_combo(1, 1, "AP", event("A"), event("B")).
        defense_combo(2, 1, "AP", event("A"), event("B")).
        defense_combo(3, 1, "AP", event("A"), event("B")).
        defense_combo(4, 5, "AP", event("C"), event("D")).
        """
        res, models, cost, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_optimise.lp"],
            extra_rules=rules_pref,
            ctl_opts=["0"]
        )
        assert res.satisfiable
        assert cost[0] == -5

    def test_multiplier_logic(self):
        rules_mult = """
        defense_combo(1, 5, "OVR", event("A"), event("B")).
        defense_combo(2, 1, "SAL", event("C"), event("D")).
        """
        
        res, _, cost, _ = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_optimise.lp"],
            extra_rules=rules_mult,
            ctl_opts=["0"]
        )
        assert cost[0] == -5

        res, _, cost, _ = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_optimise.lp"],
            extra_rules=rules_mult,
            consts={"w_sal": 10},
            ctl_opts=["0"]
        )
        assert cost[0] == -10

        res, _, cost, _ = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_optimise.lp"],
            extra_rules=rules_mult,
            consts={"w_ovr": 10},
            ctl_opts=["0"]
        )
        assert cost[0] == -50
