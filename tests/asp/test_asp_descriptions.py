# tests/asp/test_asp_descriptions.py
import clingo
import pytest

# ------------------ runner + helpers ------------------

def solve(files, extra_rules: str = "", consts=None, ctl_opts=None):
    """
    Load ASP files + optional inline facts/rules, set #const values,
    ground, and collect shown atoms from all models.
    """
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

def shown(models, name: str):
    """Return shown symbols with the given predicate name from the last model."""
    if not models:
        return []
    return [s for s in models[-1] if s.name == name]

def sym_to_str(s: clingo.Symbol) -> str:
    """Unquote clingo.String symbols and stringify others uniformly."""
    return s.string if s.type == clingo.SymbolType.String else str(s)

def norm_pair(a, b):
    """Normalized unordered pair of clingo symbols as python strings."""
    A, B = sym_to_str(a), sym_to_str(b)
    return tuple(sorted((A, B)))

def norm_triple(a, b, c):
    """Normalized unordered triple of clingo symbols as python strings."""
    A, B, C = sym_to_str(a), sym_to_str(b), sym_to_str(c)
    return tuple(sorted((A, B, C)))

# ------------------ shared base facts ------------------

BASE = r"""
boost_type("OVR"). boost_type("SAL"). boost_type("AP").
country("CANADA"). country("USA"). country("FINLAND").
event("COM"). event("CAP"). event("TOTW").
club("BOS"). club("VGK"). club("TOR"). club("DET").
"""

# ------------------ main_description.lp ------------------

