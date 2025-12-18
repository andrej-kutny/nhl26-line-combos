import pytest

from src.asp.solver import ASPSolver


def test_stageb_forward_enumerates_all_3_of_4_combinations():
    assert ASPSolver.is_available(), "clingo is required for this test (see requirements.txt)"
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


def test_stageb_defense_enumerates_pair_for_required_combo():
    assert ASPSolver.is_available(), "clingo is required for this test (see requirements.txt)"
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


def test_stageb_forward_reports_non_required_active_combos_and_bonus_sums():
    assert ASPSolver.is_available(), "clingo is required for this test (see requirements.txt)"
    solver = ASPSolver()
    base_rules = solver._read_rules("base.lp")
    stageb_rules = solver._read_rules("goal1_stageb_forward.lp")

    facts = """
    player("p1", 80, "det", "canada", "fant"). salary("p1", 0). ap("p1", 0).
    player("p2", 81, "det", "canada", "fant"). salary("p2", 0). ap("p2", 0).
    player("p3", 82, "det", "canada", "fant"). salary("p3", 0). ap("p3", 0).
    card_player("p1", "G1"). card_player("p2", "G2"). card_player("p3", "G3").

    % Required: DET*3 => +20 SAL
    fwd_combo(1, 20, sal, "team", "det", "team", "det", "team", "det").
    required_combo(1).

    % Not required but still active: CANADA*3 => +5 SAL
    fwd_combo(2, 5, sal, "nationality", "canada", "nationality", "canada", "nationality", "canada").
    """
    program = "\n".join([facts, base_rules, stageb_rules])
    models = solver._enumerate(program, max_models=10)
    assert len(models) == 1

    atoms = {str(s) for s in models[0]}
    assert "combo_active(1)" in atoms
    assert "combo_active(2)" in atoms
    assert "total_salary_bonus(25)" in atoms
