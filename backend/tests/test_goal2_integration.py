"""
Tests for Goal 2 ASP Integration.

Tests the direct concrete line optimization for interactive goal.
"""

import pytest
from pathlib import Path
import clingo

from src.asp.goal2 import (
    Goal2InputGenerator, ClingoGoal2Solver, get_goal2_solver
)
from src.asp.interfaces import CandidatePlayer, Goal2Input
from src.core.models import ForwardLineCombo, DefenseLineCombo, RewardType


class TestGoal2InputGenerator:
    """Test Goal 2 input generation."""
    
    def test_generate_forward_input(self):
        """Test generating forward line input."""
        # Create mock players
        players = [
            CandidatePlayer(
                card_id=1, player_id=101, team="DET", nationality="USA",
                event="OVR", overall=88, salary=5000.0, ap=10, match_count=2
            ),
            CandidatePlayer(
                card_id=2, player_id=102, team="DET", nationality="USA",
                event="OVR", overall=85, salary=4500.0, ap=8, match_count=1
            ),
            CandidatePlayer(
                card_id=3, player_id=103, team="DET", nationality="CAN",
                event="OVR", overall=83, salary=4000.0, ap=5, match_count=1
            ),
        ]
        
        gen = Goal2InputGenerator()
        
        input_data = gen.generate(
            position_type="forward",
            optimization_target="ovr",
            players=players,
            num_solutions=5
        )
        
        assert input_data.position_type == "forward"
        assert input_data.optimization_target == "ovr"
        assert len(input_data.players) == 3
        assert len(input_data.player_facts) > 0
        assert input_data.num_solutions == 5
    
    def test_generate_defense_input(self):
        """Test generating defense pair input."""
        players = [
            CandidatePlayer(
                card_id=10, player_id=201, team="DET", nationality="USA",
                event="OVR", overall=86, salary=5500.0, ap=12, match_count=2
            ),
            CandidatePlayer(
                card_id=11, player_id=202, team="DET", nationality="CAN",
                event="OVR", overall=84, salary=5000.0, ap=10, match_count=1
            ),
        ]
        
        gen = Goal2InputGenerator()
        
        input_data = gen.generate(
            position_type="defense",
            optimization_target="sal",
            players=players,
            num_solutions=3
        )
        
        assert input_data.position_type == "defense"
        assert input_data.optimization_target == "sal"
        assert len(input_data.players) == 2
    
    def test_player_facts_generation(self):
        """Test that player facts are generated correctly."""
        players = [
            CandidatePlayer(
                card_id=5, player_id=501, team="TOR", nationality="FIN",
                event="TOTW", overall=90, salary=6000.0, ap=15
            ),
        ]
        
        gen = Goal2InputGenerator()
        facts = gen._generate_player_facts(players)
        
        # Should have multiple facts per player: player(), ovr(), salary_val(), ap_val(), card_player()
        assert len(facts) >= 5
        assert any("player(" in f and "5," in f for f in facts)
        assert any("ovr(" in f and "5," in f for f in facts)
        assert any("salary_val(" in f for f in facts)
        assert any("ap_val(" in f for f in facts)


