import clingo
import pytest

def solve(files, extra_rules: str = "", consts=None, ctl_opts=None):
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
        event("SPOT"; "ICON"; "BASE").
        club("SJS"; "ABC"; "GHI").

        id("P000001").
        type("P000001", "player").
        nationality("P000001","ROU").
        id("K000001").
        type("K000001","card").
        has_card("P000001","K000001").
        position("K000001", "C").
        ovr("K000001", 90).
        salary("K000001", 100).
        team("K000001","ABC").
        card_type("K000001","BASE").

        id("P000002").
        type("P000002", "player").
        nationality("P000002","HUN").
        id("K000003").
        type("K000003","card").
        has_card("P000002","K000003").
        position("K000003", "RW").
        ovr("K000003", 88).
        salary("K000003", 80).
        team("K000003","ABC").
        card_type("K000003","ICON").

        id("P000003").
        type("P000003", "player").
        nationality("P000003","MDA").
        id("K000004").
        type("K000004","card").
        has_card("P000003","K000004").
        position("K000004","LW").
        ovr("K000004", 87).
        salary("K000004", 70).
        team("K000004","GHI").
        card_type("K000004","SPOT").

        id("P000004").
        type("P000004", "player").
        nationality("P000004","MDA").
        id("K000005").
        type("K000005","card").
        has_card("P000004","K000005").
        position("K000005","LW").
        ovr("K000005", 86).
        salary("K000005", 65).
        team("K000005","SJS").
        card_type("K000005","BASE").

        forward_combo(19, 1, "OVR", event("SPOT"), club("SJS"), event("ICON")).

        #show fwd_best_combination/3.'''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_best_combo.lp",
         "./src/asp/fwd_sal_description.lp", "./src/asp/fwd_ovr_description.lp",
         "./src/asp/fwd_ap_description.lp"],
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
        ('"K000001"','"K000004"','"K000005"',),\
        ('"K000001"','"K000003"','"K000005"',),
    }
    assert got == expected

def test_def_best_combo_unlimited_salary_cap():
    extra = r'''
        event("SPOT"; "ICON"; "BASE";"NG").
        club("SJS"; "ABC"; "GHI").
        country("ROU"; "HUN"; "MDA"; "CZECHIA").

        id("P000001").
        type("P000001", "player").
        nationality("P000001","ROU").
        id("K000001").
        type("K000001","card").
        has_card("P000001","K000001").
        position("K000001", "RD").
        ovr("K000001", 90).
        salary("K000001", 100).
        team("K000001","ABC").
        card_type("K000001","BASE").

        id("P000002").
        type("P000002", "player").
        nationality("P000002","CZECHIA").
        id("K000003").
        type("K000003","card").
        has_card("P000002","K000003").
        position("K000003", "LD").
        ovr("K000003", 88).
        salary("K000003", 80).
        team("K000003","ABC").
        card_type("K000003","ICON").

        id("P000003").
        type("P000003", "player").
        nationality("P000003","MDA").
        id("K000004").
        type("K000004","card").
        has_card("P000003","K000004").
        position("K000004","RD").
        ovr("K000004", 87).
        salary("K000004", 70).
        team("K000004","GHI").
        card_type("K000004","NG").

        id("P000004").
        type("P000004", "player").
        nationality("P000004","MDA").
        id("K000005").
        type("K000005","card").
        has_card("P000004","K000005").
        position("K000005","LD").
        ovr("K000005", 86).
        salary("K000005", 65).
        team("K000005","SJS").
        card_type("K000005","BASE").

        defense_combo(12, 1, "OVR", event("NG"), country("CZECHIA")).

        #show def_best_combination/2.'''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/def_best_combo.lp",
         "./src/asp/def_sal_description.lp", "./src/asp/def_ovr_description.lp",
         "./src/asp/def_ap_description.lp"],
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