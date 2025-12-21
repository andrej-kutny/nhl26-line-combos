# Goal 2 ASP Integration Guide

## Overview

Goal 2 is the **interactive line optimization** goal. Unlike Goal 1 (which is batch-oriented with abstraction), Goal 2 directly optimizes concrete lines with real players from user-provided filters.

### Key Differences from Goal 1

| Aspect | Goal 1 | Goal 2 |
|--------|--------|--------|
| **Flow** | Stage A (abstract) → Stage B (concrete) | Direct concrete optimization |
| **Trigger** | Batch (when combos/players change) | Interactive (user request) |
| **Combos** | Mandatory constraints from solution | Optional, can filter |
| **Performance** | Slower (2-stage pipeline) | Faster (direct optimization) |
| **Use Case** | Batch ranking of best combos | Real-time player selection |

## Architecture

### Module Structure

```
backend/src/asp/
├── interfaces.py          # Goal2Input, Goal2Output, Goal2Solver contracts
├── goal2.py              # Goal2InputGenerator, ClingoGoal2Solver
├── goal2_pipeline.py     # Goal2Pipeline orchestrator
└── g2/                   # ASP rule files
    ├── common.lp         # Shared rules (player matching, attributes)
    ├── fwd_main.lp       # Forward line formation & combo matching
    ├── def_main.lp       # Defense pair formation & combo matching
    ├── fwd_ovr_description.lp   # OVR optimization for forwards
    ├── fwd_sal_description.lp   # SAL optimization for forwards
    ├── fwd_ap_description.lp    # AP optimization for forwards
    ├── def_ovr_description.lp   # OVR optimization for defense
    ├── def_sal_description.lp   # SAL optimization for defense
    └── def_ap_description.lp    # AP optimization for defense
```

## Components

### 1. Goal2Input Interface

```python
@dataclass
class Goal2Input:
    position_type: Literal["forward", "defense"]
    optimization_target: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"]
    players: list[CandidatePlayer]
    player_facts: list[str]
    combo_facts: list[str]
    required_combo_ids: list[int]  # Optional: enforce specific combos
    num_solutions: int = 10
    ovr_weight: float = 1.0
    sal_weight: float = 1.0
    ap_weight: float = 1.0
```

### 2. Goal2Output Interface

```python
@dataclass
class Goal2Output:
    lines: list[Goal2ConcreteLineResult]  # Ranked by optimization target
    solve_time_ms: float
    total_models_found: int

@dataclass
class Goal2ConcreteLineResult:
    rank: int
    player_card_ids: list[int]
    player_ids: list[int]
    activated_combo_ids: list[int]
    total_base_ovr: int
    total_base_salary: float
    total_base_ap: int
    ovr_bonus: int
    sal_bonus: int
    ap_bonus: int
    
    @property
    def total_ovr(self) -> int:
        return self.total_base_ovr + self.ovr_bonus
    
    @property
    def total_salary(self) -> float:
        return self.total_base_salary - self.sal_bonus
    
    @property
    def total_ap(self) -> int:
        return self.total_base_ap - self.ap_bonus
```

### 3. Goal2Solver Interface

```python
class Goal2Solver(ABC):
    @abstractmethod
    def solve(self, input_data: Goal2Input) -> Goal2Output:
        """
        Run Goal 2 optimization.
        
        Args:
            input_data: Players, combos, and optimization parameters
            
        Returns:
            Top-N concrete lines ranked by optimization target
        """
        pass
```

## Usage

### Basic Usage

```python
from src.asp.goal2_pipeline import Goal2Pipeline
from src.asp.interfaces import CandidatePlayer

# Create candidate players
players = [
    CandidatePlayer(
        card_id=1, player_id=101,
        team="DET", nationality="USA", event="OVR",
        overall=88, salary=5000.0, ap=10
    ),
    # ... more players
]

# Run Goal 2 optimization
pipeline = Goal2Pipeline()
result = pipeline.run(
    position_type="forward",
    optimization_target="ovr",
    players=players,
    num_solutions=10
)

# Use results
for line in result.output.lines:
    print(f"Rank {line.rank}: OVR={line.total_ovr}, Cards={line.player_card_ids}")
```

### With Required Combos

```python
result = pipeline.run(
    position_type="forward",
    optimization_target="ovr",
    players=players,
    combo_ids=[1, 2, 3],  # Enforce these combos
    num_solutions=10
)
```

### Different Optimization Targets

```python
# Single-metric optimization
result = pipeline.run(
    position_type="forward",
    optimization_target="ovr",  # Only OVR bonus
    players=players
)

# Combined optimization
result = pipeline.run(
    position_type="defense",
    optimization_target="ovr_sal",  # OVR and SAL bonuses
    players=players
)

# All metrics
result = pipeline.run(
    position_type="forward",
    optimization_target="ovr_sal_ap",  # All bonuses
    players=players
)
```

## Implementation Details

### Input Generation (Goal2InputGenerator)

1. **Player Facts**: Convert `CandidatePlayer` objects to ASP facts
   ```asp
   player(CardID, PlayerID, Nationality, Team, Event, Overall, Salary).
   ovr(CardID, Overall).
   salary_val(CardID, Salary).
   ap_val(CardID, AP).
   card_player(CardID, PlayerID).
   ```

2. **Combo Facts**: Convert combo definitions to ASP facts
   ```asp
   % Forward
   fwd_combo(ID, RewardAmount, "REWARD_TYPE", Cond1, Cond2, Cond3).
   
   % Defense
   def_combo(ID, RewardAmount, "REWARD_TYPE", Cond1, Cond2).
   ```

