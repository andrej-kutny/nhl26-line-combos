"""
Stage A: Abstract Optimization (Combo-First).

This module handles:
1. Generating ASP facts from combo templates
2. Running the Stage A solver (mock implementation provided)

Stage A optimizes over line combination templates without considering
specific players. It returns the top-K abstract solutions.
"""

import time
from typing import Literal

from ..core.data import get_data_loader
from ..core.models import ForwardLineCombo, DefenseLineCombo, RewardType
from .interfaces import (
    StageAInput,
    StageAOutput,
    StageASolution,
    StageASolver,
)


# =============================================================================
# INPUT GENERATOR
# =============================================================================

class StageAInputGenerator:
    """
    Generates Stage A input from database combo templates.
    
    Converts combo data into ASP facts for the solver.
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def generate(
        self,
        position_type: Literal["forward", "defense"],
        optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
        top_k: int = 200,
    ) -> StageAInput:
        """
        Generate Stage A input for the given position and mode.
        
        Args:
            position_type: "forward" or "defense"
            optimization_mode: Which metrics to optimize
            top_k: Number of solutions to find
            
        Returns:
            StageAInput with combo facts ready for ASP
        """
        # Get combos from database
        if position_type == "forward":
            combos = self.loader.get_forward_combos()
            combo_facts = self._generate_forward_facts(combos, optimization_mode)
        else:
            combos = self.loader.get_defense_combos()
            combo_facts = self._generate_defense_facts(combos, optimization_mode)
        
        # Set weights based on position and mode
        ovr_weight, sal_weight, ap_weight = self._get_weights(position_type, optimization_mode)
        
        return StageAInput(
            position_type=position_type,
            optimization_mode=optimization_mode,
            combo_facts=combo_facts,
            top_k=top_k,
            ovr_weight=ovr_weight,
            sal_weight=sal_weight,
            ap_weight=ap_weight,
        )
    
    def _generate_forward_facts(
        self,
        combos: list[ForwardLineCombo],
        mode: str,
    ) -> list[str]:
        """
        Generate ASP facts for forward combos.
        
        Format matches ASP team's expected input:
        forward_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2, entry3).
        
        Where entries are: team("X"), nationality("Y"), event("Z")
        """
        facts = []
        
        for combo in combos:
            # Filter by mode if needed
            if not self._combo_matches_mode(combo.reward_type, mode):
                continue
            
            c1 = combo.condition1
            c2 = combo.condition2
            c3 = combo.condition3
            
            # Format: forward_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2, entry3).
            # Entries use functor notation: team("OTT"), nationality("USA"), event("HH")
            fact = (
                f'forward_combo({combo.id}, {combo.reward_amount}, "{combo.reward_type.value}", '
                f'{c1.type}("{c1.key}"), '
                f'{c2.type}("{c2.key}"), '
                f'{c3.type}("{c3.key}")).'
            )
            facts.append(fact)
        
        return facts
    
    def _generate_defense_facts(
        self,
        combos: list[DefenseLineCombo],
        mode: str,
    ) -> list[str]:
        """
        Generate ASP facts for defense combos.
        
        Format matches ASP team's expected input:
        defense_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2).
        
        Where entries are: team("X"), nationality("Y"), event("Z")
        """
        facts = []
        
        for combo in combos:
            if not self._combo_matches_mode(combo.reward_type, mode):
                continue
            
            c1 = combo.condition1
            c2 = combo.condition2
            
            # Format: defense_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2).
            fact = (
                f'defense_combo({combo.id}, {combo.reward_amount}, "{combo.reward_type.value}", '
                f'{c1.type}("{c1.key}"), '
                f'{c2.type}("{c2.key}")).'
            )
            facts.append(fact)
        
        return facts
    
    def _combo_matches_mode(self, reward_type: RewardType, mode: str) -> bool:
        """Check if combo's reward type is relevant for the optimization mode."""
        if mode == "ovr":
            return reward_type == RewardType.OVR
        elif mode == "sal":
            return reward_type == RewardType.SAL
        elif mode == "ap":
            return reward_type == RewardType.AP
        else:
            # Combined modes include all types
            return True
    
    def _get_weights(
        self,
        position_type: str,
        mode: str,
    ) -> tuple[float, float, float]:
        """Get optimization weights based on position and mode."""
        # Default weights from GOAL_1.md
        if position_type == "forward":
            base_ovr, base_sal = 3.0, 1.0
        else:
            base_ovr, base_sal = 2.0, 1.0
        
        base_ap = 1.0
        
        # Adjust based on mode
        if mode == "ovr":
            return (1.0, 0.0, 0.0)
        elif mode == "sal":
            return (0.0, 1.0, 0.0)
        elif mode == "ap":
            return (0.0, 0.0, 1.0)
        elif mode == "ovr_sal":
            return (base_ovr, base_sal, 0.0)
        else:  # ovr_sal_ap
            return (base_ovr, base_sal, base_ap)


# =============================================================================
# MOCK SOLVER (Placeholder until ASP team implements)
# =============================================================================

class MockStageASolver(StageASolver):
    """
    Mock Stage A solver for development/testing.
    
    Returns synthetic solutions based on actual combo data.
    ASP team will replace this with real Clingo implementation.
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def solve(self, input_data: StageAInput) -> StageAOutput:
        """
        Generate mock Stage A solutions.
        
        Creates plausible solutions by selecting random subsets of combos.
        """
        start_time = time.time()
        
        # Get actual combos to create realistic mock data
        if input_data.position_type == "forward":
            combos = self.loader.get_forward_combos()
        else:
            combos = self.loader.get_defense_combos()
        
        # Filter combos by mode
        filtered_combos = [
            c for c in combos
            if self._combo_matches_mode(c.reward_type, input_data.optimization_mode)
        ]
        
        # Generate mock solutions
        solutions = []
        num_solutions = min(input_data.top_k, len(filtered_combos))
        
        for rank in range(1, num_solutions + 1):
            # Select a subset of combos for this solution
            # In reality, ASP would find optimal non-conflicting subsets
            selected = filtered_combos[rank - 1 : rank]  # Just one combo per solution for mock
            
            combo_ids = [c.id for c in selected]
            gain_ovr = sum(c.reward_amount for c in selected if c.reward_type == RewardType.OVR)
            gain_sal = sum(c.reward_amount for c in selected if c.reward_type == RewardType.SAL)
            gain_ap = sum(c.reward_amount for c in selected if c.reward_type == RewardType.AP)
            
            solutions.append(StageASolution(
                rank=rank,
                combo_ids=combo_ids,
                gain_ovr=gain_ovr,
                gain_sal=gain_sal,
                gain_ap=gain_ap,
            ))
        
        solve_time = (time.time() - start_time) * 1000
        
        return StageAOutput(
            solutions=solutions,
            solve_time_ms=solve_time,
            total_models_found=len(solutions),
        )
    
    def _combo_matches_mode(self, reward_type: RewardType, mode: str) -> bool:
        """Check if combo's reward type is relevant for the optimization mode."""
        if mode == "ovr":
            return reward_type == RewardType.OVR
        elif mode == "sal":
            return reward_type == RewardType.SAL
        elif mode == "ap":
            return reward_type == RewardType.AP
        return True


# =============================================================================
# FACTORY
# =============================================================================

def get_stage_a_solver() -> StageASolver:
    """
    Get the Stage A solver instance.
    
    Returns MockStageASolver until ASP team provides real implementation.
    
    TODO: Replace with real Clingo solver when available:
        from .clingo_solver import ClingoStageASolver
        return ClingoStageASolver()
    """
    return MockStageASolver()
