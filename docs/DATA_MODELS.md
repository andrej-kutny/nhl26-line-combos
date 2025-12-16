# Data Models

This document describes all data models used in the NHL 26 Line Combos Optimizer.

## Overview

All models are defined using [Pydantic](https://docs.pydantic.dev/) for:
- Type validation
- JSON serialization
- OpenAPI schema generation

**Location**: `src/core/models.py`

---

## Important Identity Concepts (Player vs Card)

The project data is **card-centric**:
- **`id`**: unique identifier for a specific card (database auto-increment)
- **`player_id`**: stable identifier for the real player across cards (`skater_id.csv`, `g_id.csv`)

In the current API models:
- **`PlayerBase.id`** = unique auto-increment ID (identifies a specific card)
- **`PlayerBase.player_id`** = identifies the real player (shared across multiple cards)

This distinction matters for:
- UI pickers (choose a specific card by `id` vs a wildcard "any card for player" by `player_id`)
- ASP solving (card-level attributes like event/team/overall depend on the specific card)

---

## Enumerations

### Position

Player positions in the game.

```python
class Position(str, Enum):
    FORWARD = "FWD"
    DEFENSE = "DEF"
    GOALIE = "G"
    CENTER = "C"
    LEFT_WING = "LW"
    RIGHT_WING = "RW"
```

### RewardType

Types of rewards from line combinations.

```python
class RewardType(str, Enum):
    OVR = "OVR"  # Overall rating bonus
    SAL = "SAL"  # Salary cap reduction
    AP = "AP"    # Ability points bonus
```

### OptimizationTarget

What to optimize for.

```python
class OptimizationTarget(str, Enum):
    OVR = "ovr"          # Maximize overall rating
    SALARY = "salary"    # Minimize salary
    AP = "ap"            # Minimize ability points
    BALANCED = "balanced"  # Balance all factors
```

---

## Player Models

### PlayerBase

Base model for all player types.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | **Auto-increment ID** (unique per card) |
| `player_id` | int | **Player ID** (shared across cards) |
| `first_name` | str | Player's first name |
| `last_name` | str | Player's last name |
| `img` | str | Card image filename |
| `position` | str | Card position (e.g., C/LW/RW/LD/RD) |
| `salary` | float | Card salary |
| `event` | str | Card event/release (e.g., ICON, CAP, TOTW) |
| `overall` | int | Overall rating (1-99) |
| `nationality` | str | Player nationality |
| `league` | str | League (NHL, NHLAA, etc.) |
| `team` | str | Team abbreviation |

**Properties**:
- `full_name`: Returns `"{first_name} {last_name}"`

**Methods**:
- `matches_condition(type, key)`: Check if player matches a combo condition

### ForwardPlayer

Forward player with `position = "FWD"`.

```json
{
  "id": 2029,
  "first_name": "SERGEI",
  "last_name": "FEDOROV",
  "event": "ICON",
  "overall": 86,
  "nationality": "Russia",
  "league": "NHLAA",
  "team": "DET",
  "position": "FWD"
}
```

### DefensePlayer

Defense player with `position = "DEF"`.

### Goalie

Goalie player with `position = "G"`.

### Player

Generic player model that can represent any position.

---

## Source Data Schemas (CSV in `data/`)

These CSV files are the source-of-truth inputs used by `src/core/data_loader.py`.

### `fwd_filtered.csv` / `def_filtered.csv`

These are **player card** datasets (one row = one card). Key columns:
- `player_id` (int, shared across multiple cards for the same player)
- `position` (card position like C/LW/RW/LD/RD)
- `POS` (broad group: FWD/DEF)
- `nationality`, `event`, `league`, `team`, `salary`, `overall`
- Note: CSV contains `card_id` (UUID) but it's not imported to database (we use auto-increment `id` instead)

### `g_filtered.csv`

Goalie card dataset (one row = one card). Key columns:
- `player_id`, `nationality`, `event`, `league`, `team`, `salary`, `overall`
- Note: CSV contains `card_id` (UUID) but it's not imported to database (we use auto-increment `id` instead)

### `skater_id.csv` / `g_id.csv`

Name lookup tables:
- `First name`, `Second name`, `player_id`

---

## Line Combination Models

### ComboCondition

A single condition in a line combination.

| Field | Type | Description |
|-------|------|-------------|
| `type` | str | Condition type: `team`, `nationality`, or `event` |
| `key` | str | Value to match (e.g., "DET", "CANADA", "ICON") |

```json
{
  "type": "team",
  "key": "DET"
}
```

### ForwardLineCombo

Forward line combination requiring 3 players.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique combo ID |
| `reward_amount` | int | Bonus amount |
| `reward_type` | RewardType | Type of reward (OVR/SAL/AP) |
| `condition1` | ComboCondition | Condition for slot 1 |
| `condition2` | ComboCondition | Condition for slot 2 |
| `condition3` | ComboCondition | Condition for slot 3 |

```json
{
  "id": 0,
  "reward_amount": 2,
  "reward_type": "OVR",
  "condition1": {"type": "team", "key": "TBL"},
  "condition2": {"type": "event", "key": "COM"},
  "condition3": {"type": "team", "key": "WSH"}
}
```

### DefenseLineCombo

Defense line combination requiring 2 players.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique combo ID |
| `reward_amount` | int | Bonus amount |
| `reward_type` | RewardType | Type of reward |
| `condition1` | ComboCondition | Condition for slot 1 |
| `condition2` | ComboCondition | Condition for slot 2 |

---

## API Request/Response Models

### OptimizationConstraints

User-defined constraints for optimization.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_ovr` | int | 0 | Minimum player OVR |
| `max_salary` | int? | null | Maximum total salary |
| `max_ap` | int? | null | Maximum ability points |
| `require_center` | bool | false | Require at least one center |
| `excluded_player_ids` | list[int] | [] | Player IDs to exclude |
| `required_team` | str? | null | All players must be from this team |
| `required_nationality` | str? | null | All players must have this nationality |
| `required_event` | str? | null | All players must be from this event |

```json
{
  "min_ovr": 80,
  "max_salary": 30000000,
  "max_ap": 9,
  "require_center": true,
  "excluded_player_ids": [2029, 1063],
  "required_team": null,
  "required_nationality": "CANADA",
  "required_event": null
}
```

### OptimizationRequest

Request body for optimization endpoints.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `constraints` | OptimizationConstraints | {} | Optimization constraints |
| `optimization_target` | OptimizationTarget | "ovr" | What to optimize |
| `num_solutions` | int | 5 | Number of solutions (1-20) |

```json
{
  "constraints": {
    "min_ovr": 80,
    "excluded_player_ids": []
  },
  "optimization_target": "ovr",
  "num_solutions": 5
}
```

### ActiveCombo

A combo activated by a line solution.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Combo ID |
| `reward_type` | RewardType | Type of reward |
| `reward_amount` | int | Bonus amount |
| `description` | str | Human-readable description |

```json
{
  "id": 5,
  "reward_type": "OVR",
  "reward_amount": 2,
  "description": "team=DET + event=ICON + nationality=RUSSIA"
}
```

### LineSolution

A single optimization solution.

| Field | Type | Description |
|-------|------|-------------|
| `rank` | int | Solution rank (1 = best) |
| `players` | list[Player] | Players in this line |
| `total_base_ovr` | int | Sum of player OVRs |
| `ovr_bonus` | int | OVR bonus from combos |
| `effective_ovr` | int | total_base_ovr + ovr_bonus |
| `total_salary` | int | Total salary |
| `total_ap` | int | Total ability points |
| `active_combos` | list[ActiveCombo] | Activated combos |

```json
{
  "rank": 1,
  "players": [
    {"id": 2029, "first_name": "SERGEI", ...},
    {"id": 1437, "first_name": "PLAYER", ...},
    {"id": 1221, "first_name": "PLAYER", ...}
  ],
  "total_base_ovr": 258,
  "ovr_bonus": 2,
  "effective_ovr": 260,
  "total_salary": 22500000,
  "total_ap": 7,
  "active_combos": [
    {"id": 5, "reward_type": "OVR", "reward_amount": 2, ...}
  ]
}
```

### OptimizationResponse

Response from optimization endpoints.

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether optimization succeeded |
| `message` | str | Status message |
| `solutions` | list[LineSolution] | Found solutions |
| `computation_time_ms` | int | Time taken in milliseconds |
| `candidates_evaluated` | int | Number of candidates considered |

```json
{
  "success": true,
  "message": "Found 5 solution(s)",
  "solutions": [...],
  "computation_time_ms": 145,
  "candidates_evaluated": 1766
}
```

---

## Data Flow Diagram

```
CSV Files                    Pydantic Models                 JSON Response
─────────────────────────────────────────────────────────────────────────────

fwd_filtered.csv    ──►    ForwardPlayer         ──►    { "id": 2029, ... }
def_filtered.csv    ──►    DefensePlayer         ──►    { "id": 380, ... }
g_filtered.csv      ──►    Goalie                ──►    { "id": 112, ... }

fwd_line_combos.csv ──►    ForwardLineCombo      ──►    { "id": 0, ... }
def_line_combos.csv ──►    DefenseLineCombo      ──►    { "id": 0, ... }

API Request         ──►    OptimizationRequest   ──►    (to ASP solver)
ASP Result          ──►    LineSolution          ──►    OptimizationResponse
```

---

## Validation Rules

Pydantic enforces these validations automatically:

| Model | Field | Rule |
|-------|-------|------|
| PlayerBase | overall | 1 ≤ value ≤ 99 |
| OptimizationConstraints | min_ovr | 0 ≤ value ≤ 99 |
| OptimizationRequest | num_solutions | 1 ≤ value ≤ 20 |
| LineComboBase | reward_amount | value ≥ 0 |

Invalid requests return HTTP 422 with validation errors.

---

## Related Documentation

- [Architecture](ARCHITECTURE.md) - System overview
- [ASP Integration](ASP_INTEGRATION.md) - Using models in ASP

