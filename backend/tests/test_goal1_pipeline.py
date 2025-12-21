"""
Tests for Goal 1 pipeline components.

Run with: pytest tests/test_goal1_pipeline.py -v
"""

import pytest

from src.asp import (
    # Interfaces
    StageAInput,
    StageASolution,
    StageBInput,
    CandidatePlayer,
    # Generators
    StageAInputGenerator,
    StageBInputGenerator,
    # Solvers
    get_stage_a_solver,
    get_stage_b_solver,
    # Pipeline
    Goal1Pipeline,
    run_goal1_pipeline,
)
from src.core.data import get_results_store


# =============================================================================
# STAGE A TESTS
# =============================================================================

class TestStageAInputGenerator:
    """Tests for Stage A input generation."""
    
    def test_generate_forward_ovr(self):
        """Generate input for forward OVR optimization."""
        generator = StageAInputGenerator()
        input_data = generator.generate("forward", "ovr", top_k=50)
        
        assert input_data.position_type == "forward"
        assert input_data.optimization_mode == "ovr"
        assert input_data.top_k == 50
        assert len(input_data.combo_facts) > 0
    
    def test_generate_defense_sal(self):
        """Generate input for defense SAL optimization."""
        generator = StageAInputGenerator()
        input_data = generator.generate("defense", "sal", top_k=100)
        
        assert input_data.position_type == "defense"
        assert input_data.optimization_mode == "sal"
        assert len(input_data.combo_facts) > 0
    
    def test_weights_forward(self):
        """Forward combos should have correct default weights."""
        generator = StageAInputGenerator()
        input_data = generator.generate("forward", "ovr_sal")
        
        assert input_data.ovr_weight == 3.0
        assert input_data.sal_weight == 1.0
    
    def test_weights_defense(self):
        """Defense combos should have correct default weights."""
        generator = StageAInputGenerator()
        input_data = generator.generate("defense", "ovr_sal")
        
        assert input_data.ovr_weight == 2.0
        assert input_data.sal_weight == 1.0
    
    def test_single_mode_weights(self):
        """Single mode should have weight only for that metric."""
        generator = StageAInputGenerator()
        
        ovr_input = generator.generate("forward", "ovr")
        assert ovr_input.ovr_weight == 1.0
        assert ovr_input.sal_weight == 0.0
        
        sal_input = generator.generate("forward", "sal")
        assert sal_input.ovr_weight == 0.0
        assert sal_input.sal_weight == 1.0


class TestStageASolver:
    """Tests for Stage A mock solver."""
    
    def test_solve_returns_solutions(self):
        """Solver should return solutions."""
        generator = StageAInputGenerator()
        solver = get_stage_a_solver()
        
        input_data = generator.generate("forward", "ovr", top_k=10)
        output = solver.solve(input_data)
        
        assert len(output.solutions) > 0
        assert output.solve_time_ms >= 0
    
    def test_solutions_have_correct_structure(self):
        """Solutions should have required fields."""
        generator = StageAInputGenerator()
        solver = get_stage_a_solver()
        
        input_data = generator.generate("forward", "ovr", top_k=5)
        output = solver.solve(input_data)
        
        for solution in output.solutions:
            assert isinstance(solution.rank, int)
            assert isinstance(solution.combo_ids, list)
            assert isinstance(solution.gain_ovr, int)
            assert isinstance(solution.gain_sal, int)
            assert isinstance(solution.gain_ap, int)


# =============================================================================
# STAGE B TESTS
# =============================================================================

class TestStageBInputGenerator:
    """Tests for Stage B input generation."""
    
    def test_generate_from_stage_a_solution(self):
        """Generate input from a Stage A solution."""
        # Create a mock Stage A solution
        solution = StageASolution(
            rank=1,
            combo_ids=[0, 1],  # Use first two combo IDs
            gain_ovr=4,
        )
        
        generator = StageBInputGenerator()
        input_data = generator.generate(solution, "forward", player_limit=50)
        
        assert input_data.position_type == "forward"
        assert input_data.stage_a_solution_rank == 1
        assert len(input_data.combo_ids) == 2
    
    def test_candidate_players_sorted(self):
        """Candidates should be sorted by match_count, then overall."""
        solution = StageASolution(rank=1, combo_ids=[0])
        
        generator = StageBInputGenerator()
        input_data = generator.generate(solution, "forward", player_limit=20)
        
        if len(input_data.players) >= 2:
            # Check sorting: match_count DESC, overall DESC
            for i in range(len(input_data.players) - 1):
                p1 = input_data.players[i]
                p2 = input_data.players[i + 1]
                
                assert (p1.match_count, p1.overall) >= (p2.match_count, p2.overall), \
                    "Players should be sorted by match_count DESC, overall DESC"
    
    def test_player_limit_respected(self):
        """Should not exceed player limit."""
        solution = StageASolution(rank=1, combo_ids=[0, 1, 2])
        
        generator = StageBInputGenerator()
        input_data = generator.generate(solution, "forward", player_limit=10)
        
        assert len(input_data.players) <= 10


