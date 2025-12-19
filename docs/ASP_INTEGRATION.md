# ASP Team Integration Guide

This guide explains how to integrate the Clingo ASP solver with the Goal 1 pipeline.

If you are unsure about the exact input/output format, start with:
- `docs/ASP_DATA_CONTRACT.md` (backend ↔ ASP facts and expected outputs)

## Overview

The Goal 1 pipeline uses a **2-stage architecture**:

1. **Stage A**: Abstract optimization over combo templates (no real players)
2. **Stage B**: Concrete line enumeration with candidate players

The backend provides:
- Interface contracts (what your solver must implement)
- Input generators (facts/data in ASP-ready format)
- Pipeline orchestrator (coordinates Stage A → B → storage)
- Mock solvers (for development/testing)

**Your job**: Replace the mock solvers with real Clingo implementations.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GOAL 1 PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐           │
│  │  Stage A     │      │  Stage B     │      │   Storage    │           │
│  │  Input Gen   │─────>│  Input Gen   │─────>│  Results     │           │
│  └──────┬───────┘      └──────┬───────┘      └──────────────┘           │
│         │                     │                                          │
│         ▼                     ▼                                          │
│  ┌──────────────┐      ┌──────────────┐                                 │
│  │  Stage A     │      │  Stage B     │   <── ASP Team implements       │
│  │  Solver      │      │  Solver      │                                 │
│  └──────────────┘      └──────────────┘                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Understand the Interface Contracts

```python
from src.asp.interfaces import (
    # Stage A
    StageAInput,      # What you receive
    StageAOutput,     # What you return
    StageASolver,     # Interface to implement
    
    # Stage B
    StageBInput,      # What you receive
    StageBOutput,     # What you return  
    StageBSolver,     # Interface to implement
)
```

### 2. Run the Pipeline with Mock Solvers

```python
from src.asp.pipeline import run_goal1_pipeline

# This uses mock solvers - verify the pipeline works
result = run_goal1_pipeline("forward", "ovr", top_k=10)
print(f"Run ID: {result.run_id}")
print(f"Stage A solutions: {result.stage_a_solutions}")
print(f"Stage B lines: {result.stage_b_lines_total}")
```

### 3. Implement Your Solvers

Create `src/asp/clingo_solver.py`:

```python
from .interfaces import StageASolver, StageAInput, StageAOutput
# ... implement ...
```

### 4. Plug In Your Solvers

Update `src/asp/stage_a.py` and `src/asp/stage_b.py`:

```python
def get_stage_a_solver() -> StageASolver:
    from .clingo_solver import ClingoStageASolver
    return ClingoStageASolver()
```

---

## Stage A: Abstract Optimization

### What Stage A Does

Stage A finds the **top-K abstract combo solutions** without considering specific players.
It answers: "Which combinations of combos would give the best rewards?"

### Input You Receive

```python
@dataclass
class StageAInput:
    position_type: Literal["forward", "defense"]
    optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"]
    combo_facts: list[str]  # ASP-ready facts
    top_k: int = 200
    ovr_weight: float = 1.0
    sal_weight: float = 1.0
    ap_weight: float = 1.0
```

### Example `combo_facts`

```prolog
% Forward combo facts (3 conditions)
% Format: forward_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2, entry3).
forward_combo(5, 6, "SAL", team("OTT"), nationality("USA"), team("BOS")).
forward_combo(2, 5, "AP", team("DET"), event("SOTM"), nationality("GERMANY")).

% Defense combo facts (2 conditions)
% Format: defense_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2).
defense_combo(2, 1, "OVR", team("DAL"), event("HH")).
defense_combo(8, 3, "AP", nationality("CANADA"), team("TOR")).
```

### Output You Return

The ASP output format (from Clingo):

```
player_attr(1,team("DET")) player_attr(2,team("MTL")) player_attr(3,team("TOR"))
player_attr(1,event("SOTM")) player_attr(2,event("TOTW")) player_attr(3,event("TOTW"))
player_attr(1,nationality("GERMANY")) player_attr(3,nationality("DENMARK"))
fwd_active_combo(2,5,"AP") fwd_active_combo(39,3,"AP") fwd_active_combo(44,3,"AP")
total_reward(11)
```

Which maps to these Python dataclasses:

