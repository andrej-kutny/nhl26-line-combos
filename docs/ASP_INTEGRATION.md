# ASP Team Integration Guide

This guide explains how the Clingo ASP solver is integrated with the API and how to extend it.

## Overview

The core integration is in place:

1. `src/api/routes/optimize.py` calls `src/asp/solver.py`
2. `src/asp/solver.py` loads data via `src/core/data_loader.py`, generates ASP facts, and runs Clingo
3. Rules live in `src/asp/rules/` (forward line, defense pair, full team)

In practice, most iteration happens in the ASP rule files (constraints and objectives) and in candidate filtering (to keep the search space tractable).

## Architecture

```
API Request → optimize.py → ASPSolver → Clingo → ASPSolver → API Response
                               ↓
                         data_loader.py
                               ↓
                           CSV Files
```

## Current implementation (what exists today)

The solver generates a minimal “world description” as facts and combines it with rule files:

- Player facts: `player(CardID, OVR, Team, Nationality, Event).`
- Duplicate prevention: `card_player(CardID, PlayerID).` plus a rule in `base.lp` forbidding selecting two cards with the same `PlayerID`.
- Optional numeric attributes: `salary(CardID, SalaryM).` and `ap(CardID, AP).`
- Combo facts: `fwd_combo(...)` and `def_combo(...)`
- Target selector: `opt_target("ovr"|"salary"|"ap"|"balanced").`

Combos are treated as “auto-activating”: if the selected players satisfy a combo’s
conditions (with an injective match from conditions → players), that combo’s bonus
is applied. A single line/pair may activate 0..N different combos simultaneously.

## Exporting combo CSVs to `.lp` facts (Goal 1 / debugging)

When you want to test ASP logic without relying on the backend fact generator, you can export the combo CSVs into small `.lp` fact files:

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
source venv/bin/activate
python scripts/export_combo_lp.py --data-dir data --out-dir out
```

This writes 6 files under `out/` (`fwd_*.lp` and `def_*.lp`) using the same predicate signatures as our ASP rules (`fwd_combo/9`, `def_combo/7`). The `out/` directory is ignored by git.

## Step 1: Understand the Data

### Players

The `DataLoader` provides player data. Access it like this:

```python
from src.core.data_loader import get_data_loader

loader = get_data_loader()

# Get all forwards
forwards = loader.get_forwards()  # List[ForwardPlayer]

# Get with filtering
filtered = loader.filter_players(
    forwards,
    min_ovr=80,
    team="DET",
    excluded_ids=[2029, 1063]
)

# Each player has:
for player in forwards:
    print(f"{player.id}: {player.full_name}")
    print(f"  OVR: {player.overall}")
    print(f"  Team: {player.team}")
    print(f"  Nationality: {player.nationality}")
    print(f"  Event: {player.event}")
```

### Line Combinations

```python
# Get forward combos (3-player)
fwd_combos = loader.get_forward_combos()  # List[ForwardLineCombo]

# Each combo has:
for combo in fwd_combos:
    print(f"Combo {combo.id}:")
    print(f"  Reward: {combo.reward_amount} {combo.reward_type}")
    
    # Get conditions
    conditions = combo.get_conditions()  # List of 3 conditions
    for i, cond in enumerate(conditions):
        print(f"  Slot {i+1}: {cond.type} = {cond.key}")
```

### Matching Players to Conditions

```python
# Check if a player matches a condition
player = forwards[0]
condition = combos[0].condition1

if player.matches_condition(condition.type, condition.key):
    print(f"{player.full_name} matches {condition.type}={condition.key}")

# Get all players matching a condition
matching = loader.get_players_matching_combo_condition(forwards, condition)
```

## Step 2: Generate ASP Facts

Facts are generated inside `src/asp/solver.py` in the current codebase.
The code below is a pedagogical sketch and may diverge from the actual implementation.

```python
from src.core.data_loader import get_data_loader

def generate_player_facts(players):
    """Generate ASP facts for players."""
    facts = []
    for p in players:
        # player(ID, OVR, Team, Nationality, Event).
        fact = f'player({p.id}, {p.overall}, "{p.team.lower()}", "{p.nationality.lower()}", "{p.event.lower()}").'
        facts.append(fact)
    return "\n".join(facts)

def generate_combo_facts(combos, is_forward=True):
    """Generate ASP facts for line combinations."""
    facts = []
    for c in combos:
        conditions = c.get_conditions()
        if is_forward:
            # fwd_combo(ID, RewardAmt, RewardType, Type1, Key1, Type2, Key2, Type3, Key3).
            fact = (
                f'fwd_combo({c.id}, {c.reward_amount}, {c.reward_type.value.lower()}, '
                f'"{conditions[0].type}", "{conditions[0].key.lower()}", '
                f'"{conditions[1].type}", "{conditions[1].key.lower()}", '
                f'"{conditions[2].type}", "{conditions[2].key.lower()}").'
            )
        else:
            # def_combo(ID, RewardAmt, RewardType, Type1, Key1, Type2, Key2).
            fact = (
                f'def_combo({c.id}, {c.reward_amount}, {c.reward_type.value.lower()}, '
                f'"{conditions[0].type}", "{conditions[0].key.lower()}", '
                f'"{conditions[1].type}", "{conditions[1].key.lower()}").'
            )
        facts.append(fact)
    return "\n".join(facts)