class TestStageBSolver:
    """Tests for Stage B mock solver."""
    
    def test_solve_forward_lines(self):
        """Should generate forward lines with 3 players."""
        solver = get_stage_b_solver()
        
        # Create input with some candidate players
        players = [
            CandidatePlayer(
                card_id=i,
                player_id=i * 100,
                team="TOR",
                nationality="CANADA",
                event="BASE",
                overall=85,
                salary=1000,
                match_count=1,
            )
            for i in range(10)
        ]
        
        player_facts = []
        for p in players:
            player_facts.append(f'player({p.card_id}, {p.overall}, "{p.team}", "{p.nationality}", "{p.event}").')
            player_facts.append(f'card_player({p.card_id}, {p.player_id}).')
            player_facts.append(f'salary({p.card_id}, {int(p.salary)}).')
            player_facts.append(f'ap({p.card_id}, {int(p.ap)}).')
        
        input_data = StageBInput(
            position_type="forward",
            stage_a_solution_rank=1,
            combo_ids=[0],
            combo_facts=[],
            players=players,
            player_facts=player_facts,
        )
        
        output = solver.solve(input_data)
        
        assert len(output.lines) > 0
        for line in output.lines:
            assert len(line.player_card_ids) == 3
    
    def test_solve_defense_pairs(self):
        """Should generate defense pairs with 2 players."""
        solver = get_stage_b_solver()
        
        players = [
            CandidatePlayer(
                card_id=i,
                player_id=i * 100,
                team="BOS",
                nationality="USA",
                event="BASE",
                overall=84,
                salary=900,
                match_count=1,
            )
            for i in range(10)
        ]
        
        player_facts = []
        for p in players:
            player_facts.append(f'player({p.card_id}, {p.overall}, "{p.team}", "{p.nationality}", "{p.event}").')
            player_facts.append(f'card_player({p.card_id}, {p.player_id}).')
            player_facts.append(f'salary({p.card_id}, {int(p.salary)}).')
            player_facts.append(f'ap({p.card_id}, {int(p.ap)}).')
        
        input_data = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[0],
            combo_facts=[],
            players=players,
            player_facts=player_facts,
        )
        
        output = solver.solve(input_data)
        
        assert len(output.lines) > 0
        for line in output.lines:
            assert len(line.player_card_ids) == 2


# =============================================================================
# PIPELINE TESTS
# =============================================================================

class TestGoal1Pipeline:
    """Tests for the full Goal 1 pipeline."""
    
    @pytest.fixture
    def cleanup_runs(self):
        """Cleanup any runs created during tests."""
        run_ids = []
        yield run_ids
        
        store = get_results_store()
        for run_id in run_ids:
            try:
                store.delete_run(run_id)
            except Exception:
                pass
    
    def test_pipeline_without_storage(self):
        """Pipeline should work without storing results."""
        result = run_goal1_pipeline(
            "forward",
            "ovr",
            top_k=5,
            player_limit=20,
            store_results=False,
        )
        
        assert result.run_id is None
        assert result.position_type == "forward"
        assert result.optimization_mode == "ovr"
        assert result.stage_a_solutions > 0
        assert result.total_time_ms > 0
    
    def test_pipeline_with_storage(self, cleanup_runs):
        """Pipeline should store results when enabled."""
        result = run_goal1_pipeline(
            "forward",
            "ovr",
            top_k=3,
            player_limit=15,
            store_results=True,
        )
        
        if result.run_id:
            cleanup_runs.append(result.run_id)
        
        assert result.run_id is not None
        
        # Verify results are in database
        store = get_results_store()
        run = store.get_run(result.run_id)
        
        assert run is not None
        assert run.position_type.value == "forward"
        assert run.optimization_mode.value == "ovr"
    
    def test_pipeline_defense(self, cleanup_runs):
        """Pipeline should work for defense position."""
        result = run_goal1_pipeline(
            "defense",
            "sal",
            top_k=3,
            player_limit=15,
            store_results=True,
        )
        
        if result.run_id:
            cleanup_runs.append(result.run_id)
        
        assert result.position_type == "defense"
        assert result.optimization_mode == "sal"
    
    def test_pipeline_combined_mode(self, cleanup_runs):
        """Pipeline should work with combined optimization modes."""
        result = run_goal1_pipeline(
            "forward",
            "ovr_sal",
            top_k=3,
            player_limit=20,
            store_results=True,
        )
        
        if result.run_id:
            cleanup_runs.append(result.run_id)
        
        assert result.optimization_mode == "ovr_sal"
    
    def test_pipeline_result_has_timing(self):
        """Pipeline result should include timing information."""
        result = run_goal1_pipeline(
            "forward",
            "ovr",
            top_k=2,
            player_limit=20,
            store_results=False,
        )
        
        assert result.total_time_ms > 0
        assert result.stage_a_time_ms >= 0
        assert result.stage_b_time_ms >= 0


# =============================================================================
# INTEGRATION TEST
# =============================================================================

class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.fixture
    def cleanup_runs(self):
        """Cleanup any runs created during tests."""
        run_ids = []
        yield run_ids
        
        store = get_results_store()
        for run_id in run_ids:
            try:
                store.delete_run(run_id)
            except Exception:
                pass
    
    def test_full_workflow(self, cleanup_runs):
        """Test complete workflow: run pipeline → query results via endpoint."""
        # Run pipeline
        result = run_goal1_pipeline(
            "forward",
            "ovr",
            top_k=5,
            player_limit=30,
            store_results=True,
        )
        
        if result.run_id:
            cleanup_runs.append(result.run_id)
        
        assert result.run_id is not None
        
        # Query results from store
        store = get_results_store()
        
        # Check Stage A results
        stage_a_results = store.get_stage_a_results(result.run_id)
        assert len(stage_a_results) > 0
        
        # Check Stage B results
        concrete_lines = store.get_concrete_lines(result.run_id, limit=100)
        # Note: May be 0 if mock solver doesn't generate matching lines
        assert concrete_lines is not None
