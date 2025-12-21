import pytest
from src.asp.stage_b import ClingoStageBSolver, StageBInput, CandidatePlayer
from src.core.models import RewardType

class TestStageBIntegration:
    """
    Integration tests for Stage B Solver using real ASP rules (g1b_grounding).
    """
    
    def test_solve_defense_pair(self):
        solver = ClingoStageBSolver()
        
        # Setup: Combo requires Team A and Team B.
        # Player 1: Team A
        # Player 2: Team B
        # Player 3: Team C
        
        combo_facts = [
            'def_combo(1, 5, ovr, "team", "A", "team", "B").'
        ]
        
        players = [
            CandidatePlayer(card_id=101, player_id=1, team="A", nationality="N", event="E", overall=80, salary=1000, ap=0, match_count=1),
            CandidatePlayer(card_id=102, player_id=2, team="B", nationality="N", event="E", overall=80, salary=1000, ap=0, match_count=1),
            CandidatePlayer(card_id=103, player_id=3, team="C", nationality="N", event="E", overall=90, salary=1000, ap=0, match_count=0),
        ]
        
        # Generate facts manually or via helper?
        # Using manual string construction to match updated StageBInputGenerator logic.
        player_facts = [
            'player(101, 80, "A", "N", "E").', 'card_player(101, 1).', 'salary(101, 1000).', 'ap(101, 0).',
            'player(102, 80, "B", "N", "E").', 'card_player(102, 2).', 'salary(102, 1000).', 'ap(102, 0).',
            'player(103, 90, "C", "N", "E").', 'card_player(103, 3).', 'salary(103, 1000).', 'ap(103, 0).',
        ]
        
        input_data = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[1],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        
        assert len(output.lines) > 0
        
        # Best line with "balanced" target (Bonus > OVR priority):
        # P1+P2: Base OVR 160 + Combo 5 = 165.
        # P1+P3: Base OVR 170.
        # Since "balanced" prioritizes bonuses (level 3) over OVR (level 2),
        # it will pick P1+P2 despite lower total score, because it has a bonus.
        
        best = output.lines[-1]
        assert best.total_ovr == 165
        assert 101 in best.player_card_ids
        assert 102 in best.player_card_ids

    def test_solve_forward_line(self):
        solver = ClingoStageBSolver()
        
        # 3 Players.
        # Combo: A, B, C. Reward 30.
        
        combo_facts = [
            'fwd_combo(1, 30, ovr, "team", "A", "team", "B", "team", "C").'
        ]
        
        players = [
            CandidatePlayer(card_id=1, player_id=1, team="A", nationality="N", event="E", overall=80, salary=100, ap=0, match_count=1),
            CandidatePlayer(card_id=2, player_id=2, team="B", nationality="N", event="E", overall=80, salary=100, ap=0, match_count=1),
            CandidatePlayer(card_id=3, player_id=3, team="C", nationality="N", event="E", overall=80, salary=100, ap=0, match_count=1),
            CandidatePlayer(card_id=4, player_id=4, team="D", nationality="N", event="E", overall=85, salary=100, ap=0, match_count=0),
        ]
        
        player_facts = [
            'player(1, 80, "A", "N", "E").', 'card_player(1,1).', 'salary(1,100).', 'ap(1,0).',
            'player(2, 80, "B", "N", "E").', 'card_player(2,2).', 'salary(2,100).', 'ap(2,0).',
            'player(3, 80, "C", "N", "E").', 'card_player(3,3).', 'salary(3,100).', 'ap(3,0).',
            'player(4, 85, "D", "N", "E").', 'card_player(4,4).', 'salary(4,100).', 'ap(4,0).',
        ]
        
        input_data = StageBInput(
            position_type="forward",
            stage_a_solution_rank=1,
            combo_ids=[1],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        best = output.lines[-1]
        
        # 1+2+3: 240 + 30 = 270.
        # 1+2+4: 245 (No combo).
        assert set(best.player_card_ids) == {1, 2, 3}

    def test_constraints_exclusion(self):
        solver = ClingoStageBSolver()
        
        # Exclude player 1
        
        combo_facts = []
        players = [
            CandidatePlayer(card_id=1, player_id=1, team="A", nationality="N", event="E", overall=90, salary=100, ap=0, match_count=0),
            CandidatePlayer(card_id=2, player_id=2, team="A", nationality="N", event="E", overall=80, salary=100, ap=0, match_count=0),
            CandidatePlayer(card_id=3, player_id=3, team="A", nationality="N", event="E", overall=80, salary=100, ap=0, match_count=0),
        ]
        player_facts = [
            'player(1, 90, "A", "N", "E").', 'card_player(1,1).', 'salary(1,100).', 'ap(1,0).',
            'player(2, 80, "A", "N", "E").', 'card_player(2,2).', 'salary(2,100).', 'ap(2,0).',
            'player(3, 80, "A", "N", "E").', 'card_player(3,3).', 'salary(3,100).', 'ap(3,0).',
            'excluded(1).' # Constraint
        ]
        
        input_data = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        best = output.lines[-1]
        
        # Must pick 2 and 3 because 1 is excluded.
        assert 1 not in best.player_card_ids
        assert 2 in best.player_card_ids
        assert 3 in best.player_card_ids

    def test_stageb_can_satisfy_all_combos(self):
        # Ported from test_goal1_stageb_enumeration.py
        solver = ClingoStageBSolver()
        
        # 5 players. P1-P4 match FANT/FANT/FANT. P5 does not.
        players = [
            CandidatePlayer(card_id=1, player_id=1, team="det", nationality="canada", event="fant", overall=80, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=2, player_id=2, team="mtl", nationality="swe", event="fant", overall=81, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=3, player_id=3, team="nyr", nationality="fin", event="fant", overall=82, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=4, player_id=4, team="tbl", nationality="nor", event="fant", overall=83, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=5, player_id=5, team="tbl", nationality="nor", event="totw", overall=83, salary=0, ap=0, match_count=0),
        ]
        
        player_facts = [
            'player(1, 80, "det", "canada", "fant"). card_player(1,1). salary(1,0). ap(1,0).',
            'player(2, 81, "mtl", "swe", "fant"). card_player(2,2). salary(2,0). ap(2,0).',
            'player(3, 82, "nyr", "fin", "fant"). card_player(3,3). salary(3,0). ap(3,0).',
            'player(4, 83, "tbl", "nor", "fant"). card_player(4,4). salary(4,0). ap(4,0).',
            'player(5, 83, "tbl", "nor", "totw"). card_player(5,5). salary(5,0). ap(5,0).',
        ]
        
        combo_facts = [
            'fwd_combo(1, 20, sal, "event", "fant", "event", "fant", "event", "fant").',
            'fwd_combo(2, 10, ap, "event", "fant", "event", "fant", "event", "fant").',
            # Enforce activation to match original test semantics of "can satisfy"
            ':- not combo_active(1).',
            ':- not combo_active(2).'
        ]
        
        input_data = StageBInput(
            position_type="forward",
            stage_a_solution_rank=1,
            combo_ids=[1, 2],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        
        assert len(output.lines) >= 1
        
    def test_stageb_cant_satisfy_all_combos(self):
        solver = ClingoStageBSolver()
        
        players = [
            CandidatePlayer(card_id=1, player_id=1, team="det", nationality="canada", event="fant", overall=80, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=2, player_id=2, team="mtl", nationality="swe", event="fant", overall=81, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=3, player_id=3, team="nyr", nationality="fin", event="fant", overall=82, salary=0, ap=0, match_count=1),
        ]
        
        player_facts = [
            'player(1, 80, "det", "canada", "fant"). card_player(1,1). salary(1,0). ap(1,0).',
            'player(2, 81, "mtl", "swe", "fant"). card_player(2,2). salary(2,0). ap(2,0).',
            'player(3, 82, "nyr", "fin", "fant"). card_player(3,3). salary(3,0). ap(3,0).',
        ]
        
        combo_facts = [
            'fwd_combo(3, 10, sal, "team", "vgk", "nationality", "nor", "event", "fant").',
            ':- not combo_active(3).' # Enforce it
        ]
        
        input_data = StageBInput(
            position_type="forward",
            stage_a_solution_rank=1,
            combo_ids=[3],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        # Should be empty
        assert len(output.lines) == 0

    def test_stageb_forward_enumerates_all_combinations(self):
        solver = ClingoStageBSolver()
        
        # 4 identical players. Combo needs 3.
        # All have OVR 80. Score will be equal.
        # Should find 4 models.
        
        players = [
            CandidatePlayer(card_id=1, player_id=1, team="det", nationality="can", event="fant", overall=80, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=2, player_id=2, team="det", nationality="can", event="fant", overall=80, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=3, player_id=3, team="det", nationality="can", event="fant", overall=80, salary=0, ap=0, match_count=1),
            CandidatePlayer(card_id=4, player_id=4, team="det", nationality="can", event="fant", overall=80, salary=0, ap=0, match_count=1),
        ]
        player_facts = [
            'player(1, 80, "det", "can", "fant"). card_player(1,1). salary(1,0). ap(1,0).',
            'player(2, 80, "det", "can", "fant"). card_player(2,2). salary(2,0). ap(2,0).',
            'player(3, 80, "det", "can", "fant"). card_player(3,3). salary(3,0). ap(3,0).',
            'player(4, 80, "det", "can", "fant"). card_player(4,4). salary(4,0). ap(4,0).',
        ]
        combo_facts = [
            'fwd_combo(1, 20, sal, "team", "det", "team", "det", "team", "det").',
            ':- not combo_active(1).'
        ]
        
        input_data = StageBInput(
            position_type="forward",
            stage_a_solution_rank=1,
            combo_ids=[1],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        assert len(output.lines) == 4

    def test_unique_player_conflict(self):
        solver = ClingoStageBSolver()
        # Card 1 and 2 refer to same player ID 10.
        # P1: OVR 99. P2: OVR 98.
        players = [
            CandidatePlayer(card_id=1, player_id=10, team="CHI", nationality="USA", event="ICON", overall=99, salary=20, ap=0, match_count=0),
            CandidatePlayer(card_id=2, player_id=10, team="LAK", nationality="USA", event="TOTW", overall=98, salary=19, ap=0, match_count=0),
            CandidatePlayer(card_id=3, player_id=1, team="TBL", nationality="SWE", event="GM", overall=90, salary=11, ap=0, match_count=0),
        ]
        player_facts = [
            'player(1, 99, "CHI", "USA", "ICON"). card_player(1, 10). salary(1, 20). ap(1, 0).',
            'player(2, 98, "LAK", "USA", "TOTW"). card_player(2, 10). salary(2, 19). ap(2, 0).',
            'player(3, 90, "TBL", "SWE", "GM"). card_player(3, 1). salary(3, 11). ap(3, 0).',
        ]
        
        input_data = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[],
            combo_facts=[],
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        best = output.lines[-1]
        
        # Must select 2 players.
        # Can select 1 and 3 (OVR 189).
        # Can select 2 and 3 (OVR 188).
        # CANNOT select 1 and 2 (Same player 10).
        
        assert 10 in best.player_ids
        # Check that we don't have both Card 1 and Card 2
        assert not (1 in best.player_card_ids and 2 in best.player_card_ids)
        # Should pick best OVR (Card 1)
        assert 1 in best.player_card_ids
        assert 3 in best.player_card_ids

    def test_salary_cap(self):
        solver = ClingoStageBSolver()
        
        # Card 1 (P10): Sal 20, OVR 99
        # Card 2 (P10): Sal 19, OVR 98
        # Card 3 (P1): Sal 11, OVR 90
        
        players = [
            CandidatePlayer(card_id=1, player_id=10, team="CHI", nationality="USA", event="ICON", overall=99, salary=20, ap=0, match_count=0),
            CandidatePlayer(card_id=2, player_id=10, team="LAK", nationality="USA", event="TOTW", overall=98, salary=19, ap=0, match_count=0),
            CandidatePlayer(card_id=3, player_id=1, team="TBL", nationality="SWE", event="GM", overall=90, salary=11, ap=0, match_count=0),
        ]
        player_facts = [
            'player(1, 99, "CHI", "USA", "ICON"). card_player(1, 10). salary(1, 20). ap(1, 0).',
            'player(2, 98, "LAK", "USA", "TOTW"). card_player(2, 10). salary(2, 19). ap(2, 0).',
            'player(3, 90, "TBL", "SWE", "GM"). card_player(3, 1). salary(3, 11). ap(3, 0).',
        ]
        
        # Scenario 1: Cap 30.
        # 1+3 = 31 > 30. Invalid.
        # 2+3 = 30 <= 30. Valid.
        
        facts_cap_30 = player_facts + ['max_salary(30).']
        
        input_30 = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[],
            combo_facts=[],
            players=players,
            player_facts=facts_cap_30
        )
        
        out_30 = solver.solve(input_30)
        best_30 = out_30.lines[-1]
        assert 2 in best_30.player_card_ids
        assert 3 in best_30.player_card_ids
        assert 1 not in best_30.player_card_ids
        
        # Scenario 2: Cap 31.
        # 1+3 = 31 <= 31. Valid. Higher OVR.
        
        facts_cap_31 = player_facts + ['max_salary(31).']
        
        input_31 = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[],
            combo_facts=[],
            players=players,
            player_facts=facts_cap_31
        )
        
        out_31 = solver.solve(input_31)
        best_31 = out_31.lines[-1]
        assert 1 in best_31.player_card_ids
        assert 3 in best_31.player_card_ids

    def test_salary_cap_bonus(self):
        solver = ClingoStageBSolver()
        
        # P1 (Sal 20)
        # P2 (Sal 20)
        # Cap 35. Total 40 > 35.
        # But Combo provides 5 Salary relief (Bonus).
        # Effective = 40 - 5 = 35. Allowed.
        
        players = [
            CandidatePlayer(card_id=1, player_id=1, team="A", nationality="N", event="E", overall=80, salary=20, ap=0, match_count=0),
            CandidatePlayer(card_id=2, player_id=2, team="B", nationality="N", event="E", overall=80, salary=20, ap=0, match_count=0),
        ]
        
        player_facts = [
            'player(1, 80, "A", "N", "E"). card_player(1, 1). salary(1, 20). ap(1, 0).',
            'player(2, 80, "B", "N", "E"). card_player(2, 2). salary(2, 20). ap(2, 0).',
        ]
        
        combo_facts = [
            'def_combo(1, 5, sal, "team", "A", "team", "B").',
            'max_salary(35).'
        ]
        
        input_data = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[1],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        
        # Should be valid
        assert len(output.lines) > 0
        best = output.lines[-1]
        assert set(best.player_card_ids) == {1, 2}

    def test_bonus_priority_over_base_ovr(self):
        solver = ClingoStageBSolver()
        
        # P1: Base OVR 99. No Combo.
        # P2: Base OVR 90. Combo +1 OVR.
        # P3: Partner (OVR 80).
        
        # P1+P3: 179. No Combo.
        # P2+P3: 170. Combo +1. Total 171.
        
        # Priority 3 (Bonus): P2+P3 has 1. P1+P3 has 0.
        # P2+P3 should be chosen despite lower base OVR and lower total OVR (171 vs 179).
        
        players = [
            CandidatePlayer(card_id=1, player_id=1, team="A", nationality="N", event="E", overall=99, salary=0, ap=0, match_count=0),
            CandidatePlayer(card_id=2, player_id=2, team="B", nationality="N", event="E", overall=90, salary=0, ap=0, match_count=0),
            CandidatePlayer(card_id=3, player_id=3, team="C", nationality="N", event="E", overall=80, salary=0, ap=0, match_count=0),
        ]
        
        player_facts = [
            'player(1, 99, "A", "N", "E"). card_player(1, 1). salary(1, 0). ap(1, 0).',
            'player(2, 90, "B", "N", "E"). card_player(2, 2). salary(2, 0). ap(2, 0).',
            'player(3, 80, "C", "N", "E"). card_player(3, 3). salary(3, 0). ap(3, 0).',
        ]
        
        # Combo matches P2 (Team B) and P3 (Team C)
        combo_facts = [
            'def_combo(1, 1, ovr, "team", "B", "team", "C").'
        ]
        
        input_data = StageBInput(
            position_type="defense",
            stage_a_solution_rank=1,
            combo_ids=[1],
            combo_facts=combo_facts,
            players=players,
            player_facts=player_facts
        )
        
        output = solver.solve(input_data)
        best = output.lines[-1]
        
        # Should pick 2 and 3
        assert 2 in best.player_card_ids
        assert 3 in best.player_card_ids
        assert 1 not in best.player_card_ids
