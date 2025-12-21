"""
Goal 1 result models for NHL 26 Line Combos Optimizer.

Contains models for storing and retrieving Goal 1 pipeline results.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .enums import OptimizationMode, PositionType


class Goal1Run(BaseModel):
    """
    Metadata for a Goal 1 pipeline run.
    
    Each run captures the parameters and timestamp for reproducibility.
    """
    id: Optional[int] = Field(default=None, description="Database ID (auto-assigned)")
    run_timestamp: str = Field(..., description="ISO format timestamp")
    position_type: PositionType = Field(..., description="forward or defense")
    optimization_mode: OptimizationMode = Field(..., description="Optimization target")
    parameters: dict = Field(default_factory=dict, description="Run parameters (K, LIMIT, weights)")
    dataset_hash: Optional[str] = Field(default=None, description="Hash of dataset for reproducibility")


class Goal1StageAResult(BaseModel):
    """
    Stage A result: abstract combo selection.
    
    Represents a single solution from Stage A optimization,
    containing selected combo IDs and their total gains.
    """
    id: Optional[int] = Field(default=None, description="Database ID (auto-assigned)")
    run_id: int = Field(..., description="Reference to Goal1Run")
    solution_rank: int = Field(..., ge=1, description="Rank of this solution (1 = best)")
    combo_ids: list[int] = Field(..., description="Selected combo IDs")
    gain_ovr: int = Field(default=0, description="Total OVR bonus from selected combos")
    gain_sal: int = Field(default=0, description="Total SAL bonus from selected combos")
    gain_ap: int = Field(default=0, description="Total AP bonus from selected combos")


class Goal1ConcreteLine(BaseModel):
    """
    Stage B result: concrete line with real players.
    
    Represents a single concrete line that realizes a Stage A solution.
    Contains player IDs and computed metrics.
    """
    id: Optional[int] = Field(default=None, description="Database ID (auto-assigned)")
    run_id: int = Field(..., description="Reference to Goal1Run")
    stage_a_solution_id: Optional[int] = Field(default=None, description="Reference to StageA solution")
    player_ids: list[int] = Field(..., description="Player card IDs in this line")
    activated_combo_ids: list[int] = Field(..., description="Combos activated by this line")
    total_ovr: int = Field(default=0, description="Sum of player OVRs + bonuses")
    total_salary: float = Field(default=0.0, description="Sum of player salaries")
    total_ap: int = Field(default=0, description="Sum of player AP costs")
    ranking_score: float = Field(default=0.0, description="Computed score for ordering")
    
    def line_key(self) -> str:
        """
        Return a canonical key for deduplication.
        
        Lines with the same players (regardless of order) get the same key.
        """
        return ",".join(str(pid) for pid in sorted(self.player_ids))
