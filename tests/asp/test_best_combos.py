# uses only clingo + pytest
import clingo
import pytest

# ---------------- runner & helpers ----------------
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

def shown(models, name):
    return [s for s in models[-1] if s.name == name]

def sym_to_str(sym):
    # clingo returns strings as '"X"'; strip quotes for easy dict/set use
    s = str(sym)
    return s[1:-1] if s.startswith('"') and s.endswith('"') else s

def norm_pair(a, b):
    x, y = map(sym_to_str, (a, b))
    return tuple(sorted((x, y)))

def norm_triple(a, b, c):
    x, y, z = map(sym_to_str, (a, b, c))
    return tuple(sorted((x, y, z)))


# ---------------- shared base facts ----------------
BASE = r"""
boost_type("OVR"). boost_type("SAL"). boost_type("AP").
country("CANADA"). country("USA").
event("COM"). event("CAP"). event("TOTW").
club("TOR"). club("DET"). club("BOS"). club("VGK").
"""


# ===================== DEF: def_best_combo.lp =====================

def test_def_best_combo_ties_are_accumulated_not_broken():
    """
    Property specific to def_best_combo.lp under ties:
    With equal OVR/AP across multiple pairs, the choice + sum objective accumulates
    *all* intersection pairs rather than selecting a single winner.
    We compute the expected unordered pairs from the cards we inject (no hard-coding).
    """
    extra = BASE + r"""
    id("P1"). type("P1","player"). nationality("P1","CANADA").
    id("P2"). type("P2","player"). nationality("P2","USA").
    id("P3"). type("P3","player"). nationality("P3","CANADA").
    id("P4"). type("P4","player"). nationality("P4","USA").

    id("E1"). type("E1","card"). has_card("P1","E1"). position("E1","LD").
    ovr("E1",85). salary("E1",300). team("E1","TOR"). card_type("E1","COM").
    id("E2"). type("E2","card"). has_card("P2","E2"). position("E2","RD").
    ovr("E2",85). salary("E2",300). team("E2","TOR"). card_type("E2","COM").

    id("E3"). type("E3","card"). has_card("P3","E3"). position("E3","LD").
    ovr("E3",85). salary("E3",300). team("E3","DET"). card_type("E3","COM").
    id("E4"). type("E4","card"). has_card("P4","E4"). position("E4","RD").
    ovr("E4",85). salary("E4",300). team("E4","DET"). card_type("E4","COM").

    % Equal AP/OVR boosts (everyone COM); SAL boosts differ but are ignored by def_best objective
    defense_combo("ap_all",10,"AP",event("COM"),event("COM")).
    defense_combo("ovr_all",5,"OVR",event("COM"),event("COM")).
    defense_combo("sal_tor",100,"SAL",club("TOR"),club("TOR")).
    defense_combo("sal_det",200,"SAL",club("DET"),club("DET")).

    #show def_best_combination/2.
    """
    files = [
        "src/asp/def_ap_description.lp",
        "src/asp/def_ovr_description.lp",
        "src/asp/def_sal_description.lp",
        "src/asp/main_description.lp",
        "src/asp/def_best_combo.lp",
    ]
    res, models = solve(files, extra_rules=extra, ctl_opts=["--opt-mode=optN"])
    assert res.satisfiable

    # What program chose
    chosen = { norm_pair(*s.arguments) for s in shown(models, "def_best_combination") }

    # Expected: all unordered pairs among {E1,E2,E3,E4}
    cards = ["E1", "E2", "E3", "E4"]
    expected = { tuple(sorted((a, b))) for i,a in enumerate(cards) for b in cards[i+1:] }

    assert chosen == expected, f"expected accumulation of all pairs: {expected}, got {chosen}"