class TestGoal2CLINGOSolver:
    """Test Goal 2 Clingo solver."""
    
    @pytest.fixture
    def solver(self):
        """Get Goal 2 solver instance."""
        try:
            return ClingoGoal2Solver()
        except RuntimeError:
            pytest.skip("Clingo not available")
    
    @pytest.fixture
    def simple_forward_input(self):
        """Create simple forward line test input."""
        players = [
            CandidatePlayer(
                card_id=1, player_id=101, team="DET", nationality="USA",
                event="OVR", overall=88, salary=5000.0, ap=10
            ),
            CandidatePlayer(
                card_id=2, player_id=102, team="DET", nationality="USA",
                event="OVR", overall=85, salary=4500.0, ap=8
            ),
            CandidatePlayer(
                card_id=3, player_id=103, team="DET", nationality="CAN",
                event="OVR", overall=83, salary=4000.0, ap=5
            ),
            CandidatePlayer(
                card_id=4, player_id=104, team="TOR", nationality="USA",
                event="OVR", overall=87, salary=5200.0, ap=9
            ),
        ]
        
        return Goal2Input(
            position_type="forward",
            optimization_target="ovr",
            players=players,
            player_facts=[
                'player(1, 101, "USA", "DET", "OVR", 88, 5000).',
                'player(2, 102, "USA", "DET", "OVR", 85, 4500).',
                'player(3, 103, "CAN", "DET", "OVR", 83, 4000).',
                'player(4, 104, "USA", "TOR", "OVR", 87, 5200).',
                'ovr(1, 88). ovr(2, 85). ovr(3, 83). ovr(4, 87).',
                'salary_val(1, 5000). salary_val(2, 4500). salary_val(3, 4000). salary_val(4, 5200).',
                'ap_val(1, 10). ap_val(2, 8). ap_val(3, 5). ap_val(4, 9).',
                'card_player(1, 101). card_player(2, 102). card_player(3, 103). card_player(4, 104).',
            ],
            combo_facts=[],
            num_solutions=5,
        )
    
    @pytest.fixture
    def simple_defense_input(self):
        """Create simple defense pair test input."""
        players = [
            CandidatePlayer(
                card_id=10, player_id=201, team="DET", nationality="USA",
                event="OVR", overall=86, salary=5500.0, ap=12
            ),
            CandidatePlayer(
                card_id=11, player_id=202, team="DET", nationality="CAN",
                event="OVR", overall=84, salary=5000.0, ap=10
            ),
            CandidatePlayer(
                card_id=12, player_id=203, team="TOR", nationality="USA",
                event="OVR", overall=85, salary=5300.0, ap=11
            ),
        ]
        
        return Goal2Input(
            position_type="defense",
            optimization_target="ovr",
            players=players,
            player_facts=[
                'player(10, 201, "USA", "DET", "OVR", 86, 5500).',
                'player(11, 202, "CAN", "DET", "OVR", 84, 5000).',
                'player(12, 203, "USA", "TOR", "OVR", 85, 5300).',
                'ovr(10, 86). ovr(11, 84). ovr(12, 85).',
                'salary_val(10, 5500). salary_val(11, 5000). salary_val(12, 5300).',
                'ap_val(10, 12). ap_val(11, 10). ap_val(12, 11).',
                'card_player(10, 201). card_player(11, 202). card_player(12, 203).',
            ],
            combo_facts=[],
            num_solutions=3,
        )
    
    def test_solver_available(self, solver):
        """Test that solver is available."""
        assert solver is not None
    
    def test_forward_line_solve_basic(self, solver, simple_forward_input):
        """Test basic forward line solving."""
        # This test just verifies the solver doesn't crash
        # Actual solution validation depends on ASP files being present
        try:
            output = solver.solve(simple_forward_input)
            assert output is not None
            assert hasattr(output, 'lines')
            assert hasattr(output, 'solve_time_ms')
        except FileNotFoundError:
            # ASP rule files might not exist yet, which is expected
            pytest.skip("G2 ASP rule files not available yet")
    
    def test_defense_line_solve_basic(self, solver, simple_defense_input):
        """Test basic defense pair solving."""
        try:
            output = solver.solve(simple_defense_input)
            assert output is not None
            assert hasattr(output, 'lines')
        except FileNotFoundError:
            pytest.skip("G2 ASP rule files not available yet")


