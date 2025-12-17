import pytest


def test_solve_any_ignores_optimization():
    from src.asp.solver import ASPSolver

    solver = ASPSolver()
    if not solver.is_available():
        pytest.skip("clingo not available in this environment")

    program = """
    a.
    #maximize { 1@1,a }.
    #show a/0.
    """

    models, status = solver._solve_any(program, max_models=1, time_limit_seconds=5)
    assert status == "sat"
    assert models
    assert any(sym.name == "a" for sym in models[0])

