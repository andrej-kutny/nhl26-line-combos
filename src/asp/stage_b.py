"""
Stage B: Grounding (Player-Aware Enumeration).

This module handles:
1. Building candidate player pools from Stage A solutions
2. Running the Stage B solver to enumerate concrete lines

Stage B takes abstract solutions from Stage A and finds all concrete
lines (with actual players) that satisfy the selected combos.
"""

import time
from typing import Literal

from ..core.data import get_data_loader
from ..core.models import ForwardLineCombo, DefenseLineCombo
from .interfaces import (
    StageAOutput,
    StageASolution,
    StageBInput,
    StageBOutput,
    StageBSolver,
    CandidatePlayer,
    ConcreteLine,
)


# =============================================================================
# INPUT GENERATOR
# =============================================================================

class StageBInputGenerator:
    """
    Generates Stage B input from Stage A solutions.
    
    For each Stage A solution:
    1. Extract attribute keys from selected combos
    2. Query database for matching players
    3. Rank by match_count and overall
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def generate(
        self,
        stage_a_solution: StageASolution,
        position_type: Literal["forward", "defense"],
        player_limit: int = 100,
    ) -> StageBInput:
        """
        Generate Stage B input for a single Stage A solution.
        
        Args:
            stage_a_solution: The abstract solution from Stage A
            position_type: "forward" or "defense"
            player_limit: Max players to include in candidate pool
            
        Returns:
            StageBInput with candidate players and combo facts
        """
        # Get the combos for this solution
        combos = self._get_combos_by_ids(stage_a_solution.combo_ids, position_type)
        
        # Extract attribute keys from combos
        teams, nationalities, events = self._extract_keys(combos)
        
        # Query candidate players
        candidates = self._query_candidates(
            position_type,
            teams,
            nationalities,
            events,
            limit=player_limit,
        )
        
        # Generate ASP facts
        combo_facts = self._generate_combo_facts(combos, position_type)
        player_facts = self._generate_player_facts(candidates)
        
        return StageBInput(
            position_type=position_type,
            stage_a_solution_rank=stage_a_solution.rank,
            combo_ids=stage_a_solution.combo_ids,
            combo_facts=combo_facts,
            players=candidates,
            player_facts=player_facts,
        )
    
    def _get_combos_by_ids(
        self,
        combo_ids: list[int],
        position_type: str,
    ) -> list[ForwardLineCombo | DefenseLineCombo]:
        """Fetch combo objects by their IDs."""
        if position_type == "forward":
            all_combos = self.loader.get_forward_combos()
        else:
            all_combos = self.loader.get_defense_combos()
        
        combo_map = {c.id: c for c in all_combos}
        return [combo_map[cid] for cid in combo_ids if cid in combo_map]
    
    def _extract_keys(
        self,
        combos: list[ForwardLineCombo | DefenseLineCombo],
    ) -> tuple[set[str], set[str], set[str]]:
        """
        Extract unique attribute keys from combos.
        
        Returns:
            (teams, nationalities, events) sets
        """
        teams: set[str] = set()
        nationalities: set[str] = set()
        events: set[str] = set()
        
        for combo in combos:
            for condition in [combo.condition1, combo.condition2]:
                self._add_condition_key(condition, teams, nationalities, events)
            
            # Forward combos have condition3
            if hasattr(combo, "condition3") and combo.condition3:
                self._add_condition_key(combo.condition3, teams, nationalities, events)
        
        return teams, nationalities, events
    
    def _add_condition_key(
        self,
        condition,
        teams: set[str],
        nationalities: set[str],
        events: set[str],
    ) -> None:
        """Add a condition's key to the appropriate set."""
        if condition.type == "team":
            teams.add(condition.key)
        elif condition.type == "nationality":
            nationalities.add(condition.key)
        elif condition.type == "event":
            events.add(condition.key)
    
    def _query_candidates(
        self,
        position_type: str,
        teams: set[str],
        nationalities: set[str],
        events: set[str],
        limit: int,
    ) -> list[CandidatePlayer]:
        """
        Query database for candidate players matching combo attributes.
        
        Implements the ranking from GOAL_1.md:
        - Primary: match_count DESC
        - Secondary: overall DESC
        """
        # Get all players of the position type
        if position_type == "forward":
            players = self.loader.get_forwards()
        else:
            players = self.loader.get_defense()
        
        # Calculate match_count and filter
        candidates = []
        for player in players:
            match_count = 0
            
            # Check if player matches any attribute
            if player.team in teams:
                match_count += 1
            if player.nationality in nationalities:
                match_count += 1
            if player.event in events:
                match_count += 1
            
            # Only include players that match at least one attribute
            if match_count > 0:
                candidates.append(CandidatePlayer(
                    card_id=player.id,
                    player_id=player.player_id,
                    team=player.team,
                    nationality=player.nationality,
                    event=player.event,
                    overall=player.overall,
                    salary=player.salary,
                    ap=getattr(player, "ap", 0),
                    match_count=match_count,
                ))
        
        # Sort by match_count DESC, overall DESC
        candidates.sort(key=lambda p: (-p.match_count, -p.overall))
        
        return candidates[:limit]
    
    def _generate_combo_facts(
        self,
        combos: list[ForwardLineCombo | DefenseLineCombo],
        position_type: str,
    ) -> list[str]:
        """
        Generate ASP facts for the selected combos.
        
        Uses same format as Stage A input for consistency with ASP team.
        """
        facts = []
        
        for combo in combos:
            c1 = combo.condition1
            c2 = combo.condition2
            
            if position_type == "forward":
                c3 = combo.condition3
                fact = (
                    f'forward_combo({combo.id}, {combo.reward_amount}, "{combo.reward_type.value}", '
                    f'{c1.type}("{c1.key}"), '
                    f'{c2.type}("{c2.key}"), '
                    f'{c3.type}("{c3.key}")).'
                )
            else:
                fact = (
                    f'defense_combo({combo.id}, {combo.reward_amount}, "{combo.reward_type.value}", '
                    f'{c1.type}("{c1.key}"), '
                    f'{c2.type}("{c2.key}")).'
                )
            
            facts.append(fact)
        
        return facts
    
    def _generate_player_facts(self, candidates: list[CandidatePlayer]) -> list[str]:
        """Generate ASP facts for candidate players."""
        facts = []
        
        for p in candidates:
            # Player fact with all attributes
            fact = (
                f"player({p.card_id}, {p.player_id}, "
                f"\"{p.team}\", \"{p.nationality}\", \"{p.event}\", "
                f"{p.overall}, {p.salary}, {p.ap})."
            )
            facts.append(fact)
            
            # Attribute facts for easier ASP matching
            facts.append(f"player_team({p.card_id}, \"{p.team}\").")
            facts.append(f"player_nationality({p.card_id}, \"{p.nationality}\").")
            facts.append(f"player_event({p.card_id}, \"{p.event}\").")
        
        return facts