```python
@dataclass
class PlayerAttribute:
    slot: int           # 1, 2, 3 for forwards
    attr_type: str      # "team", "nationality", "event"
    attr_value: str     # e.g., "DET", "GERMANY"

@dataclass
class ActiveComboInfo:
    combo_id: int
    reward_amount: int
    reward_type: str    # "OVR", "SAL", "AP"

@dataclass
class StageASolution:
    rank: int
    combo_ids: list[int]
    active_combos: list[ActiveComboInfo]
    player_attrs: list[PlayerAttribute]  # Slot constraints
    total_reward: int
    gain_ovr: int = 0
    gain_sal: int = 0
    gain_ap: int = 0

@dataclass
class StageAOutput:
    solutions: list[StageASolution]
    solve_time_ms: float = 0.0
    total_models_found: int = 0
```

### Stage A Solver Interface

```python
class StageASolver(ABC):
    @abstractmethod
    def solve(self, input_data: StageAInput) -> StageAOutput:
        """
        Find top-K abstract combo solutions.
        
        Requirements:
        - Return up to input_data.top_k solutions
        - Solutions should be ranked by weighted gain
        - Combos in a solution should be "compatible" (can be activated together)
        """
        pass
```

### ASP Rules for Stage A (Example)

```prolog
% Select which combos to use (choice rule)
{ use_combo(C) : combo_reward(C, _, _) }.

% Combo compatibility constraint
% (Define what makes combos incompatible for your domain)

% Calculate total gain
total_ovr_gain(G) :- G = #sum { A, C : use_combo(C), combo_reward(C, ovr, A) }.
total_sal_gain(G) :- G = #sum { A, C : use_combo(C), combo_reward(C, sal, A) }.

% Maximize weighted gain
#maximize { A*W : use_combo(C), combo_reward(C, ovr, A), ovr_weight(W) }.
#maximize { A*W : use_combo(C), combo_reward(C, sal, A), sal_weight(W) }.

#show use_combo/1.
#show total_ovr_gain/1.
#show total_sal_gain/1.
```

---

## Stage B: Concrete Enumeration

### What Stage B Does

For each Stage A solution, Stage B enumerates **all concrete lines** using candidate players.
It answers: "What actual player combinations can realize this combo solution?"

### Input You Receive

```python
@dataclass
class CandidatePlayer:
    card_id: int       # Unique card ID
    player_id: int     # Real player ID (for uniqueness)
    team: str
    nationality: str
    event: str
    overall: int
    salary: float
    match_count: int   # How many combo attributes this player matches

@dataclass
class StageBInput:
    position_type: Literal["forward", "defense"]
    stage_a_solution_rank: int
    combo_ids: list[int]
    combo_facts: list[str]      # Selected combo facts
    players: list[CandidatePlayer]
    player_facts: list[str]     # ASP-ready player facts
```

### Example `player_facts`

```prolog
% Player facts
player(123, 456, "TOR", "CANADA", "BASE", 89, 5000000, 2).
player_team(123, "TOR").
player_nationality(123, "CANADA").
player_event(123, "BASE").
```

### Output You Return

```python
@dataclass
class ConcreteLine:
    player_card_ids: list[int]      # Card IDs (3 for forward, 2 for defense)
    player_ids: list[int]           # Real player IDs
    activated_combo_ids: list[int]
    total_ovr: int = 0
    total_salary: float = 0.0
    total_ap: int = 0

@dataclass
class StageBOutput:
    stage_a_solution_rank: int
    lines: list[ConcreteLine]
    solve_time_ms: float = 0.0
```

### Stage B Solver Interface

```python
class StageBSolver(ABC):
    @abstractmethod
    def solve(self, input_data: StageBInput) -> StageBOutput:
        """
        Enumerate all concrete lines for a Stage A solution.
        
        Requirements:
        - Forward lines: 3 players, defense pairs: 2 players
        - No duplicate player_id within a line
        - Symmetry breaking: {p1,p2,p3} == {p3,p1,p2} (same line)
        - Return ALL valid lines (not just top-K)
        """
        pass
```

### ASP Rules for Stage B (Example)

```prolog
% Forward line: select 3 cards
3 { in_line(C) : player(C, _, _, _, _, _, _, _) } 3.

% No duplicate real players (by player_id)
:- in_line(C1), in_line(C2), C1 != C2,
   player(C1, P, _, _, _, _, _, _),
   player(C2, P, _, _, _, _, _, _).

% Symmetry breaking (canonical ordering by card_id)
:- in_line(C1), in_line(C2), in_line(C3), C1 >= C2.
:- in_line(C2), in_line(C3), C2 >= C3.

% Check combo activation
combo_satisfied(ComboID) :-
    selected_combo(ComboID, _, _, T1, K1, T2, K2, T3, K3),
    in_line(C1), player_team(C1, K1), % or nationality/event based on T1
    in_line(C2), player_nationality(C2, K2),
    in_line(C3), player_event(C3, K3).

% All selected combos must be satisfied
:- selected_combo(C, _, _, _, _, _, _, _, _), not combo_satisfied(C).

% Calculate totals
total_ovr(T) :- T = #sum { O, C : in_line(C), player(C, _, _, _, _, O, _, _) }.

#show in_line/1.
#show total_ovr/1.
```

