import clingo
import pytest

# ---------- runner ----------
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
    models = []
    def on_model(m):
        models.append(m.symbols(shown=True))
    res = ctl.solve(on_model=on_model)
    return res, models

# ---------- shared base facts ----------
BASE = r"""
boost_type("OVR"). boost_type("SAL"). boost_type("AP").
country("CANADA"). country("USA"). country("FINLAND").
event("COM"). event("CAP"). event("TOTW").
club("BOS"). club("VGK"). club("TOR"). club("DET").
"""

# ---------- main_description.lp ----------
def test_main_description_forward_line_canonicalization():
    extra = BASE + r"""
    id("P1"). type("P1","player"). nationality("P1","CANADA").
    id("P2"). type("P2","player"). nationality("P2","USA").
    id("P3"). type("P3","player"). nationality("P3","USA").

    id("K1"). type("K1","card"). has_card("P1","K1"). position("K1","C").
    ovr("K1",92). salary("K1",10). team("K1","BOS"). card_type("K1","COM").

    id("K2"). type("K2","card"). has_card("P2","K2"). position("K2","LW").
    ovr("K2",90). salary("K2",10). team("K2","BOS"). card_type("K2","COM").

    id("K3"). type("K3","card"). has_card("P3","K3"). position("K3","RW").
    ovr("K3",88). salary("K3",10). team("K3","BOS"). card_type("K3","COM").

    #show forward_line/3.
    """
    files = ["src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra)
    assert res.satisfiable
    fl = [s for s in models[0] if s.name == "forward_line"]
    assert len(fl) == 1

def test_main_description_defense_line_basic():
    extra = BASE + r"""
    id("P4"). type("P4","player"). nationality("P4","CANADA").
    id("P5"). type("P5","player"). nationality("P5","USA").

    id("D1"). type("D1","card"). has_card("P4","D1"). position("D1","LD").
    ovr("D1",89). salary("D1",9). team("D1","TOR"). card_type("D1","COM").

    id("D2"). type("D2","card"). has_card("P5","D2"). position("D2","RD").
    ovr("D2",87). salary("D2",9). team("D2","DET"). card_type("D2","COM").

    #show defense_line/2.
    """
    files = ["src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra)
    assert res.satisfiable
    assert any(s.name == "defense_line" for s in models[0])

# ---------- fwd_sal_description.lp ----------
def test_fwd_sal_description_best_forward_line_sal_combination():
    extra = BASE + r"""
    % forwards
    id("PF1"). type("PF1","player"). nationality("PF1","CANADA").
    id("PF2"). type("PF2","player"). nationality("PF2","USA").
    id("PF3"). type("PF3","player"). nationality("PF3","USA").
    id("PF4"). type("PF4","player"). nationality("PF4","USA").

    id("F1"). type("F1","card"). has_card("PF1","F1"). position("F1","C").
    ovr("F1",90). salary("F1",400). team("F1","BOS"). card_type("F1","COM").

    id("F2"). type("F2","card"). has_card("PF2","F2"). position("F2","LW").
    ovr("F2",88). salary("F2",350). team("F2","BOS"). card_type("F2","COM").

    id("F3"). type("F3","card"). has_card("PF3","F3"). position("F3","RW").
    ovr("F3",86). salary("F3",300). team("F3","BOS"). card_type("F3","COM").

    id("F4"). type("F4","card"). has_card("PF4","F4"). position("F4","RW").
    ovr("F4",82). salary("F4",200). team("F4","VGK"). card_type("F4","CAP").

    % one SAL boost defined via a forward_combo over clubs/events
    forward_combo("fc_s",200,"SAL",club("BOS"),club("BOS"),club("BOS")).

    #show best_forward_line_sal_combination/3.
    """
    files = ["src/asp/fwd_sal_description.lp", "src/asp/main_description.lp"]
    res, models = solve(
        files,
        extra_rules=extra,
        consts={"salary_cap": 900, "w_sal": 1},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable
    shown = [s for s in models[-1] if s.name == "best_forward_line_sal_combination"]
    assert shown

# ---------- fwd_ovr_description.lp ----------
def test_fwd_ovr_description_best_forward_line_ovr_combination():
    extra = BASE + r"""
    id("P1"). type("P1","player"). nationality("P1","CANADA").
    id("P2"). type("P2","player"). nationality("P2","USA").
    id("P3"). type("P3","player"). nationality("P3","USA").

    id("A"). type("A","card"). has_card("P1","A"). position("A","C").
    ovr("A",88). salary("A",10). team("A","BOS"). card_type("A","TOTW").

    id("B"). type("B","card"). has_card("P2","B"). position("B","LW").
    ovr("B",85). salary("B",10). team("B","VGK"). card_type("B","COM").

    id("C"). type("C","card"). has_card("P3","C"). position("C","RW").
    ovr("C",84). salary("C",10). team("C","VGK"). card_type("C","COM").

    % OVR boost defined by a forward_combo over countries or events
    forward_combo("fc_o",3,"OVR",event("TOTW"),event("COM"),event("COM")).

    #show best_forward_line_ovr_combination/3.
    """
    files = ["src/asp/fwd_ovr_description.lp", "src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra, ctl_opts=["--opt-mode=optN"])
    assert res.satisfiable
    shown = [s for s in models[-1] if s.name == "best_forward_line_ovr_combination"]
    assert shown

# ---------- fwd_ap_description.lp ----------
def test_fwd_ap_description_best_forward_line_ap_combination():
    extra = BASE + r"""
    id("P1"). type("P1","player"). nationality("P1","CANADA").
    id("P2"). type("P2","player"). nationality("P2","USA").
    id("P3"). type("P3","player"). nationality("P3","USA").

    id("A"). type("A","card"). has_card("P1","A"). position("A","C").
    ovr("A",82). salary("A",10). team("A","BOS"). card_type("A","COM").

    id("B"). type("B","card"). has_card("P2","B"). position("B","LW").
    ovr("B",81). salary("B",10). team("B","BOS"). card_type("B","COM").

    id("C"). type("C","card"). has_card("P3","C"). position("C","RW").
    ovr("C",80). salary("C",10). team("C","BOS"). card_type("C","COM").

    forward_combo("fc_ap",5,"AP",club("BOS"),club("BOS"),club("BOS")).

    #show best_forward_line_ap_combination/3.
    """
    files = ["src/asp/fwd_ap_description.lp", "src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra, ctl_opts=["--opt-mode=optN"])
    assert res.satisfiable
    shown = [s for s in models[-1] if s.name == "best_forward_line_ap_combination"]
    assert shown

# ---------- def_ap_description.lp ----------
def test_def_ap_description_boosted_def_line_exists():
    extra = BASE + r"""
    id("PD1"). type("PD1","player"). nationality("PD1","CANADA").
    id("PD2"). type("PD2","player"). nationality("PD2","USA").

    id("D1"). type("D1","card"). has_card("PD1","D1"). position("D1","LD").
    ovr("D1",90). salary("D1",10). team("D1","TOR"). card_type("D1","COM").

    id("D2"). type("D2","card"). has_card("PD2","D2"). position("D2","RD").
    ovr("D2",88). salary("D2",10). team("D2","DET"). card_type("D2","CAP").

    defense_combo("dc_ap",7,"AP",club("TOR"),event("COM")).

    #show boosted_def_line/6.
    """
    files = ["src/asp/def_ap_description.lp", "src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra)
    assert res.satisfiable
    shown = [s for s in models[-1] if s.name == "boosted_def_line"]
    assert shown

# ---------- def_ovr_description.lp ----------
def test_def_ovr_description_best_defense_line_ovr_combination():
    extra = BASE + r"""
    id("PD3"). type("PD3","player"). nationality("PD3","CANADA").
    id("PD4"). type("PD4","player"). nationality("PD4","USA").

    id("E1"). type("E1","card"). has_card("PD3","E1"). position("E1","LD").
    ovr("E1",90). salary("E1",10). team("E1","TOR"). card_type("E1","COM").

    id("E2"). type("E2","card"). has_card("PD4","E2"). position("E2","RD").
    ovr("E2",87). salary("E2",10). team("E2","DET"). card_type("E2","COM").

    defense_combo("dc_ovr",3,"OVR",club("TOR"),club("DET")).

    #show best_defense_line_ovr_combination/2.
    """
    files = ["src/asp/def_ovr_description.lp", "src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra, ctl_opts=["--opt-mode=optN"])
    assert res.satisfiable
    shown = [s for s in models[-1] if s.name == "best_defense_line_ovr_combination"]
    assert shown

# ---------- def_sal_description.lp ----------
def test_def_sal_description_best_defense_line_sal_combination():
    extra = BASE + r"""
    id("PG1"). type("PG1","player"). nationality("PG1","CANADA").
    id("PG2"). type("PG2","player"). nationality("PG2","USA").

    id("G1"). type("G1","card"). has_card("PG1","G1"). position("G1","G").
    ovr("G1",86). salary("G1",600). team("G1","TOR"). card_type("G1","COM").

    id("G2"). type("G2","card"). has_card("PG2","G2"). position("G2","G").
    ovr("G2",84). salary("G2",450). team("G2","DET"). card_type("G2","COM").

    defense_combo("dc_sal",150,"SAL",event("COM"),event("COM")).

    #show best_defense_line_sal_combination/2.
    """
    files = ["src/asp/def_sal_description.lp", "src/asp/main_description.lp"]
    res, models = solve(
        files,
        extra_rules=extra,
        consts={"salary_cap": 1000, "w_sal": 1},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable
    shown = [s for s in models[-1] if s.name == "best_defense_line_sal_combination"]
    assert shown
