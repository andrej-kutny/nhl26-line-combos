import pytest


def test_solve_any_ignores_optimization():
    from src.asp.solver import ASPSolver

    solver = ASPSolver()
    assert solver.is_available(), "clingo is required for this test (see requirements.txt)"

    program = """
    a.
    #maximize { 1@1,a }.
    #show a/0.
    """

    models, status = solver._solve_any(program, max_models=1, time_limit_seconds=5)
    assert status == "sat"
    assert models
    assert any(sym.name == "a" for sym in models[0])
