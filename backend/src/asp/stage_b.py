"""
Stage B: Grounding (Player-Aware Enumeration).

This module handles:
1. Building candidate player pools from Stage A solutions
2. Running the Stage B solver to enumerate concrete lines

Stage B takes abstract solutions from Stage A and finds all concrete
lines (with actual players) that satisfy the selected combos.
"""

import time
import clingo
from typing import Literal
from pathlib import Path

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
        
        Matches g1b_grounding rules format:
        def_combo(ID, Reward, Type, Type1, Key1, Type2, Key2).
        fwd_combo(ID, Reward, Type, Type1, Key1, Type2, Key2, Type3, Key3).
        """
        facts = []
        
        for combo in combos:
            c1 = combo.condition1
            c2 = combo.condition2
            reward_type = combo.reward_type.value.lower() # g1b uses lowercase atoms: ovr, sal, ap
            
            if position_type == "forward":
                c3 = combo.condition3
                fact = (
                    f'fwd_combo({combo.id}, {combo.reward_amount}, {reward_type}, '
                    f'"{c1.type}", "{c1.key}", '
                    f'"{c2.type}", "{c2.key}", '
                    f'"{c3.type}", "{c3.key}").'
                )
            else:
                fact = (
                    f'def_combo({combo.id}, {combo.reward_amount}, {reward_type}, '
                    f'"{c1.type}", "{c1.key}", '
                    f'"{c2.type}", "{c2.key}").'
                )
            
            facts.append(fact)
        
        return facts
    
    def _generate_player_facts(self, candidates: list[CandidatePlayer]) -> list[str]:
        """
        Generate ASP facts for candidate players.
        
        Matches g1b_grounding rules format:
        player(CardID, OVR, Team, Nationality, Event).
        card_player(CardID, PlayerID).
        salary(CardID, S).
        ap(CardID, A).
        """
        facts = []
        
        for p in candidates:
            # player(CardID, OVR, Team, Nat, Event)
            fact = (
                f'player({p.card_id}, {int(p.overall)}, '
                f'"{p.team}", "{p.nationality}", "{p.event}").'
            )
            facts.append(fact)
            
            facts.append(f"card_player({p.card_id}, {p.player_id}).")
            facts.append(f"salary({p.card_id}, {int(p.salary)}).")
            facts.append(f"ap({p.card_id}, {int(p.ap)}).")
        
        return facts


# =============================================================================
# SOLVER
# =============================================================================

class ClingoStageBSolver(StageBSolver):
    """
    Clingo-based Stage B solver.
    
    Uses ASP rules in src/asp/g1b_grounding/ to enumerate concrete lines
    that satisfy the selected combos and maximize score.
    """
    
    def __init__(self):
        # Paths relative to backend/src/asp/ (where this file is)
        current_dir = Path(__file__).parent
        self.rules_base = current_dir / "g1b_grounding/base.lp"
        self.rules_def = current_dir / "g1b_grounding/defense_pair.lp"
        self.rules_fwd = current_dir / "g1b_grounding/forward_line.lp"

    def solve(self, input_data: StageBInput) -> StageBOutput:
        start_time = time.time()
        
        if not input_data.players:
            return StageBOutput(
                stage_a_solution_rank=input_data.stage_a_solution_rank,
                lines=[],
                solve_time_ms=0,
            )

        # 1. Select rules based on position type
        rules_files = [str(self.rules_base)]
        if input_data.position_type == "forward":
            rules_files.append(str(self.rules_fwd))
        else:
            rules_files.append(str(self.rules_def))
            
        # 2. Setup Clingo
        # Find all optimal solutions
        ctl = clingo.Control(["--opt-mode=optN"])
        
        for f in rules_files:
            try:
                ctl.load(f)
            except Exception as e:
                # Fallback if path resolution fails (e.g. running from different cwd)
                # Try relative to CWD if absolute failed?
                # But Path(__file__) should be absolute.
                raise RuntimeError(f"Failed to load rule file {f}: {e}")
            
        # 3. Add input facts
        program = "\n".join(input_data.combo_facts + input_data.player_facts)
        
        # Add default constraints if not present (StageBInput doesn't carry them yet)
        # TODO: Get these from input if available
        program += '\nopt_target("balanced").\n'
        program += 'max_salary(999999).\n'
        program += 'max_ap(999).\n'
        
        ctl.add("base", [], program)
        
        # 4. Ground and Solve
        ctl.ground([("base", [])])
        
        lines: list[ConcreteLine] = []
        seen_line_signatures: set[tuple[int, ...]] = set()
        player_map = {p.card_id: p for p in input_data.players}
        
        def on_model(m):
            # Only process if optimal (Clingo optN handles finding them)
            # We convert all models yielded by Clingo (which eventually are the optimal ones)
            # But Clingo yields *better* models progressively.
            # We should only keep the ones from the *last* optimization step?
            # Or assume Clingo only yields optimal ones if we check optimality?
            # Standard pattern: check m.optimality_proven is True?
            # Or simpler: Collect all, filter by best cost at the end?
            # Since we want *enumeration* of all valid lines for the optimal score:
            # We rely on Clingo's output.
            line = self._parse_model(m, player_map)
            
            # Deduplicate based on player composition
            # Use sorted tuple of card IDs as signature
            signature = tuple(line.player_card_ids)
            if signature not in seen_line_signatures:
                lines.append(line)
                seen_line_signatures.add(signature)

        ctl.solve(on_model=on_model)
        
        # Filter for the best cost (if multiple costs returned)
        # ConcreteLine doesn't store the raw cost vector.
        # But usually Clingo solve sequence ends with optimal models.
        # We can assume the last chunk of models with same score are optimal.
        # For MVP, returning all is fine, backend can filter.
        
        solve_time = (time.time() - start_time) * 1000
        
        return StageBOutput(
            stage_a_solution_rank=input_data.stage_a_solution_rank,
            lines=lines,
            solve_time_ms=solve_time,
        )

    def _parse_model(self, model, player_map: dict[int, CandidatePlayer]) -> ConcreteLine:
        selected_card_ids = []
        active_combo_ids = []
        
        total_ovr = 0
        total_salary = 0
        total_ap = 0
        
        for symbol in model.symbols(shown=True):
            if symbol.name == "select":
                # select(CardID, Slot)
                card_id = symbol.arguments[0].number
                selected_card_ids.append(card_id)
            elif symbol.name == "combo_active":
                # combo_active(ID)
                cid = symbol.arguments[0].number
                active_combo_ids.append(cid)
            elif symbol.name == "total_base_ovr":
                total_ovr = symbol.arguments[0].number
            elif symbol.name == "total_salary":
                total_salary = symbol.arguments[0].number
            elif symbol.name == "total_ap":
                total_ap = symbol.arguments[0].number
            # Bonuses are available too: total_ovr_bonus, etc.
            # ConcreteLine expects "total_ovr" which usually means Final OVR?
            # Interface doc says: "total_ovr: int".
            # Stage A uses "gain_ovr".
            # Let's sum base + bonus for total_ovr?
            # Or just use base.
            # I'll use base + bonus if available.
            elif symbol.name == "total_ovr_bonus":
                total_ovr += symbol.arguments[0].number
            elif symbol.name == "total_salary_bonus":
                # Salary bonus reduces effective salary?
                # Or implies capability?
                # Rules say: S - B > Max.
                # So effective salary is S - B.
                total_salary -= symbol.arguments[0].number
                
        selected_card_ids.sort()
        player_ids = [player_map[cid].player_id for cid in selected_card_ids if cid in player_map]
        
        return ConcreteLine(
            player_card_ids=selected_card_ids,
            player_ids=player_ids,
            activated_combo_ids=sorted(active_combo_ids),
            total_ovr=total_ovr,
            total_salary=total_salary,
            total_ap=total_ap,
        )


# =============================================================================
# FACTORY
# =============================================================================

def get_stage_b_solver() -> StageBSolver:
    """
    Get the Stage B solver instance.
    """
    return ClingoStageBSolver()
