"""
Unit tests for Goal 2 solver components.

Tests individual components of the Goal 2 optimization pipeline.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.asp.goal2 import (
    Goal2InputGenerator,
    ClingoGoal2Solver,
)
from src.asp.goal2_pipeline import (
    Goal2Pipeline,
    Goal2PipelineResult,
)
from src.asp.interfaces import (
    CandidatePlayer,
    Goal2Input,
    Goal2Output,
    Goal2ConcreteLineResult,
)


class TestGoal2InputGeneratorWeights:
    """Test weight calculation in Goal 2 input generator."""
    
    def test_ovr_weights(self):
        """Test OVR optimization weights."""
        gen = Goal2InputGenerator()
        ovr_w, sal_w, ap_w = gen._get_weights("forward", "ovr")
        
        assert ovr_w == 1.0
        assert sal_w == 0.0
        assert ap_w == 0.0
    
    def test_sal_weights(self):
        """Test SAL optimization weights."""
        gen = Goal2InputGenerator()
        ovr_w, sal_w, ap_w = gen._get_weights("defense", "sal")
        
        assert ovr_w == 0.0
        assert sal_w == 1.0
        assert ap_w == 0.0
    
    def test_ap_weights(self):
        """Test AP optimization weights."""
        gen = Goal2InputGenerator()
        ovr_w, sal_w, ap_w = gen._get_weights("forward", "ap")
        
        assert ovr_w == 0.0
        assert sal_w == 0.0
        assert ap_w == 1.0
    
    def test_combined_ovr_sal_weights(self):
        """Test OVR+SAL combined weights."""
        gen = Goal2InputGenerator()
        
        # Forward position
        ovr_w, sal_w, ap_w = gen._get_weights("forward", "ovr_sal")
        assert ovr_w == 3.0  # base_ovr for forward
        assert sal_w == 1.0
        assert ap_w == 0.0
        
        # Defense position
        ovr_w, sal_w, ap_w = gen._get_weights("defense", "ovr_sal")
        assert ovr_w == 2.0  # base_ovr for defense
        assert sal_w == 1.0
        assert ap_w == 0.0
    
    def test_combined_all_weights(self):
        """Test all-metrics combined weights."""
        gen = Goal2InputGenerator()
        ovr_w, sal_w, ap_w = gen._get_weights("forward", "ovr_sal_ap")
        
        assert ovr_w == 3.0
        assert sal_w == 1.0
        assert ap_w == 1.0


class TestGoal2InputGeneratorFacts:
    """Test fact generation in Goal 2 input generator."""
    
    def test_forward_combo_facts(self):
        """Test forward combo fact generation."""
        gen = Goal2InputGenerator()
        
        # Create mock combos
        combo = Mock()
        combo.id = 1
        combo.reward_amount = 5
        combo.reward_type = Mock(value="OVR")
        combo.condition1 = Mock(type="team", key="DET")
        combo.condition2 = Mock(type="event", key="HH")
        combo.condition3 = Mock(type="nationality", key="USA")
        
        combos = [combo]
        facts = gen._generate_combo_facts(combos, "forward")
        
        assert len(facts) == 1
        fact = facts[0]
        assert "fwd_combo" in fact
        assert "1," in fact  # combo ID
        assert "5," in fact  # reward amount
        assert '"OVR"' in fact  # reward type
        assert 'team("DET")' in fact
        assert 'event("HH")' in fact
        assert 'nationality("USA")' in fact
    
    def test_defense_combo_facts(self):
        """Test defense combo fact generation."""
        gen = Goal2InputGenerator()
        
        combo = Mock()
        combo.id = 2
        combo.reward_amount = 3
        combo.reward_type = Mock(value="SAL")
        combo.condition1 = Mock(type="team", key="TOR")
        combo.condition2 = Mock(type="nationality", key="CAN")
        
        combos = [combo]
        facts = gen._generate_combo_facts(combos, "defense")
        
        assert len(facts) == 1
        fact = facts[0]
        assert "def_combo" in fact
        assert "2," in fact
        assert "3," in fact
        assert '"SAL"' in fact
        assert 'team("TOR")' in fact
        assert 'nationality("CAN")' in fact


class TestGoal2SolverParsing:
    """Test Goal 2 solver model parsing."""
    
    @pytest.fixture
    def mock_solver(self):
        """Create a mock Goal 2 solver for testing."""
        with patch('src.asp.goal2.get_data_loader'):
            return ClingoGoal2Solver()
    
    def test_parse_line_model_forward(self, mock_solver):
        """Test parsing forward line from Clingo model."""
        # Mock player data
        input_data = Goal2Input(
            position_type="forward",
            optimization_target="ovr",
            players=[
                CandidatePlayer(
                    card_id=1, player_id=101, team="DET",
                    nationality="USA", event="OVR", overall=88, salary=5000, ap=10
                ),
                CandidatePlayer(
                    card_id=2, player_id=102, team="DET",
                    nationality="USA", event="OVR", overall=85, salary=4500, ap=8
                ),
                CandidatePlayer(
                    card_id=3, player_id=103, team="DET",
                    nationality="CAN", event="OVR", overall=83, salary=4000, ap=5
                ),
            ],
            player_facts=[],
            combo_facts=[],
            num_solutions=5,
        )
        
        # Create mock model symbols
        select_1 = Mock()
        select_1.name = "select"
        select_1.arguments = [Mock(number=1), Mock(number=1)]
        
        select_2 = Mock()
        select_2.name = "select"
        select_2.arguments = [Mock(number=2), Mock(number=2)]
        
        select_3 = Mock()
        select_3.name = "select"
        select_3.arguments = [Mock(number=3), Mock(number=3)]
        
        total_ovr = Mock()
        total_ovr.name = "total_base_ovr"
        total_ovr.arguments = [Mock(number=256)]  # 88+85+83
        
        model_symbols = [select_1, select_2, select_3, total_ovr]
        
        line = mock_solver._parse_line_model(model_symbols, input_data)
        
        assert line is not None
        assert line.player_card_ids == [1, 2, 3]
        assert line.player_ids == [101, 102, 103]
        assert line.total_base_ovr == 256
    
    def test_parse_line_model_defense(self, mock_solver):
        """Test parsing defense line from Clingo model."""
        input_data = Goal2Input(
            position_type="defense",
            optimization_target="ovr",
            players=[
                CandidatePlayer(
                    card_id=10, player_id=201, team="DET",
                    nationality="USA", event="OVR", overall=86, salary=5500, ap=12
                ),
                CandidatePlayer(
                    card_id=11, player_id=202, team="DET",
                    nationality="CAN", event="OVR", overall=84, salary=5000, ap=10
                ),
            ],
            player_facts=[],
            combo_facts=[],
            num_solutions=3,
        )
        
        select_1 = Mock()
        select_1.name = "select"
        select_1.arguments = [Mock(number=10), Mock(number=1)]
        
        select_2 = Mock()
        select_2.name = "select"
        select_2.arguments = [Mock(number=11), Mock(number=2)]
        
        total_ovr = Mock()
        total_ovr.name = "total_base_ovr"
        total_ovr.arguments = [Mock(number=170)]  # 86+84
        
        model_symbols = [select_1, select_2, total_ovr]
        
        line = mock_solver._parse_line_model(model_symbols, input_data)
        
        assert line is not None
        assert line.player_card_ids == [10, 11]
        assert line.player_ids == [201, 202]
        assert line.total_base_ovr == 170
    
    def test_parse_line_model_incomplete(self, mock_solver):
        """Test parsing incomplete model returns None."""
        input_data = Goal2Input(
            position_type="forward",
            optimization_target="ovr",
            players=[
                CandidatePlayer(
                    card_id=1, player_id=101, team="DET",
                    nationality="USA", event="OVR", overall=88, salary=5000, ap=10
                ),
            ],
            player_facts=[],
            combo_facts=[],
            num_solutions=5,
        )
        
        # Only one selection for a forward line (needs 3)
        select_1 = Mock()
        select_1.name = "select"
        select_1.arguments = [Mock(number=1), Mock(number=1)]
        
        model_symbols = [select_1]
        
        line = mock_solver._parse_line_model(model_symbols, input_data)
        
        assert line is None


class TestGoal2Pipeline:
    """Test Goal 2 pipeline orchestration."""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create mock pipeline."""
        mock_solver = Mock()
        mock_solver.solve = Mock(return_value=Goal2Output(lines=[], solve_time_ms=100.0))
        
        with patch('src.asp.goal2_pipeline.get_data_loader'):
            return Goal2Pipeline(solver=mock_solver)
    
    def test_pipeline_run_forward(self, mock_pipeline):
        """Test pipeline execution for forward lines."""
        players = [
            CandidatePlayer(
                card_id=i, player_id=100+i, team="DET",
                nationality="USA", event="OVR", overall=85+i, salary=5000+i*100, ap=10
            )
            for i in range(3)
        ]
        
        result = mock_pipeline.run(
            position_type="forward",
            optimization_target="ovr",
            players=players,
            num_solutions=5
        )
        
        assert isinstance(result, Goal2PipelineResult)
        assert result.position_type == "forward"
        assert result.optimization_target == "ovr"
        assert result.num_lines_found == 0
        assert result.total_time_ms > 0
    
    def test_pipeline_run_defense(self, mock_pipeline):
        """Test pipeline execution for defense lines."""
        players = [
            CandidatePlayer(
                card_id=i, player_id=200+i, team="DET",
                nationality="USA", event="OVR", overall=85+i, salary=5000+i*100, ap=10
            )
            for i in range(2)
        ]
        
        result = mock_pipeline.run(
            position_type="defense",
            optimization_target="sal",
            players=players,
            num_solutions=3
        )
        
        assert result.position_type == "defense"
        assert result.optimization_target == "sal"
    
    def test_pipeline_with_combo_ids(self, mock_pipeline):
        """Test pipeline with specific combo IDs to enforce."""
        players = [
            CandidatePlayer(
                card_id=i, player_id=100+i, team="DET",
                nationality="USA", event="OVR", overall=85, salary=5000, ap=10
            )
            for i in range(3)
        ]
        
        combo_ids = [1, 2, 3]
        
        result = mock_pipeline.run(
            position_type="forward",
            optimization_target="ovr",
            players=players,
            combo_ids=combo_ids,
            num_solutions=10
        )
        
        assert result is not None
        # Verify solver was called
        assert mock_pipeline.solver.solve.called