---

## Testing Your Implementation

### Unit Tests

```python
# tests/test_asp_solver.py
from src.asp.interfaces import StageAInput, StageASolution
from src.asp.clingo_solver import ClingoStageASolver  # Your implementation

def test_stage_a_returns_solutions():
    solver = ClingoStageASolver()
    input_data = StageAInput(
        position_type="forward",
        optimization_mode="ovr",
        combo_facts=["combo_reward(1, ovr, 2).", "combo_reward(2, ovr, 3)."],
        top_k=5,
    )
    
    output = solver.solve(input_data)
    
    assert len(output.solutions) > 0
    assert all(isinstance(s, StageASolution) for s in output.solutions)
```

### Integration Tests

```python
from src.asp.pipeline import Goal1Pipeline
from src.asp.clingo_solver import ClingoStageASolver, ClingoStageBSolver

def test_pipeline_with_clingo():
    pipeline = Goal1Pipeline(
        stage_a_solver=ClingoStageASolver(),
        stage_b_solver=ClingoStageBSolver(),
    )
    
    result = pipeline.run(
        position_type="forward",
        optimization_mode="ovr",
        top_k=10,
        store_results=False,
    )
    
    assert result.stage_a_solutions > 0
```

---

## Data Access

### Getting Raw Data (for verification)

```python
from src.core.data import get_data_loader

loader = get_data_loader()

# Players
forwards = loader.get_forwards()      # List[ForwardPlayer]
defense = loader.get_defense()        # List[DefensePlayer]

# Combos
fwd_combos = loader.get_forward_combos()    # List[ForwardLineCombo]
def_combos = loader.get_defense_combos()    # List[DefenseLineCombo]

# Player attributes
for p in forwards[:3]:
    print(f"Card {p.id}: {p.first_name} {p.last_name}")
    print(f"  Player ID: {p.player_id}")
    print(f"  Team: {p.team}, Nat: {p.nationality}, Event: {p.event}")
    print(f"  OVR: {p.overall}, Salary: {p.salary}")
```

### Important: Card ID vs Player ID

- `card_id` (model field `id`): Unique per card (same player can have multiple cards)
- `player_id`: Real player identity (shared across cards)

**Rule**: A line cannot have two cards of the same `player_id`.

---

## Pipeline Configuration

### Default Weights (from GOAL_1.md)

```python
# Forward combinations
ovr_weight = 3.0
sal_weight = 1.0

# Defense combinations
ovr_weight = 2.0
sal_weight = 1.0

# AP weight (when included)
ap_weight = 1.0
```

### Running Different Modes

```python
from src.asp.pipeline import run_goal1_pipeline

# OVR only
run_goal1_pipeline("forward", "ovr")

# Salary only
run_goal1_pipeline("defense", "sal")

# Combined (uses weights)
run_goal1_pipeline("forward", "ovr_sal")
run_goal1_pipeline("forward", "ovr_sal_ap")
```

---

## File Structure

```
src/asp/
├── __init__.py           # Exports all public symbols
├── interfaces.py         # Interface contracts (DO NOT MODIFY)
├── stage_a.py           # Stage A generator + mock solver
├── stage_b.py           # Stage B generator + mock solver
├── pipeline.py          # Pipeline orchestrator
└── clingo_solver.py     # YOUR IMPLEMENTATION GOES HERE
```

---

## Checklist for ASP Team

- [ ] Read this guide and understand the 2-stage architecture
- [ ] Run the pipeline with mock solvers to verify setup
- [ ] Implement `ClingoStageASolver` in `clingo_solver.py`
- [ ] Implement `ClingoStageBSolver` in `clingo_solver.py`
- [ ] Write unit tests for your solvers
- [ ] Update `get_stage_a_solver()` and `get_stage_b_solver()` to use your implementations
- [ ] Run full pipeline with your solvers
- [ ] Verify results appear in `/best/{pos}/{mode}` endpoint

---

## Questions?

Contact the backend team if you need:
- Changes to input/output formats
- Additional data in the facts
- Different constraint handling
- Performance optimizations
