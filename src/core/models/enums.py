"""
Enums for NHL 26 Line Combos Optimizer.

All enumeration types used throughout the application.
"""

from enum import Enum


class Position(str, Enum):
    """Player positions in the game."""
    FORWARD = "FWD"
    DEFENSE = "DEF"
    GOALIE = "G"
    # Specific forward positions
    CENTER = "C"
    LEFT_WING = "LW"
    RIGHT_WING = "RW"
    # Specific defense positions
    LEFT_DEFENSE = "LD"
    RIGHT_DEFENSE = "RD"


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


class OptimizationTarget(str, Enum):
    """What to optimize for (API requests)."""
    OVR = "ovr"          # Maximize overall rating
    SALARY = "salary"    # Minimize salary usage
    AP = "ap"            # Minimize ability points
    BALANCED = "balanced"  # Balance all factors


class OptimizationMode(str, Enum):
    """Optimization modes for Goal 1 pipeline."""
    OVR = "ovr"              # Maximize OVR bonus
    SAL = "sal"              # Maximize SAL bonus
    AP = "ap"                # Maximize AP bonus
    OVR_SAL = "ovr_sal"      # Weighted OVR + SAL
    OVR_SAL_AP = "ovr_sal_ap"  # Weighted OVR + SAL + AP


class PositionType(str, Enum):
    """Position types for Goal 1 results."""
    FORWARD = "forward"
    DEFENSE = "defense"
