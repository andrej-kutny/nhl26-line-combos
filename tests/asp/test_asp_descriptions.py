# test_solver.py
import clingo

extra = r"""
id("P000010"). id("P000011"). id("P000012"). id("P000013"). id("P000014"). id("P000015").
type("P000010","player"). type("P000011","player"). type("P000012","player"). type("P000013","player"). type("P000014","player"). type("P000015","player").
id("K000012"). id("K000013"). id("K000014"). id("K000015"). id("K000016"). id("K000017").
type("K000012","card"). type("K000013","card"). type("K000014","card"). type("K000015","card"). type("K000016","card"). type("K000017","card").
nationality("P000010","FIN"). has_card("P000010","K000012"). ovr("K000012",85). salary("K000012",60). position("K000012","C").  card_type("K000012","COM"). team("K000012","TOR").
nationality("P000011","SWE"). has_card("P000011","K000013"). ovr("K000013",81). salary("K000013",20). position("K000013","C").  card_type("K000013","COM"). team("K000013","CAR").
nationality("P000012","CAN"). has_card("P000012","K000014"). ovr("K000014",79). salary("K000014",9). position("K000014","C").  card_type("K000014","COM"). team("K000014","PIT").
nationality("P000013","AUT"). has_card("P000013","K000015"). ovr("K000015",78). salary("K000015",8). position("K000015","C").  card_type("K000015","COM"). team("K000015","DET").
nationality("P000014","USA"). has_card("P000014","K000016"). ovr("K000016",77). salary("K000016",7). position("K000016","C").  card_type("K000016","GB").  team("K000016","MTL").
nationality("P000015","CAN"). has_card("P000015","K000017"). ovr("K000017",77). salary("K000017",7). position("K000017","C").  card_type("K000017","COM"). team("K000017","OTT").
id("P000020"). type("P000020","player"). id("K000020"). type("K000020","card").
nationality("P000020","SLOVAKIA"). has_card("P000020","K000020"). ovr("K000020",90). salary("K000020",120). position("K000020","C"). card_type("K000020","CAP"). team("K000020","TOR").
id("P000021"). type("P000021","player"). id("K000021"). type("K000021","card").
nationality("P000021","CZECHIA"). has_card("P000021","K000021"). ovr("K000021",88). salary("K000021",100). position("K000021","G"). card_type("K000021","COM"). team("K000021","CHI").
id("P000022"). type("P000022","player"). id("K000022"). type("K000022","card").
nationality("P000022","USA"). has_card("P000022","K000022"). ovr("K000022",86). salary("K000022",80). position("K000022","G"). card_type("K000022","CAP"). team("K000022","DET").
id("P000023"). type("P000023","player"). id("K000023"). type("K000023","card").
nationality("P000023","CAN"). has_card("P000023","K000023"). ovr("K000023",84). salary("K000023",70). position("K000023","G"). card_type("K000023","COM"). team("K000023","STL").
id("P000024"). type("P000024","player"). id("K000024"). type("K000024","card").
nationality("P000024","FINLAND"). has_card("P000024","K000024"). ovr("K000024",83). salary("K000024",50). position("K000024","G"). card_type("K000024","COM"). team("K000024","VAN").
"""

def solve(files, extra_rules="", consts=None, ctl_opts=None):
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
    def on_model(m):
        nonlocal opt
        models.append(m.symbols(shown=True))
        if m.cost:
            opt = tuple(m.cost)
    res = ctl.solve(on_model=on_model)
    return res, models, opt

def test_def_ovr_description():
    res, models, cost = solve(["../../src/asp/def_ovr_description.lp", "../../src/asp/main_description.lp"], extra_rules=extra, consts={"n": 2})

    assert res.satisfiable
    assert res.exhausted
    assert models

    # visible when running `pytest -s`
    for i, m in enumerate(models, 1):
        print(f"Answer: {i}")
        print(" ".join(str(s) for s in m))
    if cost is not None:
        print("Optimization:", *cost)

def test_def_ap_description():
    res, models, cost = solve(["../../src/asp/def_ap_description.lp", "../../src/asp/main_description.lp"], extra_rules=extra, consts={"n": 2})
    assert res.satisfiable
    assert res.exhausted
    assert models

    # visible when running `pytest -s`
    for i, m in enumerate(models, 1):
        print(f"Answer: {i}")
        print(" ".join(str(s) for s in m))
    if cost is not None:
        print("Optimization:", *cost)

def test_def_sal_description():
    res, models, cost = solve(["../../src/asp/def_sal_description.lp", "../../src/asp/main_description.lp"], extra_rules=extra, consts={
        "n": 2,
        "salary_cap_boost_10": 10,
        "salary_cap_boost_15": 15,})
    assert res.satisfiable
    assert res.exhausted
    assert models

    # visible when running `pytest -s`
    for i, m in enumerate(models, 1):
        print(f"Answer: {i}")
        print(" ".join(str(s) for s in m))
    if cost is not None:
        print("Optimization:", *cost)

def test_fwd_ap_description():
    res, models, cost = solve(["../../src/asp/fwd_ap_description.lp", "../../src/asp/main_description.lp"], extra_rules=extra, consts={"n": 2})
    assert res.satisfiable
    assert res.exhausted
    assert models

    # visible when running `pytest -s`
    for i, m in enumerate(models, 1):
        print(f"Answer: {i}")
        print(" ".join(str(s) for s in m))
    if cost is not None:
        print("Optimization:", *cost)

def test_fwd_ovr_description():
    res, models, cost = solve(["../../src/asp/fwd_ovr_description.lp", "../../src/asp/main_description.lp"], extra_rules=extra, consts={"n": 2})
    assert res.satisfiable
    assert res.exhausted
    assert models

    # visible when running `pytest -s`
    for i, m in enumerate(models, 1):
        print(f"Answer: {i}")
        print(" ".join(str(s) for s in m))
    if cost is not None:
        print("Optimization:", *cost)

def test_fwd_sal_description():
    files = ["../../src/asp/fwd_sal_description.lp", "../../src/asp/main_description.lp"]
    show = "\n#show.\n#show best_forward_line_sal_combination/3.\n"
    res, models, cost = solve(
        files,
        extra_rules=extra + show,
        consts={"salary_cap": 900},
        ctl_opts=["--opt-mode=optN"]  # enumerate all optimal models
    )

    assert res.satisfiable
    assert res.exhausted
    assert models

    # visible when running `pytest -s`
    for i, m in enumerate(models, 1):
        print(f"Answer: {i}")
        print(" ".join(str(s) for s in m))
    if cost is not None:
        print("Optimization:", *cost)