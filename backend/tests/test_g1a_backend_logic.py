import pytest
from unittest.mock import MagicMock, patch
from src.asp.stage_a import StageAInputGenerator, ClingoStageASolver
from src.asp.interfaces import StageAInput
from src.core.models import DefenseLineCombo, RewardType, ComboCondition

class TestG1ABackendLogic:
    """
    Tests G1A logic by going through the Stage A Input Generator and Solver.
    Mirrors the logic tests in test_asp_g1a.py but uses the application domain objects.
    """
    
    @pytest.fixture
    def mock_loader(self):
        with patch("src.asp.stage_a.get_data_loader") as mock:
            yield mock

    def create_def_combo(self, id, reward, r_type, c1_type, c1_key, c2_type, c2_key):
        return DefenseLineCombo(
            id=id,
            reward_amount=reward,
            reward_type=r_type,
            condition1=ComboCondition(type=c1_type, key=c1_key),
            condition2=ComboCondition(type=c2_type, key=c2_key)
        )

    def test_backend_conflicting_combos(self, mock_loader):
        """
        Mirror of test_conflicting_combos.
        Two combos that require disjoint events for the same slots.
        Since players can only have 1 event, we can't satisfy both.
        """
        # Combo 1: Event A, Event B (Reward 10)
        # Combo 2: Event C, Event D (Reward 10)
        # Defense line has 2 players.
        # P1 needs Event A (for C1) or Event C (for C2). Can't have both.
        
        combos = [
            self.create_def_combo(1, 10, RewardType.AP, "event", "A", "event", "B"),
            self.create_def_combo(2, 10, RewardType.AP, "event", "C", "event", "D")
        ]
        
        mock_loader.return_value.get_defense_combos.return_value = combos
        
        generator = StageAInputGenerator()
        solver = ClingoStageASolver()
        
        input_data = generator.generate("defense", "ap", top_k=5)
        output = solver.solve(input_data)
        
        # Should pick one combo (Reward 10), not both (20).
        assert len(output.solutions) > 0
        best_sol = output.solutions[0]
        assert best_sol.total_reward == 10
        assert len(best_sol.active_combos) == 1

    def test_backend_redundant_combos(self, mock_loader):
        """
        Mirror of test_redundant_combo_definitions.
        Two combos with IDENTICAL conditions but different IDs.
        Should both activate if conditions are met.
        """
        # Combo 1: Event A, Event B (Reward 10)
        # Combo 2: Event A, Event B (Reward 5)
        
        combos = [
            self.create_def_combo(1, 10, RewardType.AP, "event", "A", "event", "B"),
            self.create_def_combo(2, 5, RewardType.AP, "event", "A", "event", "B")
        ]
        
        mock_loader.return_value.get_defense_combos.return_value = combos
        
        generator = StageAInputGenerator()
        solver = ClingoStageASolver()
        
        input_data = generator.generate("defense", "ap", top_k=5)
        output = solver.solve(input_data)
        
        # Should activate BOTH. Total reward 15.
        assert len(output.solutions) > 0
        best_sol = output.solutions[0]
        assert best_sol.total_reward == 15
        assert len(best_sol.active_combos) == 2
        
        ids = [c.combo_id for c in best_sol.active_combos]
        assert 1 in ids
        assert 2 in ids

    def test_backend_multiplier_weights(self, mock_loader):
        """
        Mirror of test_multiplier_logic.
        Different weights should change the optimal solution.
        """
        # Combo 1: OVR Reward 10 (Event A, B)
        # Combo 2: SAL Reward 5 (Event C, D)
        # Conflict: Can't have both (disjoint events)
        
        c1 = self.create_def_combo(1, 10, RewardType.OVR, "event", "A", "event", "B")
        c2 = self.create_def_combo(2, 5, RewardType.SAL, "event", "C", "event", "D")
        
        mock_loader.return_value.get_defense_combos.return_value = [c1, c2]
        
        generator = StageAInputGenerator()
        solver = ClingoStageASolver()
        
        # Case 1: Optimize OVR (Default weights: OVR=1, SAL=0)
        # Should pick Combo 1 (Reward 10 * 1 = 10) vs Combo 2 (Reward 5 * 0 = 0)
        input_ovr = generator.generate("defense", "ovr", top_k=1)
        out_ovr = solver.solve(input_ovr)
        assert out_ovr.solutions[0].total_reward == 10
        assert out_ovr.solutions[0].active_combos[0].combo_id == 1
        
        # Case 2: Optimize SAL (Weights: OVR=0, SAL=1)
        # Should pick Combo 2 (Reward 5 * 1 = 5) vs Combo 1 (Reward 10 * 0 = 0)
        input_sal = generator.generate("defense", "sal", top_k=1)
        out_sal = solver.solve(input_sal)
        assert out_sal.solutions[0].total_reward == 5
        assert out_sal.solutions[0].active_combos[0].combo_id == 2
        
        # Case 3: Optimize OVR_SAL (Weights: OVR=2, SAL=1 for Defense)
        # Combo 1 Value: 10 * 2 = 20
        # Combo 2 Value: 5 * 1 = 5
        # Should pick Combo 1.
        input_both = generator.generate("defense", "ovr_sal", top_k=1)
        out_both = solver.solve(input_both)
        # Total reward is calculated as sum(R * M). 
        # C1: 10 * 2 = 20.
        assert out_both.solutions[0].total_reward == 20
        assert out_both.solutions[0].active_combos[0].combo_id == 1

