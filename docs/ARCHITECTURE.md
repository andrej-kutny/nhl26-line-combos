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
│  │ Routes: /players, /combos, /optimize, /stats                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CORE LAYER     │    │  ASP LAYER      │    │  DATA LAYER     │
│                 │    │                 │    │                 │
│  • Models       │◄───│  • Solver       │    │  • CSV Files    │
│  • DataLoader   │    │  • Rules        │    │  • Facts        │
│  • Filters      │    │  • Parser       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Planned upgrade**: introduce a **SQLite** data store (seeded from `data/*.csv`) to support:
- fast dynamic search/autocomplete
- richer filtering and aggregations
- stable persistence beyond “CSV-as-database”

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

**Location**: `src/api/`

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

### 3. Core Layer

**Location**: `src/core/`

**Responsibilities**:
- Data models (Pydantic schemas)
- Data loading and caching
- Filtering and preprocessing
- Shared business logic

**Components**:

| Component | File | Purpose |
|-----------|------|---------|
| Models | `models.py` | Pydantic data models |
| DataLoader | `data_loader.py` | CSV loading, caching, filtering |

### 4. ASP Layer (Clingo)

**Location**: `src/asp/`

**Status**: To be implemented by ASP team

**Responsibilities**:
- Generate ASP facts from data
- Define optimization rules
- Run Clingo solver
- Parse solutions

**Components**:

| Component | File | Purpose |
|-----------|------|---------|
| Solver | `solver.py` | Clingo wrapper |
| Rules | `rules/*.lp` | ASP rule files |
| Generator | `facts_generator.py` | Data → ASP facts |

### 5. Data Layer

**Location**: `data/`

**Responsibilities**:
- Store game data (CSV format)
- Player information
- Line combination definitions

**Planned**:
- seed and query a SQLite database (replacing most in-memory CSV scanning)
- keep CSV files as source-of-truth inputs for ingestion

**Files**:

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

### 2. Optimization Flow

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
- fixed picks (by `card_id` or by `player_id` wildcard) *(planned)*

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

### 2. Cached Data Loading

**Why**: CSV files are read once and cached in memory for performance (until SQLite is introduced).

```python
@lru_cache(maxsize=1)
def get_forwards(self) -> list[ForwardPlayer]:
    # Only reads file on first call
    ...
```

### 3. Placeholder Solver Pattern

**Why**: Allows API and frontend development to proceed while ASP is being implemented.

```python
# In optimize.py
solver = PlaceholderSolver()  # Returns mock data
# Later: solver = ASPSolver()  # Real implementation
```

---

## Related Documentation

- [Data Models](DATA_MODELS.md) - Detailed model specifications
- [Development Guide](DEVELOPMENT.md) - Setup and testing