```

## Step 3: Write ASP Rules

Create rule files in `src/asp/rules/`:

### `base.lp` - Core Matching Rules

```prolog
% Match player to condition
matches(P, "team", K) :- player(P, _, Team, _, _), K = Team.
matches(P, "nationality", K) :- player(P, _, _, Nat, _), K = Nat.
matches(P, "event", K) :- player(P, _, _, _, Event), K = Event.

% Get player OVR
ovr(P, OVR) :- player(P, OVR, _, _, _).
```

### `forward_line.lp` - Forward Line Optimization

```prolog
% Include base rules
#include "base.lp".

% Select exactly 3 forwards (one per slot)
{ select(P, 1) : player(P, _, _, _, _) } = 1.
{ select(P, 2) : player(P, _, _, _, _) } = 1.
{ select(P, 3) : player(P, _, _, _, _) } = 1.

% No duplicate players
:- select(P, S1), select(P, S2), S1 != S2.

% Check if combo is activated
combo_active(ComboID) :- 
    fwd_combo(ComboID, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, 1), matches(P1, T1, K1),
    select(P2, 2), matches(P2, T2, K2),
    select(P3, 3), matches(P3, T3, K3).

% Calculate OVR bonus
ovr_bonus(ComboID, Amt) :- 
    combo_active(ComboID), 
    fwd_combo(ComboID, Amt, ovr, _, _, _, _, _, _).

% Calculate total base OVR
total_base_ovr(Total) :- 
    Total = #sum { OVR, P : select(P, _), ovr(P, OVR) }.

% Calculate total bonus
total_ovr_bonus(Bonus) :- 
    Bonus = #sum { Amt, C : ovr_bonus(C, Amt) }.

% Maximize: base OVR + bonus OVR
#maximize { OVR@1, P : select(P, _), ovr(P, OVR) }.
#maximize { Amt@1, C : ovr_bonus(C, Amt) }.

% Output selected players and active combos
#show select/2.
#show combo_active/1.
#show total_base_ovr/1.
#show total_ovr_bonus/1.
```

### `constraints.lp` - User Constraints

```prolog
% Minimum OVR constraint (parameter: min_ovr)
:- select(P, _), ovr(P, OVR), OVR < min_ovr.

% Exclude players (parameter: excluded)
:- select(P, _), excluded(P).

% Required team (parameter: required_team)
:- required_team(T), select(P, _), player(P, _, Team, _, _), Team != T.

% Required nationality (parameter: required_nationality)
:- required_nationality(N), select(P, _), player(P, _, _, Nat, _), Nat != N.
```

## Step 4: Implement the Solver

The solver already exists in `src/asp/solver.py`.
This section is kept for historical context and as a minimal example of how a Clingo wrapper can look.

```python
import clingo
import time
from typing import Optional

from src.core.data_loader import get_data_loader
from src.core.models import (
    OptimizationConstraints,
    OptimizationTarget,
    LineSolution,
    ActiveCombo,
    Player,
    Position,
    RewardType,
)