class TestGoal2ConcreteLineResult:
    """Test Goal2ConcreteLineResult data class."""
    
    def test_totals_without_bonus(self):
        """Test totals calculation without bonus."""
        line = Goal2ConcreteLineResult(
            rank=1,
            player_card_ids=[1, 2, 3],
            player_ids=[101, 102, 103],
            activated_combo_ids=[],
            total_base_ovr=256,
            total_base_salary=13500.0,
            total_base_ap=23,
            ovr_bonus=0,
            sal_bonus=0,
            ap_bonus=0,
        )
        
        assert line.total_ovr == 256
        assert line.total_salary == 13500.0
        assert line.total_ap == 23
    
    def test_totals_with_bonus(self):
        """Test totals calculation with bonus."""
        line = Goal2ConcreteLineResult(
            rank=1,
            player_card_ids=[1, 2, 3],
            player_ids=[101, 102, 103],
            activated_combo_ids=[1, 2],
            total_base_ovr=256,
            total_base_salary=13500.0,
            total_base_ap=23,
            ovr_bonus=5,
            sal_bonus=100,
            ap_bonus=2,
        )
        
        assert line.total_ovr == 261  # 256 + 5
        assert line.total_salary == 13400.0  # 13500 - 100
        assert line.total_ap == 21  # 23 - 2


class TestGoal2EdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_player_list(self):
        """Test handling of empty player list."""
        gen = Goal2InputGenerator()
        
        input_data = gen.generate(
            position_type="forward",
            optimization_target="ovr",
            players=[],
            num_solutions=5
        )
        
        assert input_data is not None
        assert len(input_data.players) == 0
        assert len(input_data.player_facts) == 0
    
    def test_single_player(self):
        """Test with single player (invalid for lines)."""
        players = [
            CandidatePlayer(
                card_id=1, player_id=101, team="DET",
                nationality="USA", event="OVR", overall=88, salary=5000, ap=10
            )
        ]
        
        gen = Goal2InputGenerator()
        
        input_data = gen.generate(
            position_type="forward",
            optimization_target="ovr",
            players=players,
            num_solutions=5
        )
        
        assert input_data is not None
        assert len(input_data.players) == 1
