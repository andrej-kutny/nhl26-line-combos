"""
Core module for NHL 26 Line Combos Optimizer.

This module provides:
- Data models (players, combos, API, Goal 1)
- Data access (DataLoader, Goal1ResultsStore)

All public classes and functions are re-exported here for convenience.
"""

# Models - re-export from models package
from .models import (
    # Enums
    Position,
    RewardType,
    ConditionType,
    OptimizationTarget,
    OptimizationMode,
    PositionType,
    # Player models
    PlayerBase,
    ForwardPlayer,
    DefensePlayer,
    Goalie,
    Player,
    # Combo models
    ComboCondition,
    LineComboBase,
    ForwardLineCombo,
    DefenseLineCombo,
    LineCombo,
    # API models
    OptimizationConstraints,
    OptimizationRequest,
    ActiveCombo,
    LineSolution,
    OptimizationResponse,
    # Goal 1 models
    Goal1Run,
    Goal1StageAResult,
    Goal1ConcreteLine,
)

# Data access - re-export from data package
from .data import (
    DataLoader,
    Goal1ResultsStore,
    get_data_loader,
    get_results_store,
)

__all__ = [
    # Enums
    "Position",
    "RewardType",
    "ConditionType",
    "OptimizationTarget",
    "OptimizationMode",
    "PositionType",
    # Player models
    "PlayerBase",
    "ForwardPlayer",
    "DefensePlayer",
    "Goalie",
    "Player",
    # Combo models
    "ComboCondition",
    "LineComboBase",
    "ForwardLineCombo",
    "DefenseLineCombo",
    "LineCombo",
    # API models
    "OptimizationConstraints",
    "OptimizationRequest",
    "ActiveCombo",
    "LineSolution",
    "OptimizationResponse",
    # Goal 1 models
    "Goal1Run",
    "Goal1StageAResult",
    "Goal1ConcreteLine",
    # Data access
    "DataLoader",
    "Goal1ResultsStore",
    "get_data_loader",
    "get_results_store",
]
