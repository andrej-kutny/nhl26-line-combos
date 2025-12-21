import clingo
import pytest
from pathlib import Path

from tests.data.asp_g1a import DEF_AP_C, DEF_SAL_C, DEF_OVR_C, FWD_AP_C, FWD_OVR_C, FWD_SAL_C

class TestASP_G1A:
    def solve(self, files, extra_rules="", consts=None, ctl_opts=None):
        # Resolve paths relative to backend/src/asp/g1a_abstraction
        # Assuming we are running tests from repo root or backend/
        # files list contains strings like "src/asp/g1a_abstraction/rules.lp"
        
        # Strategy: Find where this test file is, go up to backend/src/asp...
        # Current file: backend/tests/test_asp_g1a.py
        # Target: backend/src/asp/g1a_abstraction/...
        
        current_dir = Path(__file__).parent.resolve()
        # Navigate up to 'backend' (parent of tests) then down to src/asp/g1a_abstraction
        # But we don't know if current_dir is backend/tests or just tests/
        # Safe bet: locate 'src' folder relative to 'backend' root.
        
        # If current_dir ends with 'tests', parent is 'backend' (or root if flattened)
        backend_root = current_dir.parent
        asp_root = backend_root / "src" / "asp" / "g1a_abstraction"
        
        resolved_files = []
        for f in files:
            # f is like "src/asp/g1a_abstraction/rules.lp"
            # We just want the filename part if we are constructing path manually
            fname = Path(f).name
            full_path = asp_root / fname
            if not full_path.exists():
                raise FileNotFoundError(f"Could not find ASP file: {full_path}")
            resolved_files.append(str(full_path))

        opts = list(ctl_opts or [])
        if consts:
            for k, v in consts.items():
                opts.append(f"-c {k}={v}")
        
        ctl = clingo.Control(opts)
        for f in resolved_files:
            ctl.load(f)
        
        if extra_rules.strip():
            ctl.add("extra", [], extra_rules)
            ctl.ground([("base", []), ("extra", [])])
        else:
            ctl.ground([("base", [])])

        models, opt = [], None
        models_c = 0
        def on_model(m):
            nonlocal opt, models_c
            models_c += 1
            models.append(m.symbols(shown=True))
            if m.cost:
                opt = tuple(m.cost)
        res = ctl.solve(on_model=on_model)
        return res, models, opt, models_c

    def test_works(self):
        for target in ["src/asp/g1a_abstraction/target_optimise.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"]:
            for pos, datasets in [["def", [DEF_AP_C, DEF_SAL_C, DEF_OVR_C]], ["fwd", [FWD_SAL_C, FWD_AP_C, FWD_OVR_C]]]:
                for dataset in datasets:
                    res, models, cost, models_c = self.solve(
                        ["src/asp/g1a_abstraction/rules.lp", f"src/asp/g1a_abstraction/{pos}_rules.lp", target], 
                        extra_rules=dataset,
                        ctl_opts=["0"]
                    )
                    assert res.satisfiable

    def test_logic_rules(self):
        # ... existing code ...
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
        assert cost[0] == -6

    def test_conflicting_combos(self):
        # ... existing code ...
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
        # ... existing code ...
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
        # ... existing code ...
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

    def test_threshold_lookup(self):
        # ... existing code ...
        rules_lookup = """
        defense_combo(1, 10, "AP", event("A"), event("B")).
        defense_combo(2, 5, "AP", event("C"), event("D")).
        """
        res, models, _, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"],
            extra_rules=rules_lookup,
            consts={"min_reward": 5},
            ctl_opts=["0"]
        )
        assert res.satisfiable
        
        res, models, _, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"],
            extra_rules=rules_lookup,
            consts={"min_reward": 10},
            ctl_opts=["0"]
        )
        assert res.satisfiable

        res, models, _, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"],
            extra_rules=rules_lookup,
            consts={"min_reward": 11},
            ctl_opts=["0"]
        )
        assert not res.satisfiable

        rules_dupes = """
        defense_combo(3, 1, "AP", team("X"), team("X")).
        defense_combo(4, 1, "AP", team("Y"), team("Y")).
        """
        res, models, _, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"],
            extra_rules=rules_dupes,
            consts={"min_reward": 1},
            ctl_opts=["0"]
        )
        assert res.satisfiable
        assert count == 2

    def test_redundant_combo_definitions(self):
        # defense_combo(1, 10, "AP", event("A"), event("B")).
        # defense_combo(2, 5, "AP", event("A"), event("B")).
        # With P1=A, P2=B, both should activate.
        # Total Reward = 15.
        rules = """
        defense_combo(1, 10, "AP", event("A"), event("B")).
        defense_combo(2, 5, "AP", event("A"), event("B")).
        """
        res, models, cost, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"],
            extra_rules=rules,
            consts={"min_reward": 15},
            ctl_opts=["0"]
        )
        assert res.satisfiable
        # Verify both combos are active in the solution
        model_str = str(models[0])
        assert 'def_active_combo(1,10,"AP")' in model_str
        assert 'def_active_combo(2,5,"AP")' in model_str

    def test_no_duplicates_simple_single(self):
        rules = """
        defense_combo(1, 10, "AP", team("OTT"), event("EVENT")).
        """
        res, models, cost, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"],
            extra_rules=rules,
            consts={"min_reward": 1},
            ctl_opts=["0"]
        )
        assert res.satisfiable
        assert count == 1

    def test_no_duplicates_simple_mixed(self):
        rules = """
        defense_combo(1, 10, "AP", team("OTT"), event("EVENT")).
        defense_combo(2, 10, "AP", nationality("SWE"), event("EVENT")).
        """
        res, models, cost, count = self.solve(
            ["src/asp/g1a_abstraction/rules.lp", "src/asp/g1a_abstraction/def_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"],
            extra_rules=rules,
            consts={"min_reward": 1},
            ctl_opts=["0"]
        )
        assert res.satisfiable
        # Expect 3 models: {1}, {2}, and {1, 2} (combined)
        # Previous restrictive logic blocked {1, 2} or one of the singles incorrectly.
        assert count == 3
        
        str_models = "\n".join([str(model) for model in models])
        assert "total_reward(20)" in str_models
        assert "total_reward(10)" in str_models

    def test_no_duplicates_in_all(self):
        # Iterate over all datasets, run threshold lookup, verify no duplicate combo sets.
        for pos, datasets in [["def", [DEF_AP_C, DEF_SAL_C, DEF_OVR_C]], ["fwd", [FWD_SAL_C, FWD_AP_C, FWD_OVR_C]]]:
            for dataset in datasets:
                res, models, _, count = self.solve(
                    ["src/asp/g1a_abstraction/rules.lp", f"src/asp/g1a_abstraction/{pos}_rules.lp", "src/asp/g1a_abstraction/target_threshold_lookup.lp"], 
                    extra_rules=dataset,
                    consts={"min_reward": 5},
                    ctl_opts=["0"]
                )
                if not res.satisfiable:
                    continue
                
                # Extract sets of active combo IDs for each model
                combo_sets = set()
                combo_predicate = f"{pos}_active_combo"
                
                for model in models:
                    active_ids = []
                    for symbol in model:
                        if symbol.name == combo_predicate:
                            # Symbol is function: fwd_active_combo(ID, R, T)
                            # Args[0] is ID.
                            active_ids.append(symbol.arguments[0].number)
                    
                    # Sort tuple to make it hashable and order-independent
                    combo_tuple = tuple(sorted(active_ids))
                    
                    # If this set of combos was already seen, it's a duplicate model!
                    # (Meaning we have multiple models for the EXACT SAME set of active combos)
                    # This implies redundant attribute configurations were not filtered out.
                    assert combo_tuple not in combo_sets, f"Duplicate combo set found: {combo_tuple} in dataset {pos}"
                    combo_sets.add(combo_tuple)
