"""
Goal 1 Pipeline Orchestrator.

This module coordinates the full Goal 1 pipeline:
1. Stage A: Abstract optimization
2. Stage B: Concrete line enumeration
3. Storage: Persist results to database

Usage:
    from src.asp.pipeline import Goal1Pipeline
    
    pipeline = Goal1Pipeline()
    run_id = pipeline.run(
        position_type="forward",
        optimization_mode="ovr",
        top_k=200,
    )
"""

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Literal, Optional

from ..core.data import get_data_loader, get_results_store
from .interfaces import StageASolver, StageBSolver, ConcreteLine
from .stage_a import StageAInputGenerator, get_stage_a_solver
from .stage_b import StageBInputGenerator, get_stage_b_solver


@dataclass
class PipelineConfig:
    """Configuration for Goal 1 pipeline run."""
    position_type: Literal["forward", "defense"]
    optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"]
    top_k: int = 200  # Number of Stage A solutions
    player_limit: int = 100  # Players per Stage B candidate pool
    max_lines_per_solution: int = 1000  # Cap on lines stored per Stage A solution
    store_results: bool = True  # Whether to persist to database


@dataclass
class PipelineResult:
    """Result of a Goal 1 pipeline run."""
    run_id: Optional[int]  # Database run ID (None if not stored)
    position_type: str
    optimization_mode: str
    stage_a_solutions: int
    stage_b_lines_total: int
    total_time_ms: float
    stage_a_time_ms: float
    stage_b_time_ms: float


