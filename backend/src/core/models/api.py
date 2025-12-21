"""
API request/response models for NHL 26 Line Combos Optimizer.

Contains Pydantic models for API endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .enums import RewardType, OptimizationTarget
from .players import Player


class OptimizationConstraints(BaseModel):
    """
    Constraints for line optimization.
    
    These constraints are passed from the frontend to the API,
    then converted to ASP constraints by the solver.
    """
    min_ovr: int = Field(default=0, ge=0, le=99, description="Minimum player OVR")
    max_salary: Optional[float] = Field(default=None, description="Maximum total salary")
    max_ap: Optional[int] = Field(default=None, description="Maximum ability points")
    require_center: bool = Field(default=False, description="Require at least one center")
    excluded_player_ids: list[int] = Field(default_factory=list, description="Player IDs to exclude")
    required_team: Optional[str] = Field(default=None, description="All players must be from this team")
    required_nationality: Optional[str] = Field(default=None, description="All players must have this nationality")
    required_event: Optional[str] = Field(default=None, description="All players must be from this event")


class OptimizationRequest(BaseModel):
    """Request body for optimization endpoints."""
    constraints: OptimizationConstraints = Field(default_factory=OptimizationConstraints)
    optimization_target: OptimizationTarget = Field(default=OptimizationTarget.OVR)
    num_solutions: int = Field(default=5, ge=1, le=20, description="Number of solutions to return")


class ActiveCombo(BaseModel):
    """A line combo that is activated by the solution."""
    id: int = Field(..., description="Line combo ID")
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
    total_salary: float = Field(default=0, description="Total salary")
    total_ap: int = Field(default=0, description="Total ability points")
    active_combos: list[ActiveCombo] = Field(default_factory=list)


class OptimizationResponse(BaseModel):
    """Response from optimization endpoints."""
    success: bool = Field(default=True)
    message: str = Field(default="Optimization completed successfully")
    solutions: list[LineSolution] = Field(default_factory=list)
    computation_time_ms: int = Field(default=0, description="Time taken in milliseconds")
    candidates_evaluated: int = Field(default=0, description="Number of candidates considered")
