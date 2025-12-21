"""
Line combination models for NHL 26 Line Combos Optimizer.

Contains combo conditions and line combo models (forward 3-player, defense 2-player).
"""

from pydantic import BaseModel, Field

from .enums import RewardType


class ComboCondition(BaseModel):
    """A single condition in a line combination."""
    type: str = Field(..., description="Condition type: team, nationality, or event")
    key: str = Field(..., description="Condition value to match")


class LineComboBase(BaseModel):
    """Base model for line combinations."""
    id: int = Field(..., description="Database auto-increment ID (unique identifier)")
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
