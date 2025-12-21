import pytest
from unittest.mock import MagicMock, patch
from src.asp.stage_a import ClingoStageASolver
from src.asp.interfaces import StageAInput

class TestASPIntegration:
    @pytest.fixture
    def mock_loader(self):
        with patch("src.asp.stage_a.get_data_loader") as mock:
            yield mock

    def test_solve_defense_integration(self, mock_loader):
        solver = ClingoStageASolver()
        
        # Define some simple defense facts
        # Defense requires 2 players.
        # Let's create a scenario where we have two combos.
        # Combo 1: Req A, Req B. Reward 5.
        # Combo 2: Req A, Req C. Reward 3.
        # If we pick players satisfying A, B, C, we might get both?
        
        combo_facts = [
            'defense_combo(1, 5, "AP", team("DET"), event("HH")).',
            'defense_combo(2, 3, "AP", team("DET"), nationality("USA")).'
        ]
        
        input_data = StageAInput(
            position_type="defense",
            optimization_mode="ap",
            combo_facts=combo_facts,
            top_k=5,
            ovr_weight=0,
            sal_weight=0,
            ap_weight=1.0
        )
        
        output = solver.solve(input_data)
        
        assert len(output.solutions) == 3
        
        # We expect solutions.
        # Verify structure of the first (best) solution
        best_sol = output.solutions[0]
        assert best_sol.rank == 1
        assert best_sol.total_gain > 0
        assert len(best_sol.active_combos) > 0
        assert len(best_sol.player_attrs) > 0
        
        # Verify sorting
        scores = [s.total_gain for s in output.solutions]
        assert scores == sorted(scores, reverse=True)
        
        # Verify specific content of best solution if possible
        # With DET/HH and DET/USA, we could pick DET, HH, USA players.
        # Wait, defense line has 2 players.
        # P1: DET, HH. P2: DET, USA.
        # Matches Combo 1 (P1+P2? No, combo entries are 1 and 2).
        # Combo 1 needs Team DET and Event HH.
        # Combo 2 needs Team DET and Nationality USA.
        # If P1=DET,HH and P2=DET,USA.
        # Combo 1 satisfied?
        # Defense combo active logic:
        # def_active_combo(ID, R, T) :- defense_combo_sorted(ID, R, T, Entry1, Entry2), match(1, Entry1), match(2, Entry2).
        # So P1 must match Entry1 and P2 match Entry2 (after sorting).
        # We don't know the sort order of attributes easily without running clingo, but likely Team < Event < Nationality?
        # Anyway, we just check we got results.

    def test_solve_forward_integration(self, mock_loader):
        solver = ClingoStageASolver()
        
        # Forward line: 3 players
        combo_facts = [
             'forward_combo(10, 10, "OVR", team("DET"), event("HH"), nationality("SWE")).',
             'forward_combo(11, 5, "OVR", team("DET"), event("HH"), team("TOR")).'
        ]
        
        input_data = StageAInput(
            position_type="forward",
            optimization_mode="ovr",
            combo_facts=combo_facts,
            top_k=10,
            ovr_weight=1.0,
            sal_weight=0,
            ap_weight=0
        )
        
        output = solver.solve(input_data)
        
        assert len(output.solutions) > 0
        best_sol = output.solutions[0]
        assert best_sol.total_gain > 0
        
        # Check active combos in solution
        # We expect at least one combo to be active if feasible
        found_active = False
        for sol in output.solutions:
            if len(sol.active_combos) > 0:
                found_active = True
                break
        assert found_active

    def test_weights_handling(self, mock_loader):
        solver = ClingoStageASolver()
        
        # Two combos, one AP, one OVR.
        # If we weight AP high, AP combo should appear in top solutions.
        combo_facts = [
            'defense_combo(1, 10, "AP", team("A"), team("B")).',
            'defense_combo(2, 10, "OVR", team("C"), team("D")).'
        ]
        
        # Optimize AP
        input_ap = StageAInput(
            position_type="defense",
            optimization_mode="ap",
            combo_facts=combo_facts,
            top_k=1,
            ovr_weight=0,
            sal_weight=0,
            ap_weight=1.0
        )
        out_ap = solver.solve(input_ap)
        # Should prefer AP combo or have higher AP gain
        assert out_ap.solutions[0].gain_ap > 0
        
        # Optimize OVR
        input_ovr = StageAInput(
            position_type="defense",
            optimization_mode="ovr",
            combo_facts=combo_facts,
            top_k=1,
            ovr_weight=1.0,
            sal_weight=0,
            ap_weight=0
        )
        out_ovr = solver.solve(input_ovr)
        assert out_ovr.solutions[0].gain_ovr > 0

