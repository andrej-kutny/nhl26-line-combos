import pytest


def test_canonical_identity_prevents_duplicate_person():
    from src.asp.solver import ASPSolver

    solver = ASPSolver()
    assert solver.is_available(), "clingo is required for this test (see requirements.txt)"

    base_rules = solver._read_rules("base.lp")

    program = f"""
    player("c1", 80, "det", "usa", "ba").
    player("c2", 80, "det", "usa", "gm").

    card_player("c1", "p1").
    card_player("c2", "p2").

    card_canon("c1", "mason|appleton|usa").
    card_canon("c2", "mason|appleton|usa").

    1 {{ select(P,1) : player(P,_,_,_,_) }} 1.
    1 {{ select(P,2) : player(P,_,_,_,_) }} 1.
    :- select(P,S1), select(P,S2), S1 < S2.

    #show select/2.
    {base_rules}
    """

    models, status = solver._solve_any(program, max_models=1, time_limit_seconds=2)
    assert status in {"unsat", "unknown"}
    assert models == []
