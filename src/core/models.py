"""
Core data models for NHL 26 Line Combos Optimizer.

These models represent the domain entities used throughout the application.
All teams (API, ASP, Frontend) should use these models for consistency.

Data Structure Reference:
- Players have: event, overall (OVR), nationality, league, team, position, ID
- Line combos have: reward_amount, reward_type (OVR/SAL/AP), conditions (type/key pairs)
- Forward combos require 3 players, Defense combos require 2 players
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class Position(str, Enum):
    """Player positions in the game."""
    FORWARD = "FWD"
    DEFENSE = "DEF"
    GOALIE = "G"
    # Specific forward positions (if available in data)
    CENTER = "C"
    LEFT_WING = "LW"
    RIGHT_WING = "RW"


class RewardType(str, Enum):
    """Types of rewards from line combinations."""
    OVR = "OVR"  # Overall rating bonus
    SAL = "SAL"  # Salary cap bonus (reduces effective salary)
    AP = "AP"    # Ability points bonus


class ConditionType(str, Enum):
    """Types of conditions for line combinations."""
    TEAM = "team"
    NATIONALITY = "nationality"
    EVENT = "event"


# =============================================================================
# PLAYER MODELS
# =============================================================================

class PlayerBase(BaseModel):
    """Base model for all player types."""
    id: str = Field(..., description="Unique card ID (card_id from dataset)")
    player_id: Optional[str] = Field(
        default=None, description="Underlying player identifier (string); used to avoid duplicates"
    )
    first_name: str = Field("", description="Player's first name")
    last_name: str = Field("", description="Player's last name")
    sub_position: Optional[str] = Field(
        default=None,
        description="Forward subtype (C/LW/RW) when available; None otherwise",
    )
    event: str = Field(..., description="Card event/release type (e.g., ICON, HH, CAP)")
    overall: int = Field(..., ge=1, le=99, description="Overall rating (OVR)")
    nationality: str = Field(..., description="Player nationality")
    league: str = Field(..., description="League (NHL, NHLAA, etc.)")
    team: str = Field(..., description="Team abbreviation")
    salary: Optional[int] = Field(default=None, description="Synthetic or real salary cap hit")
    ability_points: Optional[int] = Field(default=None, description="Synthetic or real AP cost")
    
    @property
    def full_name(self) -> str:
        """Return player's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def matches_condition(self, condition_type: str, condition_key: str) -> bool:
        """
        Check if player matches a line combo condition.
        
        This method is crucial for ASP integration - it determines
        which players can activate which line combinations.
        
        Args:
            condition_type: One of "team", "nationality", "event"
            condition_key: The value to match (e.g., "DET", "CANADA", "ICON")
            
        Returns:
            True if the player matches the condition
        """
        condition_type = condition_type.lower()
        condition_key = condition_key.upper()
        
        if condition_type == "team":
            return self.team.upper() == condition_key
        elif condition_type == "nationality":
            return self.nationality.upper() == condition_key
        elif condition_type == "event":
            return self.event.upper() == condition_key
        return False


class Player(PlayerBase):
    """Generic player model (can be forward or defense)."""
    position: Position = Field(..., description="Player position")


class ForwardPlayer(PlayerBase):
    """Forward player with position always set to FWD."""
    position: Position = Field(default=Position.FORWARD, description="Always FWD")
    # Future: Add specific position (C, LW, RW) when data is available
    # specific_position: Optional[str] = None


class DefensePlayer(PlayerBase):
    """Defense player with position always set to DEF."""
    position: Position = Field(default=Position.DEFENSE, description="Always DEF")


class Goalie(PlayerBase):
    """Goalie player model."""
    position: Position = Field(default=Position.GOALIE, description="Always G")


# =============================================================================
# LINE COMBINATION MODELS
# =============================================================================

class ComboCondition(BaseModel):
    """A single condition in a line combination."""
    type: str = Field(..., description="Condition type: team, nationality, or event")
    key: str = Field(..., description="Condition value to match")


