"""
Models package for NHL 26 Line Combos Optimizer.

This package contains all Pydantic models organized by domain:
- enums: All enumeration types
- players: Player models (forwards, defense, goalies)
- combos: Line combination models
- api: API request/response models
- goal1: Goal 1 pipeline result models

All models are re-exported here for backward compatibility.
"""

# Enums
from .enums import (
    Position,
    RewardType,
    ConditionType,
    OptimizationTarget,
    OptimizationMode,
    PositionType,
)

# Player models
from .players import (
    PlayerBase,
    ForwardPlayer,
    DefensePlayer,
    Goalie,
    Player,
)

# Combo models
from .combos import (
    ComboCondition,
    LineComboBase,
    ForwardLineCombo,
    DefenseLineCombo,
    LineCombo,
)

# API models
from .api import (
    OptimizationConstraints,
    OptimizationRequest,
    ActiveCombo,
    LineSolution,
    OptimizationResponse,
)

# Goal 1 models
from .goal1 import (
    Goal1Run,
    Goal1StageAResult,
    Goal1ConcreteLine,
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
]
