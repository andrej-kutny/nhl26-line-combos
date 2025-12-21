"""
Goal 2 Pipeline Orchestrator.

This module coordinates the Goal 2 optimization (interactive line suggestions).

Unlike Goal 1 which is batch-oriented (Stage A → Stage B),
Goal 2 directly optimizes concrete lines from user-provided filters.

Usage:
    from src.asp.goal2_pipeline import Goal2Pipeline
    
    pipeline = Goal2Pipeline()
    result = pipeline.run(
        position_type="forward",
        optimization_target="ovr",
        players=candidate_players,
        combo_ids=required_combos,
    )
"""

import time
from dataclasses import dataclass
from typing import Literal, Optional

from ..core.data import get_data_loader
from .interfaces import Goal2Solver, Goal2Output
from .goal2 import Goal2InputGenerator, get_goal2_solver


@dataclass
class Goal2PipelineConfig:
    """Configuration for Goal 2 pipeline run."""
    position_type: Literal["forward", "defense"]
    optimization_target: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"]
    num_solutions: int = 10
    enforce_all_combos: bool = True  # Enforce all selected combos


@dataclass
class Goal2PipelineResult:
    """Result of a Goal 2 pipeline run."""
    position_type: str
    optimization_target: str
    num_lines_found: int
    total_time_ms: float
    output: Goal2Output


class Goal2Pipeline:
    """
    Orchestrates the Goal 2 pipeline.
    
    Runs direct concrete line optimization for interactive goal.
    """
    
    def __init__(self, solver: Optional[Goal2Solver] = None):
        """
        Initialize the pipeline.
        
        Args:
            solver: Custom Goal 2 solver (defaults to Clingo)
        """
        self.input_generator = Goal2InputGenerator()
        self.solver = solver or get_goal2_solver()
        self.loader = get_data_loader()
    
    def run(
        self,
        position_type: Literal["forward", "defense"],
        optimization_target: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
        players: list,  # List of CandidatePlayer
        combo_ids: list[int] | None = None,
        num_solutions: int = 10,
    ) -> Goal2PipelineResult:
        """
        Run the Goal 2 optimization pipeline.
        
        Args:
            position_type: "forward" or "defense"
            optimization_target: Which metrics to optimize
            players: Candidate players for line building
            combo_ids: Specific combos to enforce (None = all)
            num_solutions: Number of solutions to return
            
        Returns:
            Goal2PipelineResult with optimized lines
        """
        start_time = time.time()
        
        # Generate input
        input_data = self.input_generator.generate(
            position_type=position_type,
            optimization_target=optimization_target,
            players=players,
            combo_ids=combo_ids,
            num_solutions=num_solutions,
        )
        
        # Solve
        output = self.solver.solve(input_data)
        
        total_time = (time.time() - start_time) * 1000
        
        return Goal2PipelineResult(
            position_type=position_type,
            optimization_target=optimization_target,
            num_lines_found=len(output.lines),
            total_time_ms=total_time,
            output=output,
        )
