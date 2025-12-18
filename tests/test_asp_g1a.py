import clingo

from tests.data.asp_g1a import DEF_AP_C, DEF_SAL_C, DEF_OVR_C, FWD_AP_C, FWD_OVR_C, FWD_SAL_C

class TestASP_G1A:
    def solve(self, files, extra_rules="", consts=None, ctl_opts=None):
        opts = list(ctl_opts or [])
        if consts:
            for k, v in consts.items():
                opts.append(f"-c{k}={v}")
        ctl = clingo.Control(opts)
        for f in files:
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
                    print(f"Testing {pos} {target} dataset: \n{dataset}")
                    res, models, cost, models_c = self.solve(["src/asp/g1a_abstraction/rules.lp", f"src/asp/g1a_abstraction/{pos}_rules.lp", target], extra_rules=dataset)
                    assert res.satisfiable
                    print(f"Models: {models_c}")
                    print(f"Cost: {cost}")