def test_def_best_combo_intersection_prefers_cap_feasible_pair_but_excludes_expensive():
    """
    Property: When cap is tight, only cap-feasible pair(s) should survive the intersection.
    We do not rely on hard-coded ids, we check presence/absence by totals vs cap.
    """
    extra = BASE + r"""
    % TOR cheap pair
    id("Q1"). type("Q1","player"). nationality("Q1","CANADA").
    id("Q2"). type("Q2","player"). nationality("Q2","USA").
    id("T1"). type("T1","card"). has_card("Q1","T1"). position("T1","LD").
    ovr("T1",80). salary("T1",200). team("T1","TOR"). card_type("T1","COM").
    id("T2"). type("T2","card"). has_card("Q2","T2"). position("T2","RD").
    ovr("T2",80). salary("T2",200). team("T2","TOR"). card_type("T2","COM").

    % DET expensive high-OVR pair
    id("Q3"). type("Q3","player"). nationality("Q3","CANADA").
    id("Q4"). type("Q4","player"). nationality("Q4","USA").
    id("D1"). type("D1","card"). has_card("Q3","D1"). position("D1","LD").
    ovr("D1",92). salary("D1",600). team("D1","DET"). card_type("D1","CAP").
    id("D2"). type("D2","card"). has_card("Q4","D2"). position("D2","RD").
    ovr("D2",92). salary("D2",600). team("D2","DET"). card_type("D2","CAP").

    defense_combo("ap_det",5,"AP",club("DET"),club("DET")).
    defense_combo("ovr_det",3,"OVR",club("DET"),club("DET")).
    defense_combo("sal_tor",100,"SAL",club("TOR"),club("TOR")).

    #show def_best_combination/2.
    """
    files = [
        "src/asp/def_ap_description.lp",
        "src/asp/def_ovr_description.lp",
        "src/asp/def_sal_description.lp",
        "src/asp/main_description.lp",
        "src/asp/def_best_combo.lp",
    ]
    res, models = solve(
        files,
        extra_rules=extra,
        consts={"salary_cap": 500},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable
    chosen = { norm_pair(*s.arguments) for s in shown(models, "def_best_combination") }

    # Cheap pair total=400, expensive pair total=1200 (cap=500)
    assert ("T1", "T2") in chosen, "cap-feasible TOR pair must remain"
    assert ("D1", "D2") not in chosen, "expensive DET pair must be excluded by cap"


# ===================== FWD: fwd_best_combo.lp =====================

def test_fwd_best_combo_ties_are_accumulated_not_broken():
    """
    Property specific to fwd_best_combo.lp under ties:
    With equal OVR/AP among multiple candidate triples, the program accumulates all
    triples in the intersection (not a single winner). We build expectation from facts.
    """
    extra = BASE + r"""
    id("PF1"). type("PF1","player"). nationality("PF1","CANADA").
    id("PF2"). type("PF2","player"). nationality("PF2","USA").
    id("PF3"). type("PF3","player"). nationality("PF3","USA").
    id("PF4"). type("PF4","player"). nationality("PF4","CANADA").

    id("A"). type("A","card"). has_card("PF1","A"). position("A","C").
    ovr("A",90). salary("A",300). team("A","BOS"). card_type("A","COM").
    id("B"). type("B","card"). has_card("PF2","B"). position("B","LW").
    ovr("B",88). salary("B",300). team("B","BOS"). card_type("B","COM").
    id("C"). type("C","card"). has_card("PF3","C"). position("C","RW").
    ovr("C",86). salary("C",300). team("C","BOS"). card_type("C","COM").
    id("D"). type("D","card"). has_card("PF4","D"). position("D","RW").
    ovr("D",86). salary("D",300). team("D","BOS"). card_type("D","COM").

    forward_combo("ap_all",5,"AP",club("BOS"),club("BOS"),club("BOS")).
    forward_combo("ovr_all",3,"OVR",club("BOS"),club("BOS"),club("BOS")).
    forward_combo("sal_all",100,"SAL",club("BOS"),club("BOS"),club("BOS")).

    #show fwd_best_combination/3.
    """
    files = [
        "src/asp/fwd_ap_description.lp",
        "src/asp/fwd_ovr_description.lp",
        "src/asp/fwd_sal_description.lp",
        "src/asp/main_description.lp",
        "src/asp/fwd_best_combo.lp",
    ]
    res, models = solve(
        files,
        extra_rules=extra,
        consts={"salary_cap": 1000},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable
    chosen = { norm_triple(*s.arguments) for s in shown(models, "fwd_best_combination") }

    # Expected: all 3-of-4 unordered triples from {"A","B","C","D"}
    cards = ["A", "B", "C", "D"]
    expected = {
        tuple(sorted((cards[i], cards[j], cards[k])))
        for i in range(4) for j in range(i+1, 4) for k in range(j+1, 4)
    }
    assert chosen == expected, f"expected accumulation of all triples: {expected}, got {chosen}"


def test_fwd_best_combo_empty_intersection_yields_only_cap_feasible_line():
    """
    Property: With a tight cap, only the cheaper line should remain in the intersection.
    We assert inclusion/exclusion by ids derived from the facts, not counts.
    """
    extra = BASE + r"""
    % expensive high-ovr line (A,B,C)
    id("P1"). type("P1","player"). nationality("P1","CANADA").
    id("P2"). type("P2","player"). nationality("P2","USA").
    id("P3"). type("P3","player"). nationality("P3","USA").
    id("A"). type("A","card"). has_card("P1","A"). position("A","C").
    ovr("A",95). salary("A",500). team("A","VGK"). card_type("A","CAP").
    id("B"). type("B","card"). has_card("P2","B"). position("B","LW").
    ovr("B",93). salary("B",500). team("B","VGK"). card_type("B","CAP").
    id("C"). type("C","card"). has_card("P3","C"). position("C","RW").
    ovr("C",92). salary("C",500). team("C","VGK"). card_type("C","CAP").

    % cheap lower-ovr line (E,F,G)
    id("P4"). type("P4","player"). nationality("P4","CANADA").
    id("P5"). type("P5","player"). nationality("P5","USA").
    id("P6"). type("P6","player"). nationality("P6","USA").
    id("E"). type("E","card"). has_card("P4","E"). position("E","C").
    ovr("E",84). salary("E",200). team("E","BOS"). card_type("E","COM").
    id("F"). type("F","card"). has_card("P5","F"). position("F","LW").
    ovr("F",83). salary("F",200). team("F","BOS"). card_type("F","COM").
    id("G"). type("G","card"). has_card("P6","G"). position("G","RW").
    ovr("G",82). salary("G",200). team("G","BOS"). card_type("G","COM").

    forward_combo("ovr_vgk",3,"OVR",club("VGK"),club("VGK"),club("VGK")).
    forward_combo("ap_vgk",5,"AP",club("VGK"),club("VGK"),club("VGK")).
    forward_combo("sal_bos",150,"SAL",club("BOS"),club("BOS"),club("BOS")).

    #show fwd_best_combination/3.
    """
    files = [
        "src/asp/fwd_ap_description.lp",
        "src/asp/fwd_ovr_description.lp",
        "src/asp/fwd_sal_description.lp",
        "src/asp/main_description.lp",
        "src/asp/fwd_best_combo.lp",
    ]
    res, models = solve(
        files,
        extra_rules=extra,
        consts={"salary_cap": 650},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable
    chosen = { norm_triple(*s.arguments) for s in shown(models, "fwd_best_combination") }

    assert ("E", "F", "G") in chosen, "cheap BOS line should be feasible under cap"
    assert ("A", "B", "C") not in chosen, "expensive VGK line should be excluded by cap"