class Goal1Pipeline:
    """
    Orchestrates the Goal 1 pipeline.
    
    Runs Stage A → Stage B → Storage for a given configuration.
    """
    
    def __init__(
        self,
        stage_a_solver: Optional[StageASolver] = None,
        stage_b_solver: Optional[StageBSolver] = None,
    ):
        """
        Initialize the pipeline.
        
        Args:
            stage_a_solver: Custom Stage A solver (defaults to mock)
            stage_b_solver: Custom Stage B solver (defaults to mock)
        """
        self.stage_a_generator = StageAInputGenerator()
        self.stage_b_generator = StageBInputGenerator()
        self.stage_a_solver = stage_a_solver or get_stage_a_solver()
        self.stage_b_solver = stage_b_solver or get_stage_b_solver()
        self.results_store = get_results_store()
        self.loader = get_data_loader()
    
    def run(
        self,
        position_type: Literal["forward", "defense"],
        optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
        top_k: int = 200,
        player_limit: int = 100,
        store_results: bool = True,
    ) -> PipelineResult:
        """
        Run the full Goal 1 pipeline.
        
        Args:
            position_type: "forward" or "defense"
            optimization_mode: Which metrics to optimize
            top_k: Number of Stage A solutions to generate
            player_limit: Max players per Stage B candidate pool
            store_results: Whether to persist results to database
            
        Returns:
            PipelineResult with run statistics
        """
        config = PipelineConfig(
            position_type=position_type,
            optimization_mode=optimization_mode,
            top_k=top_k,
            player_limit=player_limit,
            store_results=store_results,
        )
        
        return self._execute(config)
    
    def _execute(self, config: PipelineConfig) -> PipelineResult:
        """Execute the pipeline with given configuration."""
        start_time = time.time()
        
        # Create run in database (if storing)
        run_id = None
        if config.store_results:
            run_id = self._create_run(config)
        
        # Stage A: Abstract optimization
        stage_a_start = time.time()
        stage_a_output = self._run_stage_a(config)
        stage_a_time = (time.time() - stage_a_start) * 1000
        
        # Store Stage A results
        if config.store_results and run_id:
            self._store_stage_a_results(run_id, stage_a_output)
        
        # Stage B: Concrete enumeration for each Stage A solution
        stage_b_start = time.time()
        total_lines = 0
        
        for solution in stage_a_output.solutions:
            stage_b_output = self._run_stage_b(config, solution)
            
            if config.store_results and run_id:
                stored = self._store_stage_b_results(
                    run_id,
                    stage_b_output.lines,
                    config.max_lines_per_solution,
                )
                total_lines += stored
            else:
                total_lines += len(stage_b_output.lines)
        
        stage_b_time = (time.time() - stage_b_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        return PipelineResult(
            run_id=run_id,
            position_type=config.position_type,
            optimization_mode=config.optimization_mode,
            stage_a_solutions=len(stage_a_output.solutions),
            stage_b_lines_total=total_lines,
            total_time_ms=total_time,
            stage_a_time_ms=stage_a_time,
            stage_b_time_ms=stage_b_time,
        )
    
    def _create_run(self, config: PipelineConfig) -> int:
        """Create a new run entry in the database."""
        # Compute dataset hash for reproducibility
        dataset_hash = self._compute_dataset_hash(config.position_type)
        
        parameters = {
            "top_k": config.top_k,
            "player_limit": config.player_limit,
            "max_lines_per_solution": config.max_lines_per_solution,
        }
        
        return self.results_store.create_run(
            position_type=config.position_type,
            optimization_mode=config.optimization_mode,
            parameters=parameters,
            dataset_hash=dataset_hash,
        )
    
    def _compute_dataset_hash(self, position_type: str) -> str:
        """Compute a hash of the dataset for this position type."""
        # Get player count and combo count as a simple hash basis
        if position_type == "forward":
            players = self.loader.get_forwards()
            combos = self.loader.get_forward_combos()
        else:
            players = self.loader.get_defense()
            combos = self.loader.get_defense_combos()
        
        hash_input = f"{len(players)}:{len(combos)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    def _run_stage_a(self, config: PipelineConfig):
        """Run Stage A optimization."""
        input_data = self.stage_a_generator.generate(
            position_type=config.position_type,
            optimization_mode=config.optimization_mode,
            top_k=config.top_k,
        )
        return self.stage_a_solver.solve(input_data)
    
    def _run_stage_b(self, config: PipelineConfig, stage_a_solution):
        """Run Stage B enumeration for a single Stage A solution."""
        input_data = self.stage_b_generator.generate(
            stage_a_solution=stage_a_solution,
            position_type=config.position_type,
            player_limit=config.player_limit,
        )
        return self.stage_b_solver.solve(input_data)
    
    def _store_stage_a_results(self, run_id: int, stage_a_output) -> None:
        """Store Stage A results in database."""
        for solution in stage_a_output.solutions:
            self.results_store.store_stage_a_result(
                run_id=run_id,
                solution_rank=solution.rank,
                combo_ids=solution.combo_ids,
                gain_ovr=solution.gain_ovr,
                gain_sal=solution.gain_sal,
                gain_ap=solution.gain_ap,
            )
    
    def _store_stage_b_results(
        self,
        run_id: int,
        lines: list[ConcreteLine],
        max_lines: int,
    ) -> int:
        """
        Store Stage B concrete lines in database.
        
        Returns number of lines stored (after deduplication).
        """
        stored = 0
        
        for line in lines[:max_lines]:
            # Compute ranking score
            ranking_score = self._compute_ranking_score(line)
            
            line_id = self.results_store.store_concrete_line(
                run_id=run_id,
                player_ids=line.player_card_ids,  # Using card IDs
                activated_combo_ids=line.activated_combo_ids,
                total_ovr=line.total_ovr,
                total_salary=line.total_salary,
                total_ap=line.total_ap,
                ranking_score=ranking_score,
            )
            
            if line_id:  # Not a duplicate
                stored += 1
        
        return stored
    
    def _compute_ranking_score(self, line: ConcreteLine) -> float:
        """
        Compute a ranking score for a concrete line.
        
        This is used to sort lines in the results endpoint.
        Higher is better.
        """
        # Simple formula: total OVR + (bonus from combos)
        # Could be made more sophisticated based on mode
        combo_bonus = len(line.activated_combo_ids) * 2
        return float(line.total_ovr + combo_bonus)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def run_goal1_pipeline(
    position_type: Literal["forward", "defense"],
    optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
    top_k: int = 200,
    player_limit: int = 100,
    store_results: bool = True,
) -> PipelineResult:
    """
    Convenience function to run the Goal 1 pipeline.
    
    Usage:
        from src.asp.pipeline import run_goal1_pipeline
        
        result = run_goal1_pipeline("forward", "ovr")
        print(f"Run ID: {result.run_id}")
        print(f"Total lines: {result.stage_b_lines_total}")
    """
    pipeline = Goal1Pipeline()
    return pipeline.run(
        position_type=position_type,
        optimization_mode=optimization_mode,
        top_k=top_k,
        player_limit=player_limit,
        store_results=store_results,
    )