# =============================================================================
# MOCK SOLVER (Placeholder until ASP team implements)
# =============================================================================

class MockStageBSolver(StageBSolver):
    """
    Mock Stage B solver for development/testing.
    
    Generates sample concrete lines from candidate players.
    ASP team will replace with real Clingo implementation.
    """
    
    def solve(self, input_data: StageBInput) -> StageBOutput:
        """
        Generate mock Stage B solutions.
        
        Creates plausible lines from candidate players.
        Real implementation will enumerate ALL valid lines.
        """
        start_time = time.time()
        
        lines = []
        players = input_data.players
        
        if not players:
            return StageBOutput(
                stage_a_solution_rank=input_data.stage_a_solution_rank,
                lines=[],
                solve_time_ms=0,
            )
        
        # Generate some mock lines
        if input_data.position_type == "forward":
            lines = self._generate_forward_lines(players, input_data.combo_ids)
        else:
            lines = self._generate_defense_lines(players, input_data.combo_ids)
        
        solve_time = (time.time() - start_time) * 1000
        
        return StageBOutput(
            stage_a_solution_rank=input_data.stage_a_solution_rank,
            lines=lines,
            solve_time_ms=solve_time,
        )
    
    def _generate_forward_lines(
        self,
        players: list[CandidatePlayer],
        combo_ids: list[int],
    ) -> list[ConcreteLine]:
        """Generate mock forward lines (3 players each)."""
        lines = []
        
        # Get unique player_ids to avoid duplicates
        seen_player_ids: set[int] = set()
        unique_players = []
        
        for p in players:
            if p.player_id not in seen_player_ids:
                seen_player_ids.add(p.player_id)
                unique_players.append(p)
        
        # Generate up to 10 mock lines
        for i in range(min(10, len(unique_players) // 3)):
            p1 = unique_players[i * 3]
            p2 = unique_players[i * 3 + 1]
            p3 = unique_players[i * 3 + 2]
            
            lines.append(ConcreteLine(
                player_card_ids=[p1.card_id, p2.card_id, p3.card_id],
                player_ids=[p1.player_id, p2.player_id, p3.player_id],
                activated_combo_ids=combo_ids,
                total_ovr=p1.overall + p2.overall + p3.overall,
                total_salary=p1.salary + p2.salary + p3.salary,
                total_ap=p1.ap + p2.ap + p3.ap,
            ))
        
        return lines
    
    def _generate_defense_lines(
        self,
        players: list[CandidatePlayer],
        combo_ids: list[int],
    ) -> list[ConcreteLine]:
        """Generate mock defense pairs (2 players each)."""
        lines = []
        
        seen_player_ids: set[int] = set()
        unique_players = []
        
        for p in players:
            if p.player_id not in seen_player_ids:
                seen_player_ids.add(p.player_id)
                unique_players.append(p)
        
        for i in range(min(10, len(unique_players) // 2)):
            p1 = unique_players[i * 2]
            p2 = unique_players[i * 2 + 1]
            
            lines.append(ConcreteLine(
                player_card_ids=[p1.card_id, p2.card_id],
                player_ids=[p1.player_id, p2.player_id],
                activated_combo_ids=combo_ids,
                total_ovr=p1.overall + p2.overall,
                total_salary=p1.salary + p2.salary,
                total_ap=p1.ap + p2.ap,
            ))
        
        return lines


# =============================================================================
# FACTORY
# =============================================================================

def get_stage_b_solver() -> StageBSolver:
    """
    Get the Stage B solver instance.
    
    Returns MockStageBSolver until ASP team provides real implementation.
    
    TODO: Replace with real Clingo solver when available:
        from .clingo_solver import ClingoStageBSolver
        return ClingoStageBSolver()
    """
    return MockStageBSolver()
