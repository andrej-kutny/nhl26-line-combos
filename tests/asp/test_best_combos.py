import clingo
import pytest

import os

def solve(files, extra_rules: str = "", consts=None, ctl_opts=None):
    # Determine base path relative to this test file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    
    abs_files = []
    for f in files:
        if not os.path.isabs(f):
            abs_files.append(os.path.join(root_dir, f))
        else:
            abs_files.append(f)

    opts = list(ctl_opts or [])
    if consts:
        for k, v in consts.items():
            opts.append(f"-c{k}={v}")
    ctl = clingo.Control(opts)
    for f in abs_files:
        ctl.load(f)
    if extra_rules.strip():
        ctl.add("extra", [], extra_rules)
        ctl.ground([("base", []), ("extra", [])])
    else:
        ctl.ground([("base", [])])
    models = []
    def on_model(m: clingo.Model):
        models.append(m.symbols(shown=True))
    res = ctl.solve(on_model=on_model)
    return res, models

def shown(models, name):
    return [s for s in models[-1] if s.name == name]

def sym_to_str(sym: clingo.Symbol) -> str:
    # your facts use strings like "K000001"; model will contain those as clingo.String
    return str(sym)

def test_fwd_best_combo_unlimited_salary_cap():
    extra = r'''
        player("K000001", "P000001", "ROU", "ABC", "BASE", 90, 100).
        player("K000003", "P000002", "HUN", "ABC", "ICON", 88, 80).
        player("K000004", "P000003", "MDA", "GHI", "SPOT", 87, 70).
        player("K000005", "P000004", "MDA", "SJS", "BASE", 86, 65).
        forward_combo(19, 1, "OVR", event("SPOT"), team("SJS"), event("ICON")).

        #show fwd_best_combination/3.'''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/fwd_main.lp", "backend/src/asp/g2/fwd_best_combo.lp",
         "backend/src/asp/g2/fwd_sal_description.lp", "backend/src/asp/g2/fwd_ovr_description.lp",
         "backend/src/asp/g2/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 9999, "w_ovr": 3, "w_ap": 0, "w_sal": 0},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable

    got = {
        tuple(map(sym_to_str, s.arguments))
        for s in shown(models, "fwd_best_combination")
    }
    expected = {
        ('"K000003"','"K000004"','"K000005"',),
        ('"K000001"','"K000003"','"K000004"',),
        ('"K000001"','"K000004"','"K000005"',),
        ('"K000001"','"K000003"','"K000005"',),
    }
    assert got == expected

def test_def_best_combo_unlimited_salary_cap():
    extra = r'''
        player("K000001", "P000001", "ROU", "ABC", "BASE", 90, 100).
        player("K000003", "P000002", "CZECHIA", "ABC", "ICON", 88, 80).
        player("K000004", "P000003", "MDA", "GHI", "NG", 87, 70).
        player("K000005", "P000004", "MDA", "SJS", "BASE", 86, 65).
        defense_combo(12, 1, "OVR", event("NG"), nationality("CZECHIA")).

        #show def_best_combination/2.'''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/def_main.lp", "backend/src/asp/g2/def_best_combo.lp",
         "backend/src/asp/g2/def_sal_description.lp", "backend/src/asp/g2/def_ovr_description.lp",
         "backend/src/asp/g2/def_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 9999, "w_ovr": 3, "w_ap": 0, "w_sal": 0},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable

    got = {
        tuple(map(sym_to_str, s.arguments))
        for s in shown(models, "def_best_combination")
    }
    expected = {
        ('"K000003"','"K000004"'),
        ('"K000001"','"K000003"'),
        ('"K000001"','"K000004"'),
        ('"K000001"','"K000005"'),
        ('"K000003"','"K000005"'),
        ('"K000004"','"K000005"'),
    }
    assert got == expected
