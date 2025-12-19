# NHL 26 Line Combos Optimizer

Finding optimal NHL 26 HUT line combinations using Answer Set Programming (ASP) with Clingo.

> **KRR Final Project** - Jönköping University, AI Master Students

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Documentation Hub](docs/index.md) | Central documentation index |
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [Goal 1 Pipeline](docs/GOAL_1.md) | Two-stage ASP optimization |

### Backend Documentation
| Document | Description |
|----------|-------------|
| [Data Models](docs/backend/DATA_MODELS.md) | Pydantic models and schemas |
| [Development Guide](docs/backend/DEVELOPMENT.md) | Setup, testing, contributing |
| [ASP Integration](docs/backend/ASP_INTEGRATION.md) | ASP/Clingo implementation guide |

### Frontend Documentation
| Guide | For |
|-------|-----|
| [Frontend Integration](docs/FRONTEND_INTEGRATION.md) | Frontend API integration |

---

## 🎯 Project Goal

This project focuses on **finding the best NHL 26 HUT line combinations** under user constraints, using **Answer Set Programming (ASP) with Clingo**.  
Line combinations: `backend/data/fwd_line_combos.csv`, `backend/data/def_line_combos.csv`  
Player cards: `backend/data/fwd_filtered.csv`, `backend/data/def_filtered.csv`, `backend/data/g_filtered.csv`  

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
│                  FRONTEND (React + Ant Design)                  │
│              http://localhost:5173                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API (via Vite proxy)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                      │
│              http://localhost:8000                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Core Module    │  │   ASP Module    │  │  Data (SQLite)  │
│  (data_loader)  │  │   (Clingo)      │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Data storage**: Uses **SQLite** database seeded from CSV files for fast dynamic queries (search/autocomplete, filters, aggregations).

## 🚀 Quick Start

### Prerequisites

**Backend:**
- Python 3.11+

**Frontend:**
- Node.js 18+
- npm 9+
- Yarn 1.22+

### 1. Setup Backend Environment

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run API Server

```bash
cd backend
source venv/bin/activate

# Development mode with auto-reload
uvicorn src.api.main:app --reload --port 8000

# Or using Python module
python -m uvicorn src.api.main:app --reload --port 8000
```

### 3. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
yarn install
```

### 5. Run Frontend Development Server

```bash
cd frontend
yarn dev
# Opens at http://localhost:5173
```

### 6. Run Both (Development)

```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
yarn dev
```

## 📁 Project Structure

```
nhl26-line-combos/
├── backend/                   # Python backend
│   ├── data/                  # CSV data files + SQLite database
│   │   ├── nhl26.db           # SQLite database
│   │   ├── fwd_filtered.csv   # Forward players
│   │   ├── def_filtered.csv   # Defense players
│   │   ├── g_filtered.csv     # Goalies
│   │   ├── skater_id.csv      # Skater names
│   │   ├── g_id.csv           # Goalie names
│   │   ├── fwd_line_combos.csv # Forward line combos
│   │   └── def_line_combos.csv # Defense line combos
│   ├── src/
│   │   ├── core/              # Models and data loading
│   │   │   ├── models/        # Pydantic data models
│   │   │   └── data/          # SQLite loading and filtering
│   │   ├── api/               # FastAPI application
│   │   │   ├── main.py        # App entry point
│   │   │   └── routes/        # API endpoints
│   │   └── asp/               # ASP/Clingo integration
│   │       ├── pipeline.py    # Goal 1 pipeline
│   │       ├── stage_a.py     # Stage A solver
│   │       └── stage_b.py     # Stage B solver
│   ├── scripts/               # Migration scripts
│   ├── tests/                 # Test files
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── App.tsx           # Main app component
│   │   └── main.tsx          # Entry point
│   ├── vite.config.ts        # Vite config with API proxy
│   └── package.json          # Node dependencies
├── docs/                      # Documentation
│   ├── backend/               # Backend-specific docs
│   ├── ARCHITECTURE.md
│   └── FRONTEND_INTEGRATION.md
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

- **ASP Team**: [docs/backend/ASP_INTEGRATION.md](docs/backend/ASP_INTEGRATION.md)
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
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Code Style

```bash
cd backend
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
- **React 18**: Frontend framework
- **Ant Design**: UI component library
- **Vite**: Frontend build tool
- **SQLite**: Persistent storage and fast search/filter queries

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.
