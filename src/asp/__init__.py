"""
ASP module - Clingo integration, facts generation, and solver.

This module provides the Goal 1 pipeline with ASP-based optimization:
- Stage A: Abstract optimization over combo templates
- Stage B: Concrete line enumeration with real players

Current implementation uses mock solvers for development.
ASP team will replace with real Clingo implementations.

Usage:
    # Run the full pipeline
    from src.asp.pipeline import run_goal1_pipeline
    
    result = run_goal1_pipeline("forward", "ovr")
    print(f"Run ID: {result.run_id}")
    
    # Or use individual components
    from src.asp.stage_a import StageAInputGenerator, get_stage_a_solver
    from src.asp.stage_b import StageBInputGenerator, get_stage_b_solver
"""

# Interface contracts (for ASP team to implement)
from .interfaces import (
    # Stage A types
    StageAInput,
    StageAOutput,
    StageASolution,
    StageASolver,
    # Stage B types
    StageBInput,
    StageBOutput,
    StageBSolver,
    CandidatePlayer,
    ConcreteLine,
)

# Input generators (backend-owned)
from .stage_a import StageAInputGenerator, get_stage_a_solver
from .stage_b import StageBInputGenerator, get_stage_b_solver

# Pipeline orchestrator
from .pipeline import Goal1Pipeline, PipelineConfig, PipelineResult, run_goal1_pipeline

__all__ = [
    # Interfaces
    "StageAInput",
    "StageAOutput",
    "StageASolution",
    "StageASolver",
    "StageBInput",
    "StageBOutput",
    "StageBSolver",
    "CandidatePlayer",
    "ConcreteLine",
    # Generators
    "StageAInputGenerator",
    "StageBInputGenerator",
    # Solvers (mock until ASP implements)
    "get_stage_a_solver",
    "get_stage_b_solver",
    # Pipeline
    "Goal1Pipeline",
    "PipelineConfig",
    "PipelineResult",
    "run_goal1_pipeline",
]
