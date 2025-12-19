# System Architecture

This document describes the architecture of the NHL 26 Line Combos Optimizer.

## Overview

The system uses a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                              │
│                     Frontend Application (Angular v21)                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ REST API (JSON)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                      │
│                         FastAPI Backend                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Routes: /players, /combos, /optimize, /stats, /best              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CORE LAYER     │    │  ASP LAYER      │    │  DATA LAYER     │
│                 │    │                 │    │                 │
│  • models/      │◄───│  • Pipeline     │    │  • SQLite DB    │
│  • data/        │    │  • Stage A/B    │    │  • CSV Files    │
│  • Goal1Store   │    │  • Rules (*.lp) │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Data storage**: Uses **SQLite** database (`backend/data/nhl26.db`) seeded from CSV files via `backend/scripts/csv_to_sqlite.py`:
- Fast indexed queries for filtering by team, nationality, event, OVR
- Goal 1 pipeline result persistence (runs, Stage A, Stage B concrete lines)
- CSV files remain as source-of-truth for data updates

## Layer Descriptions

### 1. Presentation Layer (Frontend)

**Technology**: Angular v21

**Responsibilities**:
- User interface for line optimization
- Display players and combinations
- Constraint configuration forms
- Solution visualization

**Communication**: REST API calls to backend

### 2. API Layer (FastAPI)

**Location**: `backend/src/api/`

**Responsibilities**:
- HTTP request handling
- Input validation (Pydantic)
- Response serialization
- CORS handling
- API documentation (OpenAPI)

**Components**:

| Component | File | Purpose |
|-----------|------|---------|
| Main App | `main.py` | FastAPI application setup |
| Players Routes | `routes/players.py` | Player CRUD endpoints |
| Combos Routes | `routes/combos.py` | Line combo endpoints |
| Optimize Routes | `routes/optimize.py` | Optimization endpoints |
| Stats Routes | `routes/stats.py` | Statistics endpoints |
| Best Routes | `routes/best.py` | Goal 1 results endpoints |

### 3. Core Layer

**Location**: `backend/src/core/`

**Responsibilities**:
- Data models (Pydantic schemas)
- Data loading and caching from SQLite
- Filtering and preprocessing
- Shared business logic
- Goal 1 pipeline result storage

**Components**:

| Component | Location | Purpose |
|-----------|----------|---------|
| Models | `models/` | Pydantic data models (split by domain) |
| DataLoader | `data/loader.py` | SQLite loading, caching, filtering |
| Goal1Store | `data/goal1_store.py` | Goal 1 pipeline result CRUD |

**Model Files**:

| File | Contents |
|------|----------|
| `models/enums.py` | Position, RewardType, OptimizationMode, etc. |
| `models/players.py` | ForwardPlayer, DefensePlayer, Goalie, Player |
| `models/combos.py` | ForwardLineCombo, DefenseLineCombo |
| `models/api.py` | OptimizationRequest, LineSolution, etc. |
| `models/goal1.py` | Goal1Run, Goal1StageAResult, Goal1ConcreteLine |

### 4. ASP Layer (Clingo)

**Location**: `backend/src/asp/`

**Status**: Pipeline scaffolding complete, ASP solvers in progress

**Responsibilities**:
- Goal 1 pipeline orchestration (Stage A → Stage B → Storage)
- Generate ASP facts from combo/player data
- Define optimization rules
- Run Clingo solver
- Parse solutions

**Components**:

| Component | File | Purpose |
|-----------|------|---------|
| Interfaces | `interfaces.py` | Solver contracts (`StageASolver`, `StageBSolver`) |
| Pipeline | `pipeline.py` | Goal 1 orchestrator (`run_goal1_pipeline()`) |
| Stage A | `stage_a.py` | Combo facts generator + mock solver |
| Stage B | `stage_b.py` | Player candidate query + mock solver |

**ASP Rules** (in `g1a_abstraction/`):

| File | Purpose |
|------|---------|
| `fwd_rules.lp` | Forward line optimization rules |
| `def_rules.lp` | Defense pair optimization rules |
| `rules.lp` | Shared rules |
| `target_optimise.lp` | Optimization targets |
| `target_threshold_lookup.lp` | Threshold lookups |

### 5. Data Layer

**Location**: `backend/data/`

**Responsibilities**:
- Store game data in SQLite database
- Player cards with full stats
- Line combination definitions
- Goal 1 pipeline results

**Database**: `nhl26.db` - Created via `python backend/scripts/csv_to_sqlite.py`

**Tables**:
- `forwards`, `defense`, `goalies` - Player cards
- `skater_names`, `goalie_names` - Name lookups
- `forward_combos`, `defense_combos` - Line combinations
- `goal1_runs`, `goal1_stage_a_results`, `goal1_concrete_lines` - Goal 1 results

**Source Files**:

| File | Content |
|------|---------|
| `fwd_filtered.csv` | Forward player cards |
| `def_filtered.csv` | Defense player cards |
| `g_filtered.csv` | Goalie cards |
| `skater_id.csv` | Skater name mappings |
| `g_id.csv` | Goalie name mappings |
| `fwd_line_combos.csv` | Forward line combinations |
| `def_line_combos.csv` | Defense line combinations |

---

## Data Flow

### 1. Player Query Flow

```
Client                API                Core              Data
  │                    │                   │                 │
  │ GET /players/fwd   │                   │                 │
  │───────────────────>│                   │                 │
  │                    │ get_forwards()    │                 │
  │                    │──────────────────>│                 │
  │                    │                   │ read CSV        │
  │                    │                   │────────────────>│
  │                    │                   │<────────────────│
  │                    │                   │ (cached)        │
  │                    │<──────────────────│                 │
  │                    │ apply filters     │                 │
  │<───────────────────│                   │                 │
  │    JSON response   │                   │                 │
```