class LineComboBase(BaseModel):
    """Base model for line combinations."""
    id: int = Field(..., description="Unique combo ID")
    reward_amount: int = Field(..., ge=0, description="Bonus amount")
    reward_type: RewardType = Field(..., description="Type of reward")
    
    def get_conditions(self) -> list[ComboCondition]:
        """Return list of conditions. Override in subclasses."""
        raise NotImplementedError


class ForwardLineCombo(LineComboBase):
    """
    Forward line combination (requires 3 players).
    
    Each condition (1, 2, 3) corresponds to a slot in the forward line.
    All three conditions must be satisfied for the combo to activate.
    """
    condition1: ComboCondition = Field(..., description="Condition for slot 1")
    condition2: ComboCondition = Field(..., description="Condition for slot 2")
    condition3: ComboCondition = Field(..., description="Condition for slot 3")
    
    def get_conditions(self) -> list[ComboCondition]:
        """Return all three conditions as a list."""
        return [self.condition1, self.condition2, self.condition3]


class DefenseLineCombo(LineComboBase):
    """
    Defense/Goalie line combination (requires 2 players).
    
    Each condition (1, 2) corresponds to a slot in the defense pair.
    Both conditions must be satisfied for the combo to activate.
    """
    condition1: ComboCondition = Field(..., description="Condition for slot 1")
    condition2: ComboCondition = Field(..., description="Condition for slot 2")
    
    def get_conditions(self) -> list[ComboCondition]:
        """Return both conditions as a list."""
        return [self.condition1, self.condition2]


# Type alias for any line combo
LineCombo = ForwardLineCombo | DefenseLineCombo


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================

class OptimizationConstraints(BaseModel):
    """
    Constraints for line optimization.
    
    These constraints are passed from the frontend to the API,
    then converted to ASP constraints by the solver.
    """
    min_ovr: int = Field(default=0, ge=0, le=99, description="Minimum player OVR")
    max_salary: Optional[int] = Field(default=None, description="Maximum total salary")
    max_ap: Optional[int] = Field(default=None, description="Maximum ability points")
    require_center: bool = Field(default=False, description="Require at least one center")
    excluded_player_ids: list[str] = Field(
        default_factory=list, description="Card IDs to exclude explicitly"
    )
    required_team: Optional[str] = Field(default=None, description="All players must be from this team")
    required_nationality: Optional[str] = Field(default=None, description="All players must have this nationality")
    required_event: Optional[str] = Field(default=None, description="All players must be from this event")


class OptimizationTarget(str, Enum):
    """What to optimize for."""
    OVR = "ovr"          # Maximize overall rating
    SALARY = "salary"    # Minimize salary usage
    AP = "ap"            # Minimize ability points
    BALANCED = "balanced"  # Balance all factors


class OptimizationRequest(BaseModel):
    """Request body for optimization endpoints."""
    constraints: OptimizationConstraints = Field(default_factory=OptimizationConstraints)
    optimization_target: OptimizationTarget = Field(default=OptimizationTarget.OVR)
    num_solutions: int = Field(default=5, ge=1, le=20, description="Number of solutions to return")


class ActiveCombo(BaseModel):
    """A line combo that is activated by the solution."""
    id: int
    reward_type: RewardType
    reward_amount: int
    description: str = Field("", description="Human-readable condition description")


class LineSolution(BaseModel):
    """A single solution for a line optimization."""
    rank: int = Field(..., description="Solution rank (1 = best)")
    players: list[Player] = Field(..., description="Players in this line")
    total_base_ovr: int = Field(..., description="Sum of player OVRs")
    ovr_bonus: int = Field(default=0, description="OVR bonus from combos")
    effective_ovr: int = Field(..., description="total_base_ovr + ovr_bonus")
    total_salary: int = Field(default=0, description="Total salary")
    total_ap: int = Field(default=0, description="Total ability points")
    active_combos: list[ActiveCombo] = Field(default_factory=list)


class OptimizationResponse(BaseModel):
    """Response from optimization endpoints."""
    success: bool = Field(default=True)
    message: str = Field(default="Optimization completed successfully")
    solutions: list[LineSolution] = Field(default_factory=list)
    computation_time_ms: int = Field(default=0, description="Time taken in milliseconds")
    candidates_evaluated: int = Field(default=0, description="Number of candidates considered")
