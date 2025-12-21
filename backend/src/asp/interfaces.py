"""
ASP Solver Interface Contracts for Goal 1 Pipeline.

This module defines the abstract interfaces that ASP solvers must implement.
The backend uses these contracts; ASP team implements them.

Stage A: Abstract optimization over combo templates (no real players)
Stage B: Concrete line enumeration using candidate players
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal


# =============================================================================
# STAGE A TYPES
# =============================================================================

@dataclass
class StageAInput:
    """
    Input for Stage A solver.
    
    Contains combo templates and optimization parameters.
    """
    position_type: Literal["forward", "defense"]
    optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"]
    
    # Combo facts as ASP-ready strings (or structured data)
    combo_facts: list[str] = field(default_factory=list)
    
    # Parameters
    top_k: int = 200  # Number of abstract solutions to return
    
    # Weights for combined modes
    # ovr_weight: float = 1.0 if optimization_mode == "ovr" else (2.0 if position_type == "defense" else 3.0)
    ovr_weight: float = 1.0 # this will be overwritten
    sal_weight: float = 1.0
    ap_weight: float = 1.0


@dataclass
class PlayerAttribute:
    """
    An abstract player attribute from Stage A output.
    
    Represents a constraint on a player slot without specifying a concrete player.
    E.g., player_attr(1, team("DET")) means slot 1 needs team="DET".
    """
    slot: int  # 1, 2, 3 for forwards; 1, 2 for defense
    attr_type: str  # "team", "nationality", "event"
    attr_value: str  # e.g., "DET", "USA", "HH"


@dataclass 
class ActiveComboInfo:
    """
    Info about an active combo from ASP output.
    
    Maps to: fwd_active_combo(id, reward_amount, reward_type)
    """
    combo_id: int
    reward_amount: int
    reward_type: str  # "OVR", "SAL", "AP"


@dataclass
class StageASolution:
    """
    A single abstract solution from Stage A.
    
    Contains which combos were selected, player slot attributes, and gains.
    
    ASP output format:
        player_attr(1,team("DET")) player_attr(2,event("TOTW")) ...
        fwd_active_combo(2,5,"AP") fwd_active_combo(39,3,"AP") ...
        total_reward(11)
    """
    rank: int
    combo_ids: list[int]  # IDs of selected combos
    active_combos: list[ActiveComboInfo] = field(default_factory=list)  # Detailed combo info
    player_attrs: list[PlayerAttribute] = field(default_factory=list)  # Slot constraints
    total_reward: int = 0  # Total reward from active combos
    gain_ovr: int = 0
    gain_sal: int = 0
    gain_ap: int = 0
    
    @property
    def total_gain(self) -> float:
        """Weighted total gain (for ranking)."""
        return float(self.gain_ovr + self.gain_sal + self.gain_ap)


@dataclass
class StageAOutput:
    """
    Output from Stage A solver.
    
    Contains top-K abstract solutions.
    """
    solutions: list[StageASolution]
    solve_time_ms: float = 0.0
    total_models_found: int = 0


# =============================================================================
# STAGE B TYPES
# =============================================================================

@dataclass
class CandidatePlayer:
    """
    A player candidate for Stage B enumeration.
    
    Includes match_count for ranking.
    """
    card_id: int  # Unique card ID
    player_id: int  # Real player ID (for uniqueness constraint)
    team: str
    nationality: str
    event: str
    overall: int
    salary: float
    ap: int = 0
    match_count: int = 0  # How many combo attributes this player matches


@dataclass
class StageBInput:
    """
    Input for Stage B solver.
    
    Contains candidate players and the combos to satisfy.
    """
    position_type: Literal["forward", "defense"]
    stage_a_solution_rank: int  # Which Stage A solution this is for
    
    # Combos to satisfy (from Stage A solution)
    combo_ids: list[int]
    combo_facts: list[str]  # ASP facts for the specific combos
    
    # Candidate players (pre-filtered and ranked)
    players: list[CandidatePlayer] = field(default_factory=list)
    player_facts: list[str] = field(default_factory=list)  # ASP facts


@dataclass
class ConcreteLine:
    """
    A concrete line from Stage B enumeration.
    
    Contains actual player card IDs.
    """
    player_card_ids: list[int]  # Card IDs (3 for forward, 2 for defense)
    player_ids: list[int]  # Real player IDs (for display)
    activated_combo_ids: list[int]  # Which combos are activated
    total_ovr: int = 0
    total_salary: float = 0.0
    total_ap: int = 0


@dataclass
class StageBOutput:
    """
    Output from Stage B solver.
    
    Contains all concrete lines that satisfy the combos.
    """
    stage_a_solution_rank: int
    lines: list[ConcreteLine]
    solve_time_ms: float = 0.0


# =============================================================================
# SOLVER INTERFACES
# =============================================================================

class StageASolver(ABC):
    """
    Abstract interface for Stage A solver.
    
    ASP team implements this to provide the abstract optimization.
    """
    
    @abstractmethod
    def solve(self, input_data: StageAInput) -> StageAOutput:
        """
        Run Stage A optimization.
        
        Args:
            input_data: Combo templates and parameters
            
        Returns:
            Top-K abstract solutions with combo selections and gains
        """
        pass


class StageBSolver(ABC):
    """
    Abstract interface for Stage B solver.
    
    ASP team implements this to provide concrete line enumeration.
    """
    
    @abstractmethod
    def solve(self, input_data: StageBInput) -> StageBOutput:
        """
        Run Stage B enumeration.
        
        Args:
            input_data: Candidate players and combos to satisfy
            
        Returns:
            All concrete lines that satisfy the combos
        """
        pass