3. **Weight Calculation**: Set optimization weights
   - `ovr`: (1.0, 0.0, 0.0)
   - `sal`: (0.0, 1.0, 0.0)
   - `ap`: (0.0, 0.0, 1.0)
   - `ovr_sal`: (3.0/2.0, 1.0, 0.0)  # Position-dependent
   - `ovr_sal_ap`: (3.0/2.0, 1.0, 1.0)

### ASP Rule Flow

1. **common.lp**: Shared rules
   - Extract player attributes from `player/7` facts
   - Match players against combo requirements
   - Define boost type extraction

2. **fwd_main.lp / def_main.lp**: Position-specific rules
   - Form valid lines (3 forwards, 2 defense)
   - Apply symmetry breaking (higher OVR first)
   - Match combos to lines
   - Determine boosted lines

3. **fwd_{target}_description.lp / def_{target}_description.lp**: Optimization
   - Calculate totals (base + bonuses)
   - Define choice/limit for solutions
   - Maximize weighted objective

### Solver (ClingoGoal2Solver)

```python
class ClingoGoal2Solver(Goal2Solver):
    def solve(self, input_data: Goal2Input) -> Goal2Output:
        # 1. Select appropriate rule files based on position & target
        # 2. Generate Clingo program
        # 3. Load rules and facts
        # 4. Call Clingo solver
        # 5. Parse models
        # 6. Return ranked results
```

### Pipeline (Goal2Pipeline)

```python
class Goal2Pipeline:
    def run(...) -> Goal2PipelineResult:
        # 1. Generate input via Goal2InputGenerator
        # 2. Solve via Goal2Solver
        # 3. Time the operation
        # 4. Return result with timing info
```

## Testing

### Test Files

- **tests/test_goal2_integration.py**: Integration tests
  - Input generation
  - ASP rule tests (if Clingo available)
  - End-to-end pipeline tests

- **tests/test_goal2_solvers.py**: Unit tests
  - Weight calculation
  - Fact generation
  - Model parsing
  - Pipeline orchestration

### Running Tests

```bash
# Run all Goal 2 tests
pytest backend/tests/test_goal2_*.py -v

# Run specific test
pytest backend/tests/test_goal2_integration.py::TestGoal2InputGenerator -v

# Run with output
pytest backend/tests/test_goal2_solvers.py -v -s
```

### Test Coverage

- ✅ Input generation (forward & defense)
- ✅ Weight calculation (all optimization targets)
- ✅ Fact generation (players & combos)
- ✅ Model parsing (forward & defense lines)
- ✅ Pipeline execution
- ✅ Edge cases (empty players, single player, etc.)
- ⚠️ ASP rules (requires Clingo, skipped if not available)

## Error Handling

### Missing Clingo

If Clingo is not installed:

```python
# Tests will gracefully skip
pytest.skip("Clingo not available")

# Runtime will raise clear error
RuntimeError("Clingo not available. Install via: pip install clingo")
```

### Invalid Input

- Empty player list: Handled gracefully
- Insufficient players: ASP solver returns 0 models
- Invalid combo IDs: Silently ignored (not in database)

## Performance Characteristics

### Time Complexity

| Aspect | Complexity |
|--------|-----------|
| Input generation | O(P + C) |
| Clingo solve | O(2^n) worst case, typically much better |
| Model parsing | O(M × S) |

Where:
- P = number of players
- C = number of combos
- M = number of models found
- S = symbols per model

### Space Complexity

- Player facts: O(P)
- Combo facts: O(C)
- Models: O(M × S)

### Typical Performance

For ~100 players and ~50 combos:
- Input generation: < 1ms
- Clingo solve: 100-500ms
- Model parsing: < 10ms
- **Total: 100-510ms**

## Extending Goal 2

### Adding New Optimization Target

1. Create new `{pos}_{target}_description.lp` file in `backend/src/asp/g2/`
2. Define calculation rules for totals
3. Add weighting logic if needed
4. Update `goal2.py` weight calculation

### Adding New Constraint

1. Add constraint logic to `{pos}_main.lp`
2. Generate constraint facts in `Goal2InputGenerator._generate_combo_facts()`
3. Update test data

### Improving Solver Performance

1. Add more symmetry breaking in `{pos}_main.lp`
2. Use Clingo domain knowledge directives
3. Add heuristics for search order
4. Increase number of solver threads

## Relationship to Goal 1

Goal 2 reuses G1 infrastructure:
- Same `interfaces.py` for `CandidatePlayer`, combo structures
- Same `ClingoGoal2Solver` pattern as G1's `ClingoStageASolver`
- Same test patterns and mocking strategies
- Different ASP rules (g2/ vs g1a_abstraction/ & g1b_grounding/)

## Debugging

### Enable Clingo Debug Output

```python
# Patch solver to show ASP program
solver = ClingoGoal2Solver()

# Modify _clingo_solve to print program:
program = "\n".join([facts, rules])
print(program)  # View ASP program before solving
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "ASP file not found" | Wrong path resolution | Check `Path(__file__).parent` logic |
| 0 models returned | Unsatisfiable ASP program | Check facts validity, combos |
| Wrong bonuses calculated | Missing `multiplier()` facts | Add `multiplier("OVR", 1)` etc. |

## Future Improvements

1. **Streaming output**: Return results as they're found
2. **Cancellation**: Allow canceling long-running solves
3. **Heuristics**: Add user preferences for search order
4. **Caching**: Cache solver results for identical inputs
5. **Parallelization**: Run multiple solve operations in parallel
