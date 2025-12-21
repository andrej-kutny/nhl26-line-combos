"""
ASP module - Clingo integration, facts generation, and solver.

This module provides Goal 1 and Goal 2 ASP-based optimization:
- Goal 1: Stage A (abstract) → Stage B (concrete with combos)
- Goal 2: Direct concrete line optimization (interactive)

Current implementation uses Clingo with fallbacks for development.

Usage:
    # Goal 1 pipeline
    from src.asp.pipeline import Goal1Pipeline
    
    pipeline = Goal1Pipeline()
    result = pipeline.run("forward", "ovr")
    
    # Goal 2 pipeline
    from src.asp.goal2_pipeline import Goal2Pipeline
    
    pipeline = Goal2Pipeline()
    result = pipeline.run("forward", "ovr", players)
"""

# Interface contracts (for ASP team to implement)
from .interfaces import (
    # Stage A types
    StageAInput,
    StageAOutput,
    StageASolution,
    StageASolver,
    PlayerAttribute,
    ActiveComboInfo,
    # Stage B types
    StageBInput,
    StageBOutput,
    StageBSolver,
    CandidatePlayer,
    ConcreteLine,
    # Goal 2 types
    Goal2Input,
    Goal2Output,
    Goal2ConcreteLineResult,
    Goal2Solver,
)

# Input generators (backend-owned)
from .stage_a import StageAInputGenerator, get_stage_a_solver
from .stage_b import StageBInputGenerator, get_stage_b_solver
from .goal2 import Goal2InputGenerator, get_goal2_solver

# Pipeline orchestrators
from .pipeline import Goal1Pipeline, PipelineConfig, PipelineResult, run_goal1_pipeline
from .goal2_pipeline import Goal2Pipeline, Goal2PipelineConfig, Goal2PipelineResult

__all__ = [
    # Goal 1 Interfaces
    "StageAInput",
    "StageAOutput",
    "StageASolution",
    "StageASolver",
    "PlayerAttribute",
    "ActiveComboInfo",
    "StageBInput",
    "StageBOutput",
    "StageBSolver",
    "CandidatePlayer",
    "ConcreteLine",
    # Goal 2 Interfaces
    "Goal2Input",
    "Goal2Output",
    "Goal2ConcreteLineResult",
    "Goal2Solver",
    # Generators
    "StageAInputGenerator",
    "StageBInputGenerator",
    "Goal2InputGenerator",
    # Solvers
    "get_stage_a_solver",
    "get_stage_b_solver",
    "get_goal2_solver",
    # Pipelines
    "Goal1Pipeline",
    "PipelineConfig",
    "PipelineResult",
    "run_goal1_pipeline",
    "Goal2Pipeline",
    "Goal2PipelineConfig",
    "Goal2PipelineResult",
]