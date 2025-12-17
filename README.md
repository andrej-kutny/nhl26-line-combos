# NHL 26 Line Combos Optimizer

Finding optimal NHL 26 HUT line combinations using Answer Set Programming (ASP) with Clingo.

> **KRR Final Project** - Jönköping University, AI Master Students

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Documentation Hub](docs/index.md) | Central documentation index |
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [Data Models](docs/DATA_MODELS.md) | Pydantic models and schemas |
| [Development Guide](docs/DEVELOPMENT.md) | Setup, testing, contributing |

### Team Integration Guides
| Guide | For |
|-------|-----|
| [ASP Integration](docs/ASP_INTEGRATION.md) | ASP/Clingo team |
| [Frontend Integration](docs/FRONTEND_INTEGRATION.md) | Frontend team |

---

## 🎯 Project Goal

This project focuses on **finding the best NHL 26 HUT line combinations** under user constraints, using **Answer Set Programming (ASP) with Clingo**.  
Line combinations: `data/fwd_line_combos.csv`, `data/def_line_combos.csv`  
Player cards: `data/fwd_filtered.csv`, `data/def_filtered.csv`, `data/g_filtered.csv`  

### Goal 1 — Rank best line combination candidates (data-driven)

Triggered when **new players** are added or **new line combinations** are added.

- **Outputs** (example target rankings):
  - **Best OVR gain**
  - **Best SAL gain**
  - **Best AP gain**
  - **Best combined OVR+SAL**
    - Forward lines: `ovr_weight = 3`, `sal_weight = 1`
    - Defense/goalie pairs: `ovr_weight = 2`, `sal_weight = 1`
  - **Best combined OVR+SAL+AP**
    - ovr and sal weight as above, `ap_weight = 1`
- **Feasibility filter**:
  - After ASP suggests high-value combo candidates, filter them down to only combos that are **actually fulfillable** by the currently available player cards (i.e., each combo condition has matching candidate cards).

For the detailed Goal 1 pipeline (two-stage ASP + SQLite grounding), see [docs/GOAL_1.md](docs/GOAL_1.md).

### Goal 2 — Suggest lines based on user filters (interactive)

Create line suggestions based on user constraints, including:

- **Already-used players** (exclude them from results)
- **Per-slot constraints** (planned extension):
  - Fixed card (specific card `id`)
  - Fixed player (by `player_id`, wildcard card selection)
  - Min/max overall (and potentially other attributes)
- **Team constraints**:
  - Remaining salary cap
  - Already-used line combinations

The API should:
- Pre-filter players and line combinations before sending them to ASP
- Support “must-include” constraints (e.g., require a specific player/card exactly once)

### Goal 3 — Find best full-team lineups (data-driven)

Triggered when **new players** are added or **new line combinations** are added.

- Use results from Goal 1 as building blocks
- Search for the best full lineup (team line combinations) subject to global constraints (salary cap, AP limit, uniqueness, etc.)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Angular v21)                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                      │
│              http://localhost:8000                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Core Module    │  │   ASP Module    │  │  Data (CSV)     │
│  (data_loader)  │  │   (Clingo)      │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Planned storage**: move from “CSV-as-database” to **SQLite** for fast dynamic queries (search/autocomplete, filters, aggregations), seeded from the CSV files.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run API Server

```bash
# Development mode with auto-reload
uvicorn src.api.main:app --reload --port 8000

# Or using Python module
python -m uvicorn src.api.main:app --reload --port 8000
```

### 3. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
nhl26-line-combos/
├── data/                      # CSV data files
│   ├── hut.sqlite             # Database
│   ├── fwd_filtered.csv       # Forward players
│   ├── def_filtered.csv       # Defense players
│   ├── g_filtered.csv         # Goalies
│   ├── skater_id.csv          # Skater names
│   ├── g_id.csv               # Goalie names
│   ├── fwd_line_combos.csv    # Forward line combos (3 players)
│   └── def_line_combos.csv    # Defense line combos (2 players)
├── src/
│   ├── core/                  # Shared models and data loading
│   │   ├── models.py          # Pydantic data models
│   │   └── data_loader.py     # CSV loading and filtering
│   ├── api/                   # FastAPI application
│   │   ├── main.py            # App entry point
│   │   └── routes/            # API endpoints
│   │       ├── players.py     # Player data endpoints
│   │       ├── combos.py      # Line combo endpoints
│   │       ├── optimize.py    # Optimization endpoints
│   │       └── stats.py       # Statistics endpoints
│   └── asp/                   # ASP/Clingo module (to implement)
│       ├── solver.py          # Clingo solver wrapper
│       └── rules/             # ASP rule files
├── docs/                      # Documentation
├── tests/                     # Test files
├── requirements.txt           # Python dependencies
└── README.md
```

## 🔌 API Endpoints

### Players
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/players/forwards` | List forwards with filters |
| GET | `/players/defense` | List defense with filters |
| GET | `/players/goalies` | List goalies with filters |
| GET | `/players/forwards/search?q=name` | Search forwards by name. Supports filters like `min_ovr`, `max_ovr`, `event`, ... |
| GET | `/players/defense/search?q=name` | Search defense players by name. Supports filters like `min_ovr`, `max_ovr`, `event`, ... |
| GET | `/players/goalies/search?q=name` | Search goalies by name. Supports filters like `min_ovr`, `max_ovr`, `event`, ... |
| GET | `/players/forwards/cards/{player_id}` | All forward cards for a player |
| GET | `/players/defense/cards/{player_id}` | All defense cards for a player |
| GET | `/players/goalies/cards/{player_id}` | All goalie cards for a player |

### Line Combinations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/combos/forward` | List forward combos |
| GET | `/combos/defense` | List defense combos |
| GET | `/combos/forward/{id}/matching-players` | Players matching combo |

### Optimization
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/optimize/forward-line` | Find optimal forward line |
| POST | `/optimize/defense-pair` | Find optimal defense pair |
| POST | `/optimize/full-team` | Find optimal full team |
| POST | `/optimize/validate` | Validate user-selected line |

### Statistics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats/` | Full dataset statistics |
| GET | `/stats/teams` | Available teams |
| GET | `/stats/nationalities` | Available nationalities |

## 👥 Team Integration

See the detailed integration guides in the `docs/` folder:

- **ASP Team**: [docs/ASP_INTEGRATION.md](docs/ASP_INTEGRATION.md)
- **Frontend Team**: [docs/FRONTEND_INTEGRATION.md](docs/FRONTEND_INTEGRATION.md)

## 📊 Data Overview

| Category | Count |
|----------|-------|
| Forward Cards | ~1,768 |
| Defense Cards | ~890 |
| Goalie Cards | ~305 |
| Forward Combos | 54 |
| Defense Combos | 56 |
| Teams | ~172 |
| Nationalities | 23 |

## 🛠️ Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code
black src/

# Check types
mypy src/
```

---

## 📖 Academic Context

This project is part of the **TKRR25 Knowledge Representation and Reasoning** course final project.

### Key Technologies

- **Clingo**: Answer Set Programming solver
- **FastAPI**: REST API framework
- **Pydantic**: Data validation
- **Pandas**: Data processing
- **Angular v21**: Frontend framework
- **SQLite (planned)**: Persistent storage and fast search/filter queries
