# NHL 26 Line Combos Optimizer

Finding optimal NHL 26 HUT line combinations using Answer Set Programming (ASP) with Clingo.

> **KRR Final Project** - Linköping University, AI Master Students

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

Maximize line combination bonuses (OVR, Salary, AP) while respecting constraints:
- 110M salary cap
- 26 ability points limit
- Position requirements (e.g., at least 1 center per line)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (TBD)                          │
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
| GET | `/players/search?q=name` | Search players by name |

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
