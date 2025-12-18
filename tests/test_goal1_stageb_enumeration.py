import pytest

from src.asp.solver import ASPSolver


@pytest.mark.skipif(not ASPSolver.is_available(), reason="clingo not installed")
def test_stageb_forward_enumerates_all_3_of_4_combinations():
    solver = ASPSolver()
    base_rules = solver._read_rules("base.lp")
    stageb_rules = solver._read_rules("goal1_stageb_forward.lp")

    # Four eligible players; any 3-player line should satisfy the "DET*3" combo.
    facts = """
    player("p1", 80, "det", "canada", "fant").
    player("p2", 81, "det", "canada", "fant").
    player("p3", 82, "det", "canada", "fant").
    player("p4", 83, "det", "canada", "fant").
    card_player("p1", "G1").
    card_player("p2", "G2").
    card_player("p3", "G3").
    card_player("p4", "G4").
    fwd_combo(1, 20, sal, "team", "det", "team", "det", "team", "det").
    required_combo(1).
    """
    program = "\n".join([facts, base_rules, stageb_rules])
    models = solver._enumerate(program, max_models=0)
    assert len(models) == 4, "Expected C(4,3)=4 distinct sets due to symmetry breaking"


@pytest.mark.skipif(not ASPSolver.is_available(), reason="clingo not installed")
def test_stageb_defense_enumerates_pair_for_required_combo():
    solver = ASPSolver()
    base_rules = solver._read_rules("base.lp")
    stageb_rules = solver._read_rules("goal1_stageb_defense.lp")

    facts = """
    player("d1", 85, "chi", "usa", "gm").
    player("d2", 84, "chi", "canada", "gm").
    card_player("d1", "G10").
    card_player("d2", "G11").
    def_combo(20, 8, ap, "team", "chi", "team", "chi").
    required_combo(20).
    """
    program = "\n".join([facts, base_rules, stageb_rules])
    models = solver._enumerate(program, max_models=10)
    assert len(models) == 1
    atoms = {str(s) for s in models[0]}
    assert "combo_active(20)" in atoms

