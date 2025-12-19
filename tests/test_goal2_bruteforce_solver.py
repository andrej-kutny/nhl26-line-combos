from __future__ import annotations

from dataclasses import dataclass

from src.asp.goal2_bruteforce import combo_activates
from src.core.models.combos import ComboCondition, ForwardLineCombo
from src.core.models.enums import RewardType


@dataclass(frozen=True)
class StubPlayer:
    team: str
    nationality: str
    event: str

    def matches_condition(self, condition_type: str, condition_key: str) -> bool:
        condition_type = condition_type.lower()
        condition_key = condition_key.upper()
        if condition_type == "team":
            return self.team.upper() == condition_key
        if condition_type == "nationality":
            return self.nationality.upper() == condition_key
        if condition_type == "event":
            return self.event.upper() == condition_key
        return False


def test_combo_activates_is_order_independent_for_forward():
    # Conditions: TEAM=DET, TEAM=DET, EVENT=FANT
    combo = ForwardLineCombo(
        id=1,
        reward_amount=20,
        reward_type=RewardType.SAL,
        condition1=ComboCondition(type="team", key="DET"),
        condition2=ComboCondition(type="team", key="DET"),
        condition3=ComboCondition(type="event", key="FANT"),
    )

    p1 = StubPlayer(team="DET", nationality="CANADA", event="GM")
    p2 = StubPlayer(team="DET", nationality="USA", event="HH")
    p3 = StubPlayer(team="CHI", nationality="CANADA", event="FANT")

    assert combo_activates([p1, p2, p3], combo) is True
    assert combo_activates([p3, p2, p1], combo) is True


def test_combo_activates_false_when_condition_missing():
    combo = ForwardLineCombo(
        id=1,
        reward_amount=20,
        reward_type=RewardType.SAL,
        condition1=ComboCondition(type="team", key="DET"),
        condition2=ComboCondition(type="team", key="DET"),
        condition3=ComboCondition(type="event", key="FANT"),
    )

    p1 = StubPlayer(team="DET", nationality="CANADA", event="GM")
    p2 = StubPlayer(team="CHI", nationality="USA", event="HH")
    p3 = StubPlayer(team="CHI", nationality="CANADA", event="FANT")

    assert combo_activates([p1, p2, p3], combo) is False

