import pytest

from src.asp.solver import ASPSolver


@pytest.mark.skipif(not ASPSolver.is_available(), reason="clingo not installed")
def test_duplicate_player_constraint_blocks_models():
    solver = ASPSolver()
    base_rules = solver._read_rules("base.lp")
    # Two different card_ids mapped to the same player_id
    facts = """
    player("a", 90, "team", "nat", "event").
    player("b", 89, "team", "nat", "event").
    card_player("a", 1).
    card_player("b", 1).
    select("a", 1).
    select("b", 2).
    """
    program = facts + "\n" + base_rules
    models = solver._solve(program, num_solutions=1)
    assert models == [], "Duplicate player_id selections should be disallowed"


@pytest.mark.skipif(not ASPSolver.is_available(), reason="clingo not installed")
def test_forward_line_rules_ground_and_solve():
    solver = ASPSolver()
    base_rules = solver._read_rules("base.lp")
    forward_rules = solver._read_rules("forward_line.lp")
    facts = """
    player("a", 90, "det", "canada", "fant").
    player("b", 89, "det", "canada", "fant").
    player("c", 88, "det", "canada", "fant").
    card_player("a", "p1").
    card_player("b", "p2").
    card_player("c", "p3").
    salary("a", 10). salary("b", 10). salary("c", 10).
    fwd_combo(1, 20, sal, "team", "det", "team", "det", "team", "det").
    opt_target("ovr").
    """
    program = "\n".join([facts, base_rules, forward_rules])
    models = solver._solve(program, num_solutions=1)
    assert models, "Expected at least one model from forward_line rules"


@pytest.mark.skipif(not ASPSolver.is_available(), reason="clingo not installed")
def test_defense_pair_rules_ground_and_solve():
    solver = ASPSolver()
    base_rules = solver._read_rules("base.lp")
    defense_rules = solver._read_rules("defense_pair.lp")
    facts = """
    player("d1", 85, "chi", "usa", "gm").
    player("d2", 84, "chi", "canada", "gm").
    card_player("d1", "p10").
    card_player("d2", "p11").
    def_combo(20, 8, ap, "team", "chi", "team", "chi").
    opt_target("ovr").
    """
    program = "\n".join([facts, base_rules, defense_rules])
    models = solver._solve(program, num_solutions=1)
    assert models, "Expected at least one model from defense_pair rules"
