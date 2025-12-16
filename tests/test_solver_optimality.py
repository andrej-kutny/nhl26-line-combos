import pytest

from src.asp.solver import ASPSolver


@pytest.mark.skipif(not ASPSolver.is_available(), reason="clingo not installed")
def test_solve_returns_optimal_model():
    solver = ASPSolver()
    program = """
    a(1). a(2).
    1 { pick(X) : a(X) } 1.
    #maximize { X@1 : pick(X) }.
    #show pick/1.
    """
    models = solver._solve(program, num_solutions=1)
    assert models, "Expected at least one model"
    atoms = {str(s) for s in models[0]}
    assert "pick(2)" in atoms, f"Expected optimal pick(2), got: {atoms}"