@pytest.mark.parametrize("n_lines", [1, 2, 3])
def test_main_description_forward_line_no_permutations(n_lines):
    """
    Property: All triples of forward_card/2 drawn from distinct players that satisfy
    O1>=O2>=O3 are produced exactly once (permutation-free).
    Works for any number of rows we generate.
    """
    facts = []
    pid = 1
    # keep helpers so we can compute expected programmatically
    cards = []            # list of card ids
    card_to_player = {}   # card -> player id
    ovr_val = {}          # card -> ovr

    for i in range(n_lines):
        for pos, o in [("C", 92), ("LW", 90), ("RW", 88)]:
            p = f"P{pid}"; pid += 1
            k = f"K{i}_{pos}"
            facts += [
                f'id("{p}"). type("{p}","player"). nationality("{p}","CANADA").',
                f'id("{k}"). type("{k}","card"). has_card("{p}","{k}"). position("{k}","{pos}").',
                f'ovr("{k}",{o}). salary("{k}",10). team("{k}","BOS"). card_type("{k}","COM").'
            ]
            cards.append(k)
            card_to_player[k] = p
            ovr_val[k] = o

    facts += ["#show forward_line/3."]
    extra = BASE + "\n".join(facts)
    files = ["src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra)
    assert res.satisfiable

    # What ASP produced (permutation-free via normalization)
    got = {
        tuple(sorted(map(sym_to_str, s.arguments)))
        for s in shown(models, "forward_line")
    }

    # Expected: all ordered triples A,B,C of cards s.t.
    # - players are pairwise distinct
    # - O1>=O2>=O3
    # Then normalized to be permutation-free for comparison.
    expected = set()
    for a in cards:
        for b in cards:
            if card_to_player[b] == card_to_player[a]:
                continue
            for c in cards:
                if card_to_player[c] in (card_to_player[a], card_to_player[b]):
                    continue
                if ovr_val[a] >= ovr_val[b] >= ovr_val[c]:
                    expected.add(tuple(sorted((a, b, c))))

    assert got == expected



# ------------------ fwd_sal_description.lp ------------------

@pytest.mark.parametrize("cap,boost", [(800, 0), (900, 100), (1200, 0)])
def test_fwd_sal_description_cap_respected(cap, boost):
    """
    Property: Every best_forward_line_sal_combination/3 satisfies the cap:
      salary(A)+salary(B)+salary(C) <= salary_cap + boost*w_sal
    Also, because your objective sums over chosen items, the optimal model
    includes *all* feasible SAL combos: chosen == feasible.
    """
    facts = [
        # BOS triple (eligible for SAL forward_combo)
        'id("P1"). type("P1","player"). nationality("P1","CANADA").',
        'id("P2"). type("P2","player"). nationality("P2","USA").',
        'id("P3"). type("P3","player"). nationality("P3","USA").',
        'id("A"). type("A","card"). has_card("P1","A"). position("A","C"). ovr("A",90). salary("A",400). team("A","BOS"). card_type("A","COM").',
        'id("B"). type("B","card"). has_card("P2","B"). position("B","LW"). ovr("B",88). salary("B",350). team("B","BOS"). card_type("B","COM").',
        'id("C"). type("C","card"). has_card("P3","C"). position("C","RW"). ovr("C",86). salary("C",300). team("C","BOS"). card_type("C","COM").',

        # VGK triple (no SAL forward_combo)
        'id("P4"). type("P4","player"). nationality("P4","CANADA").',
        'id("P5"). type("P5","player"). nationality("P5","USA").',
        'id("P6"). type("P6","player"). nationality("P6","USA").',
        'id("D"). type("D","card"). has_card("P4","D"). position("D","C"). ovr("D",84). salary("D",200). team("D","VGK"). card_type("D","CAP").',
        'id("E"). type("E","card"). has_card("P5","E"). position("E","LW"). ovr("E",83). salary("E",200). team("E","VGK"). card_type("E","CAP").',
        'id("F"). type("F","card"). has_card("P6","F"). position("F","RW"). ovr("F",82). salary("F",200). team("F","VGK"). card_type("F","CAP").',

        # SAL boost for BOS line
        f'forward_combo("sal_bos",{boost},"SAL",club("BOS"),club("BOS"),club("BOS")).',

        # Show feasible and chosen SAL picks
        "#show forward_line_sal_combination/3.",
        "#show best_forward_line_sal_combination/3.",
    ]
    extra = BASE + "\n".join(facts)
    files = ["src/asp/fwd_sal_description.lp", "src/asp/main_description.lp"]
    res, models = solve(
        files,
        extra_rules=extra,
        consts={"salary_cap": cap, "w_sal": 1},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable

    feasible = {
        tuple(sorted(map(sym_to_str, s.arguments)))
        for s in shown(models, "forward_line_sal_combination")
    }
    chosen = {
        tuple(sorted(map(sym_to_str, s.arguments)))
        for s in shown(models, "best_forward_line_sal_combination")
    }
    # accumulation behavior:
    assert chosen == feasible

    # respect cap (vacuously true if no picks)
    sal = {"A":400, "B":350, "C":300, "D":200, "E":200, "F":200}
    for A, B, C in chosen:
        total = sal[A] + sal[B] + sal[C]
        assert total <= cap + boost * 1  # w_sal=1 via consts


# ------------------ fwd_ovr_description.lp ------------------

def test_fwd_ovr_description_accumulates_all_feasible():
    """
    Property: best_forward_line_ovr_combination/3 equals forward_line_ovr_combination/3
    (accumulation, not single-argmax), given your maximize form.
    """
    facts = [
        # High OVR BOS triple (TOTW+COM+COM)
        'id("P1"). type("P1","player"). nationality("P1","CANADA").',
        'id("P2"). type("P2","player"). nationality("P2","USA").',
        'id("P3"). type("P3","player"). nationality("P3","USA").',
        'id("H"). type("H","card"). has_card("P1","H"). position("H","C"). ovr("H",92). salary("H",10). team("H","BOS"). card_type("H","TOTW").',
        'id("I"). type("I","card"). has_card("P2","I"). position("I","LW"). ovr("I",91). salary("I",10). team("I","BOS"). card_type("I","COM").',
        'id("J"). type("J","card"). has_card("P3","J"). position("J","RW"). ovr("J",90). salary("J",10). team("J","BOS"). card_type("J","COM").',

        # Lower OVR BOS triple (COM+COM+COM)
        'id("P4"). type("P4","player"). nationality("P4","CANADA").',
        'id("P5"). type("P5","player"). nationality("P5","USA").',
        'id("P6"). type("P6","player"). nationality("P6","USA").',
        'id("K"). type("K","card"). has_card("P4","K"). position("K","C"). ovr("K",85). salary("K",10). team("K","BOS"). card_type("K","COM").',
        'id("L"). type("L","card"). has_card("P5","L"). position("L","LW"). ovr("L",84). salary("L",10). team("L","BOS"). card_type("L","COM").',
        'id("M"). type("M","card"). has_card("P6","M"). position("M","RW"). ovr("M",83). salary("M",10). team("M","BOS"). card_type("M","COM").',

        # OVR boost enabled by TOTW+COM+COM (affects only the first triple)
        'forward_combo("ovr_rule",3,"OVR",event("TOTW"),event("COM"),event("COM")).',

        # Show feasible & chosen
        "#show forward_line_ovr_combination/3.",
        "#show best_forward_line_ovr_combination/3."
    ]
    extra = BASE + "\n".join(facts)
    files = ["src/asp/fwd_ovr_description.lp", "src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra, ctl_opts=["--opt-mode=optN"])
    assert res.satisfiable

    feasible = {
        tuple(sorted(map(sym_to_str, s.arguments)))
        for s in shown(models, "forward_line_ovr_combination")
    }
    chosen = {
        tuple(sorted(map(sym_to_str, s.arguments)))
        for s in shown(models, "best_forward_line_ovr_combination")
    }
    assert chosen == feasible


# ------------------ def_ovr_description.lp ------------------

def test_def_ovr_description_accumulates_all_feasible():
    """
    Property: best_defense_line_ovr_combination/2 equals defense_line_ovr_combination/2
    (accumulation behavior).
    """
    facts = [
        'id("PA"). type("PA","player"). nationality("PA","CANADA").',
        'id("PB"). type("PB","player"). nationality("PB","USA").',
        'id("PC"). type("PC","player"). nationality("PC","CANADA").',
        'id("PD"). type("PD","player"). nationality("PD","USA").',

        'id("DL1"). type("DL1","card"). has_card("PA","DL1"). position("DL1","LD"). ovr("DL1",90). salary("DL1",10). team("DL1","TOR"). card_type("DL1","COM").',
        'id("DR1"). type("DR1","card"). has_card("PB","DR1"). position("DR1","RD"). ovr("DR1",89). salary("DR1",10). team("DR1","TOR"). card_type("DR1","COM").',

        'id("DL2"). type("DL2","card"). has_card("PC","DL2"). position("DL2","LD"). ovr("DL2",85). salary("DL2",10). team("DL2","DET"). card_type("DL2","COM").',
        'id("DR2"). type("DR2","card"). has_card("PD","DR2"). position("DR2","RD"). ovr("DR2",84). salary("DR2",10). team("DR2","DET"). card_type("DR2","COM").',

        'defense_combo("ovr_any",4,"OVR",event("COM"),event("COM")).',
        "#show defense_line_ovr_combination/2.",
        "#show best_defense_line_ovr_combination/2."
    ]
    extra = BASE + "\n".join(facts)
    files = ["src/asp/def_ovr_description.lp", "src/asp/main_description.lp"]
    res, models = solve(files, extra_rules=extra, ctl_opts=["--opt-mode=optN"])
    assert res.satisfiable

    feasible = {
        norm_pair(*s.arguments)
        for s in shown(models, "defense_line_ovr_combination")
    }
    chosen = {
        norm_pair(*s.arguments)
        for s in shown(models, "best_defense_line_ovr_combination")
    }
    assert chosen == feasible


# ------------------ def_sal_description.lp ------------------

@pytest.mark.parametrize("cap,boost", [(700, 0), (800, 100)])
def test_def_sal_description_cap_respected(cap, boost):
    """
    Property: Every best_defense_line_sal_combination/2 satisfies the cap:
      salary(A)+salary(B) <= salary_cap + boost*w_sal
    And, as with other files, chosen == feasible under your accumulation maximize.
    """
    facts = [
        'id("PG1"). type("PG1","player"). nationality("PG1","CANADA").',
        'id("PG2"). type("PG2","player"). nationality("PG2","USA").',
        'id("PG3"). type("PG3","player"). nationality("PG3","CANADA").',
        'id("PG4"). type("PG4","player"). nationality("PG4","USA").',

        'id("G1"). type("G1","card"). has_card("PG1","G1"). position("G1","LD"). ovr("G1",86). salary("G1",600). team("G1","TOR"). card_type("G1","COM").',
        'id("G2"). type("G2","card"). has_card("PG2","G2"). position("G2","RD"). ovr("G2",450). salary("G2",450). team("G2","DET"). card_type("G2","COM").',

        'id("G3"). type("G3","card"). has_card("PG3","G3"). position("G3","LD"). ovr("G3",80). salary("G3",200). team("G3","DET"). card_type("G3","COM").',
        'id("G4"). type("G4","card"). has_card("PG4","G4"). position("G4","RD"). ovr("G4",80). salary("G4",200). team("G4","DET"). card_type("G4","COM").',

        f'defense_combo("sal_det",{boost},"SAL",club("DET"),club("DET")).',
        "#show defense_line_sal_combination/2.",
        "#show best_defense_line_sal_combination/2."
    ]
    extra = BASE + "\n".join(facts)
    files = ["src/asp/def_sal_description.lp", "src/asp/main_description.lp"]
    res, models = solve(
        files,
        extra_rules=extra,
        consts={"salary_cap": cap, "w_sal": 1},
        ctl_opts=["--opt-mode=optN"]
    )
    assert res.satisfiable

    feasible = {
        norm_pair(*s.arguments)
        for s in shown(models, "defense_line_sal_combination")
    }
    chosen = {
        norm_pair(*s.arguments)
        for s in shown(models, "best_defense_line_sal_combination")
    }
    assert chosen == feasible

    sal = {"G1":600, "G2":450, "G3":200, "G4":200}
    for A, B in chosen:
        total = sal[A] + sal[B]
        assert total <= cap + boost * 1  # w_sal=1