### 2. Optimization Flow (Interactive - Goal 2)

```
Client              API              Core              ASP              Clingo
  │                  │                 │                 │                  │
  │ POST /optimize   │                 │                 │                  │
  │─────────────────>│                 │                 │                  │
  │                  │ get_players()   │                 │                  │
  │                  │────────────────>│                 │                  │
  │                  │<────────────────│                 │                  │
  │                  │ get_combos()    │                 │                  │
  │                  │────────────────>│                 │                  │
  │                  │<────────────────│                 │                  │
  │                  │ optimize()      │                 │                  │
  │                  │──────────────────────────────────>│                  │
  │                  │                 │                 │ generate facts   │
  │                  │                 │                 │ load rules       │
  │                  │                 │                 │ solve()          │
  │                  │                 │                 │─────────────────>│
  │                  │                 │                 │<─────────────────│
  │                  │                 │                 │ parse models     │
  │                  │<──────────────────────────────────│                  │
  │<─────────────────│                 │                 │                  │
  │  JSON solutions  │                 │                 │                  │
```

### 3. Goal 1 Pipeline Flow (Batch)

```
Pipeline          Stage A Gen      Stage A Solver    Stage B Gen      Stage B Solver    Storage
   │                   │                 │                │                 │              │
   │ generate()        │                 │                │                 │              │
   │──────────────────>│                 │                │                 │              │
   │  combo_facts      │                 │                │                 │              │
   │<──────────────────│                 │                │                 │              │
   │                   │                 │                │                 │              │
   │ solve(input)      │                 │                │                 │              │
   │────────────────────────────────────>│                │                 │              │
   │  StageAOutput     │                 │                │                 │              │
   │<────────────────────────────────────│                │                 │              │
   │                   │                 │                │                 │              │
   │ For each Stage A solution:          │                │                 │              │
   │ generate(solution)│                 │                │                 │              │
   │─────────────────────────────────────────────────────>│                 │              │
   │  players + combo_facts              │                │                 │              │
   │<─────────────────────────────────────────────────────│                 │              │
   │                   │                 │                │                 │              │
   │ solve(input)      │                 │                │                 │              │
   │───────────────────────────────────────────────────────────────────────>│              │
   │  StageBOutput (concrete lines)      │                │                 │              │
   │<───────────────────────────────────────────────────────────────────────│              │
   │                   │                 │                │                 │              │
   │ store_results()   │                 │                │                 │              │
   │──────────────────────────────────────────────────────────────────────────────────────>│
   │                   │                 │                │                 │              │
```

---

## Product Goals → System Responsibilities

### Goal 1 — Rank best line combination candidates (batch)

Triggered when **players** or **line combinations** change:
- Generate candidate combos (via ASP)
- Rank by target metrics (OVR / SAL / AP and weighted combinations)
- Filter to combos that are **fulfillable** by the current player card pool

### Goal 2 — Suggest lines from user filters (interactive)

From Angular UI, the API receives:
- used players (exclude)
- remaining salary cap / AP budget
- fixed picks (by card `id` or by `player_id` wildcard) *(planned)*

The API pre-filters candidates and calls ASP to produce ranked solutions.

### Goal 3 — Best full-team lineups (batch)

Use the best combos and solve a larger “team lineup” optimization under global constraints.

## Key Design Decisions

### 1. Pydantic for Data Models

**Why**: Type safety, automatic validation, JSON serialization, OpenAPI schema generation.

```python
class Player(BaseModel):
    id: int
    overall: int = Field(ge=1, le=99)  # Automatic validation
    team: str
```

### 2. SQLite Data Storage

**Why**: SQLite provides efficient indexed queries, better filtering, and stable persistence.

```python
# Data loaded from SQLite with SQL WHERE clauses for efficient filtering
def get_forwards(self, min_ovr=0, team=None, ...) -> list[ForwardPlayer]:
    query = "SELECT * FROM forwards WHERE overall >= ? ..."
    ...

# Name lookups cached in memory (small tables)
@lru_cache(maxsize=1)
def _load_skater_names(self) -> dict[int, tuple[str, str]]:
    ...
```

### 3. Placeholder Solver Pattern

**Why**: Allows API and frontend development to proceed while ASP is being implemented.

```python
# In optimize.py
solver = PlaceholderSolver()  # Returns mock data
# Later: solver = ASPSolver()  # Real implementation
```

### 4. Goal 1 Two-Stage Pipeline

**Why**: Separates abstract optimization (combo selection) from concrete enumeration (player assignment).

```python
from src.asp.pipeline import run_goal1_pipeline

# Stage A: Find best combo combinations (abstract, no players)
# Stage B: Enumerate concrete lines that satisfy those combos
result = run_goal1_pipeline(
    position_type="forward",
    optimization_mode="ovr",
    top_k=200,              # Stage A solutions
    player_limit=100,       # Candidates per solution
    store_results=True,     # Persist to SQLite
)
```

**Benefits**:
- Stage A runs fast (combos only, ~50-100 items)
- Stage B is bounded by pre-filtered player candidates
- Results are persisted and queryable via `/best/{pos}/{mode}`

---

## Related Documentation

- [Goal 1 Specification](GOAL_1.md) - Two-stage pipeline design
- [ASP Integration](backend/ASP_INTEGRATION.md) - ASP implementation guide
- [Data Models](backend/DATA_MODELS.md) - Detailed model specifications
- [Development Guide](backend/DEVELOPMENT.md) - Setup and testing

