import pytest
from unittest.mock import MagicMock, patch
from src.asp.stage_a import StageAInputGenerator, ClingoStageASolver
from src.asp.interfaces import StageAInput
from src.core.models import ForwardLineCombo, DefenseLineCombo, RewardType, ComboCondition

class TestStageAExtended:
    
    @pytest.fixture
    def mock_loader(self):
        with patch("src.asp.stage_a.get_data_loader") as mock:
            yield mock

    # =========================================================================
    # INPUT GENERATOR TESTS
    # =========================================================================

    def test_generator_weights_ovr(self, mock_loader):
        """Test that OVR mode sets correct weights (1, 0, 0)."""
        generator = StageAInputGenerator()
        input_data = generator.generate("forward", "ovr")
        
        assert input_data.ovr_weight == 1.0
        assert input_data.sal_weight == 0.0
        assert input_data.ap_weight == 0.0

    def test_generator_weights_mixed(self, mock_loader):
        """Test that OVR_SAL_AP mode sets all weights."""
        generator = StageAInputGenerator()
        input_data = generator.generate("forward", "ovr_sal_ap")
        
        # Based on implementation: Forward base_ovr=3.0, base_sal=1.0, base_ap=1.0
        assert input_data.ovr_weight == 3.0
        assert input_data.sal_weight == 1.0
        assert input_data.ap_weight == 1.0

    def test_generator_filtering(self, mock_loader):
        """Test that facts are filtered by optimization mode."""
        generator = StageAInputGenerator()
        
        # Mock combos
        mock_loader.return_value.get_forward_combos.return_value = [
            ForwardLineCombo(
                id=1, reward_amount=1, reward_type=RewardType.OVR,
                condition1=ComboCondition(type="team", key="DET"),
                condition2=ComboCondition(type="team", key="DET"),
                condition3=ComboCondition(type="team", key="DET")
            ),
            ForwardLineCombo(
                id=2, reward_amount=1, reward_type=RewardType.AP,
                condition1=ComboCondition(type="team", key="TOR"),
                condition2=ComboCondition(type="team", key="TOR"),
                condition3=ComboCondition(type="team", key="TOR")
            )
        ]
        
        # Generate for OVR only
        input_data = generator.generate("forward", "ovr")
        assert len(input_data.combo_facts) == 1
        assert "OVR" in input_data.combo_facts[0]
        assert "AP" not in input_data.combo_facts[0]

    # =========================================================================
    # SOLVER EXTENDED TESTS
    # =========================================================================

    def test_solve_mixed_rewards(self, mock_loader):
        """Test solving with multiple reward types active."""
        solver = ClingoStageASolver()
        
        # 1. OVR Combo: DET+DET
        # 2. AP Combo: DET+TOR
        combo_facts = [
            'defense_combo(1, 5, "OVR", team("DET"), team("DET")).',
            'defense_combo(2, 5, "AP", team("DET"), team("TOR")).'
        ]
        
        input_data = StageAInput(
            position_type="defense",
            optimization_mode="ovr_sal_ap",
            combo_facts=combo_facts,
            top_k=5,
            ovr_weight=1.0,
            sal_weight=0.0,
            ap_weight=1.0
        )
        
        output = solver.solve(input_data)
        
        # Should find solutions
        assert len(output.solutions) > 0
        best_sol = output.solutions[0]
        
        has_ovr_gain = any(s.gain_ovr > 0 for s in output.solutions)
        has_ap_gain = any(s.gain_ap > 0 for s in output.solutions)
        
        assert has_ovr_gain
        assert has_ap_gain

    def test_solve_empty_combos(self, mock_loader):
        """Test solver behavior with no combos provided."""
        solver = ClingoStageASolver()
        
        input_data = StageAInput(
            position_type="forward",
            optimization_mode="ovr",
            combo_facts=[], # Empty
            top_k=5,
            ovr_weight=1.0,
            sal_weight=1.0,
            ap_weight=1.0
        )
        
        output = solver.solve(input_data)
        
        # With no combos, total_reward is 0.
        # target_threshold_lookup.lp requires total_reward >= 1.
        # So we expect 0 solutions.
        
        assert len(output.solutions) == 0

    def test_attribute_string_parsing(self, mock_loader):
        """Test that string values in attributes are parsed correctly."""
        solver = ClingoStageASolver()
        
        # Combo with string containing space or special chars
        # NOTE: Clingo string syntax uses double quotes.
        # When passed as python string fact: '... event("Happy Hour") ...'
        combo_facts = [
            'defense_combo(1, 5, "OVR", event("Happy Hour"), nationality("USA")).'
        ]
        
        input_data = StageAInput(
            position_type="defense",
            optimization_mode="ovr",
            combo_facts=combo_facts,
            top_k=1,
            ovr_weight=1.0,
            sal_weight=0,
            ap_weight=0
        )
        
        output = solver.solve(input_data)
        
        # If no solutions found, fail with informative message
        assert len(output.solutions) > 0, f"No solutions found. Models: {output.total_models_found}"
        
        # Check first solution
        sol = output.solutions[0]
        
        # Should have attribute with value "Happy Hour"
        events = [p.attr_value for p in sol.player_attrs if p.attr_type == "event"]
        assert "Happy Hour" in events
        
    def test_defense_symmetry_breaking(self, mock_loader):
        """
        Verify we don't get mirror image duplicate solutions.
        E.g. P1=DET, P2=TOR vs P1=TOR, P2=DET
        """
        solver = ClingoStageASolver()
        
        combo_facts = [
            'defense_combo(1, 1, "OVR", team("DET"), team("TOR")).'
        ]
        
        input_data = StageAInput(
            position_type="defense",
            optimization_mode="ovr",
            combo_facts=combo_facts,
            top_k=10,
            ovr_weight=1.0,
            sal_weight=0,
            ap_weight=0
        )
        
        output = solver.solve(input_data)
        
        # We expect exactly 1 solution with gain 1.
        solutions_with_gain = [s for s in output.solutions if s.total_gain > 0]
        assert len(solutions_with_gain) == 1