class TestGoal2ASPRules:
    """Test Goal 2 ASP rules directly with Clingo."""
    
    def solve_g2(self, rules_dir, files, facts="", ctl_opts=None):
        """
        Solve Goal 2 ASP problem.
        
        Args:
            rules_dir: Path to ASP rules directory (e.g., "src/asp/g2")
            files: List of rule filenames
            facts: Extra facts to add
            ctl_opts: Clingo control options
            
        Returns:
            (result, models, models_count)
        """
        try:
            current_dir = Path(__file__).parent.resolve()
            backend_root = current_dir.parent
            asp_root = backend_root / "src" / "asp" / "g2"
            
            resolved_files = []
            for f in files:
                full_path = asp_root / f
                if not full_path.exists():
                    raise FileNotFoundError(f"Could not find ASP file: {full_path}")
                resolved_files.append(str(full_path))
            
            opts = list(ctl_opts or [])
            ctl = clingo.Control(opts)
            
            for f in resolved_files:
                ctl.load(f)
            
            if facts.strip():
                ctl.add("base", [], facts)
                ctl.ground([("base", [])])
            else:
                ctl.ground([("base", [])])
            
            models = []
            models_c = 0
            
            def on_model(m):
                nonlocal models_c
                models_c += 1
                models.append(m.symbols(shown=True))
            
            res = ctl.solve(on_model=on_model)
            return res, models, models_c
        except ImportError:
            return None, [], 0
    
    def test_forward_line_formation(self):
        """Test that forward lines are formed correctly."""
        facts = """
        % Forward players with attributes
        player(1, 101, "USA", "DET", "OVR", 88, 5000).
        player(2, 102, "USA", "DET", "OVR", 85, 4500).
        player(3, 103, "CAN", "DET", "OVR", 83, 4000).
        
        % Dummy weight for optimization
        #const w_ovr=1.
        """
        
        try:
            res, models, count = self.solve_g2(
                "src/asp/g2",
                ["common.lp", "fwd_main.lp"],
                facts,
                ["0"]
            )
            
            if res is None:
                pytest.skip("Clingo not available")
            
            # Should have at least one model if satisfiable
            if res.satisfiable:
                assert count > 0
                # Check that we have forward_line facts
                found_forward_line = False
                for model in models:
                    for symbol in model:
                        if symbol.name == "forward_line":
                            found_forward_line = True
                            break
                assert found_forward_line, "No forward_line facts found"
        
        except FileNotFoundError:
            pytest.skip("G2 ASP rule files not available")
    
    def test_defense_line_formation(self):
        """Test that defense lines are formed correctly."""
        facts = """
        % Defense players
        player(10, 201, "USA", "DET", "OVR", 86, 5500).
        player(11, 202, "CAN", "DET", "OVR", 84, 5000).
        
        #const w_ovr=1.
        """
        
        try:
            res, models, count = self.solve_g2(
                "src/asp/g2",
                ["common.lp", "def_main.lp"],
                facts,
                ["0"]
            )
            
            if res is None:
                pytest.skip("Clingo not available")
            
            if res.satisfiable:
                assert count > 0
                found_defense_line = False
                for model in models:
                    for symbol in model:
                        if symbol.name == "defense_line":
                            found_defense_line = True
                            break
                assert found_defense_line, "No defense_line facts found"
        
        except FileNotFoundError:
            pytest.skip("G2 ASP rule files not available")


class TestGoal2Integration:
    """Integration tests for Goal 2 pipeline."""
    
    def test_input_generator_with_realistic_data(self):
        """Test input generation with realistic player data."""
        players = [
            CandidatePlayer(
                card_id=i, player_id=1000+i, team="DET", nationality="USA",
                event="OVR", overall=85+i, salary=5000+i*100, ap=10+i
            )
            for i in range(10)
        ]
        
        gen = Goal2InputGenerator()
        input_data = gen.generate(
            position_type="forward",
            optimization_target="ovr",
            players=players,
            num_solutions=10
        )
        
        assert input_data is not None
        assert len(input_data.players) == 10
        assert len(input_data.player_facts) > 0
    
    def test_goal2_solver_factory(self):
        """Test that solver factory returns valid solver."""
        solver = get_goal2_solver()
        assert solver is not None
        assert hasattr(solver, 'solve')