class ASPSolver:
    """
    Clingo ASP solver for NHL line optimization.
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def _generate_program(
        self,
        players: list,
        combos: list,
        constraints: OptimizationConstraints,
        is_forward: bool = True,
    ) -> str:
        """Generate complete ASP program."""
        lines = []
        
        # Player facts
        for p in players:
            lines.append(
                f'player({p.id}, {p.overall}, '
                f'"{p.team.lower()}", "{p.nationality.lower()}", '
                f'"{p.event.lower()}").'
            )
        
        # Combo facts
        for c in combos:
            conds = c.get_conditions()
            if is_forward:
                lines.append(
                    f'fwd_combo({c.id}, {c.reward_amount}, '
                    f'{c.reward_type.value.lower()}, '
                    f'"{conds[0].type}", "{conds[0].key.lower()}", '
                    f'"{conds[1].type}", "{conds[1].key.lower()}", '
                    f'"{conds[2].type}", "{conds[2].key.lower()}").'
                )
            else:
                lines.append(
                    f'def_combo({c.id}, {c.reward_amount}, '
                    f'{c.reward_type.value.lower()}, '
                    f'"{conds[0].type}", "{conds[0].key.lower()}", '
                    f'"{conds[1].type}", "{conds[1].key.lower()}").'
                )
        
        # Constraint facts
        if constraints.min_ovr > 0:
            lines.append(f"min_ovr({constraints.min_ovr}).")
        
        for pid in constraints.excluded_player_ids:
            lines.append(f"excluded({pid}).")
        
        if constraints.required_team:
            lines.append(f'required_team("{constraints.required_team.lower()}").')
        
        if constraints.required_nationality:
            lines.append(f'required_nationality("{constraints.required_nationality.lower()}").')
        
        return "\n".join(lines)
    
    def _parse_model(
        self,
        model: clingo.Model,
        players: list,
        combos: list,
    ) -> LineSolution:
        """Parse Clingo model into LineSolution."""
        # Create player lookup
        player_map = {p.id: p for p in players}
        combo_map = {c.id: c for c in combos}
        
        selected_players = []
        active_combos = []
        total_base_ovr = 0
        total_ovr_bonus = 0
        
        for atom in model.symbols(shown=True):
            name = atom.name
            args = atom.arguments
            
            if name == "select":
                player_id = args[0].number
                if player_id in player_map:
                    p = player_map[player_id]
                    selected_players.append(Player(
                        id=p.id,
                        first_name=p.first_name,
                        last_name=p.last_name,
                        event=p.event,
                        overall=p.overall,
                        nationality=p.nationality,
                        league=p.league,
                        team=p.team,
                        position=Position.FORWARD,  # Adjust based on context
                    ))
            
            elif name == "combo_active":
                combo_id = args[0].number
                if combo_id in combo_map:
                    c = combo_map[combo_id]
                    active_combos.append(ActiveCombo(
                        id=c.id,
                        reward_type=c.reward_type,
                        reward_amount=c.reward_amount,
                        description=self._describe_combo(c),
                    ))
            
            elif name == "total_base_ovr":
                total_base_ovr = args[0].number
            
            elif name == "total_ovr_bonus":
                total_ovr_bonus = args[0].number
        
        return LineSolution(
            rank=0,  # Set by caller
            players=selected_players,
            total_base_ovr=total_base_ovr,
            ovr_bonus=total_ovr_bonus,
            effective_ovr=total_base_ovr + total_ovr_bonus,
            total_salary=0,  # Add when salary data available
            total_ap=0,  # Add when AP data available
            active_combos=active_combos,
        )
    
    def _describe_combo(self, combo) -> str:
        """Generate human-readable combo description."""
        conditions = combo.get_conditions()
        parts = [f"{c.type}={c.key}" for c in conditions]
        return " + ".join(parts)
    
    def optimize_forward_line(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        """Find optimal forward line using ASP."""
        # Get data
        forwards = self.loader.get_forwards()
        combos = self.loader.get_forward_combos()
        
        # Pre-filter players
        forwards = self.loader.filter_players(
            forwards,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )
        
        # Generate program
        facts = self._generate_program(forwards, combos, constraints, is_forward=True)
        
        # Load rules from file
        with open("src/asp/rules/forward_line.lp") as f:
            rules = f.read()
        
        program = facts + "\n" + rules
        
        # Run Clingo
        ctl = clingo.Control(["--models", str(num_solutions)])
        ctl.add("base", [], program)
        ctl.ground([("base", [])])
        
        solutions = []
        with ctl.solve(yield_=True) as handle:
            for i, model in enumerate(handle):
                solution = self._parse_model(model, forwards, combos)
                solution.rank = i + 1
                solutions.append(solution)
        
        return solutions
    
    # Implement optimize_defense_pair and optimize_full_team similarly...
```

## Step 5: Replace Placeholder

In `src/api/routes/optimize.py`, replace:

```python
# solver = PlaceholderSolver()  # Remove this
from src.asp.solver import ASPSolver
solver = ASPSolver()  # Use real solver
```

## Testing

Test your solver directly:

```python
from src.asp.solver import ASPSolver
from src.core.models import OptimizationConstraints, OptimizationTarget

solver = ASPSolver()

solutions = solver.optimize_forward_line(
    constraints=OptimizationConstraints(min_ovr=80),
    target=OptimizationTarget.OVR,
    num_solutions=5,
)

for sol in solutions:
    print(f"\nSolution {sol.rank}:")
    print(f"  Players: {[p.full_name for p in sol.players]}")
    print(f"  Base OVR: {sol.total_base_ovr}")
    print(f"  Bonus: {sol.ovr_bonus}")
    print(f"  Effective OVR: {sol.effective_ovr}")
    print(f"  Active Combos: {len(sol.active_combos)}")
```

## API Integration Verification

Once implemented, verify via API:

```bash
# Test optimization endpoint
curl -X POST http://localhost:8000/optimize/forward-line \
  -H "Content-Type: application/json" \
  -d '{
    "constraints": {"min_ovr": 80},
    "optimization_target": "ovr",
    "num_solutions": 3
  }'
```

## Tips

1. **Start simple**: Get basic selection working before adding combos
2. **Test incrementally**: Test facts generation, then rules, then full solver
3. **Use Clingo CLI**: Debug ASP programs directly with `clingo`
4. **Pre-filter aggressively**: Reduce search space by filtering players first
5. **Add timeouts**: Use Clingo's timeout options for complex problems

## Questions?

Contact the API team if you need:
- Changes to data models
- New API endpoints
- Different data formats
