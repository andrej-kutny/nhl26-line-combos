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
