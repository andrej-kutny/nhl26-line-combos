# Development Guide

This guide covers setting up the development environment and running tests..

## Prerequisites

- Python 3.11+
- pip
- Git

## Setup

### 1. Clone Repository

```bash
git clone git@github.com:andrej-kutny/nhl26-line-combos.git
cd nhl26-line-combos/backend
```

### 2. Create Virtual Environment

```bash
# Create venv (from backend/ directory)
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# For development extras (optional)
pip install black mypy pytest-cov
```

### 4. Initialize Database

```bash
# Create SQLite database from CSV files
python scripts/csv_to_sqlite.py
```

### 5. Verify Installation

```bash
# Test data loading
python -c "from src.core import get_data_loader; print(get_data_loader().get_stats())"

# Should output dataset statistics
```

---

## Running the Server

```bash
# With auto-reload
uvicorn src.api.main:app --reload --port 8000

# Or using Python module
python -m uvicorn src.api.main:app --reload --port 8000
```


### Access Points

| Resource | URL |
|----------|-----|
| API Root | http://localhost:8000 |
| Health Check | http://localhost:8000/health |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |

---

## Project Structure

```
nhl26-line-combos/
├── backend/                   # Python backend (you are here)
│   ├── data/                  # Data files
│   │   ├── nhl26.db          # SQLite database (generated)
│   │   ├── fwd_filtered.csv  # Source CSV files
│   │   ├── def_filtered.csv
│   │   ├── g_filtered.csv
│   │   ├── skater_id.csv
│   │   ├── g_id.csv
│   │   ├── fwd_line_combos.csv
│   │   └── def_line_combos.csv
│   ├── scripts/
│   │   └── csv_to_sqlite.py  # Database migration script
│   ├── src/
│   │   ├── __init__.py
│   │   ├── core/             # Shared code
│   │   │   ├── __init__.py   # Re-exports all models and data classes
│   │   │   ├── models/       # Pydantic models (split by domain)
│   │   │   │   ├── enums.py
│   │   │   │   ├── players.py
│   │   │   │   ├── combos.py
│   │   │   │   ├── api.py
│   │   │   │   └── goal1.py
│   │   │   └── data/         # Data access layer
│   │   │       ├── loader.py
│   │   │       └── goal1_store.py
│   │   ├── api/              # FastAPI app
│   │   │   ├── main.py
│   │   │   └── routes/
│   │   └── asp/              # ASP/Clingo integration
│   │       ├── pipeline.py
│   │       ├── stage_a.py
│   │       └── stage_b.py
│   ├── tests/
│   │   ├── test_csv_to_sqlite.py
│   │   ├── test_data_loader.py
│   │   └── test_goal1_storage.py
│   └── requirements.txt
├── docs/                      # Documentation
│   ├── backend/              # Backend-specific docs
│   │   ├── DEVELOPMENT.md    # This file
│   │   ├── DATA_MODELS.md
│   │   └── ASP_INTEGRATION.md
│   ├── ARCHITECTURE.md
│   ├── FRONTEND_INTEGRATION.md
│   └── GOAL_1.md
└── README.md
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_data_loader.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get forwards
curl "http://localhost:8000/players/forwards?min_ovr=85&limit=5"

# Optimize
curl -X POST http://localhost:8000/optimize/forward-line \
  -H "Content-Type: application/json" \
  -d '{"constraints": {"min_ovr": 80}, "num_solutions": 3}'
```

---

## Code Style

### Formatting

Use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format all files
black src/ tests/

# Check without modifying
black src/ tests/ --check
```

### Type Checking

Use [mypy](https://mypy.readthedocs.io/) for type checking:

```bash
mypy src/
```

### Import Sorting

Use [isort](https://pycqa.github.io/isort/) for import sorting:

```bash
isort src/ tests/
```

---

## Adding New Features

### 1. Adding a New Endpoint

1. Create or modify route file in `src/api/routes/`
2. Add Pydantic models to the appropriate file in `src/core/models/` if needed
3. Register route in `src/api/main.py` if new file
4. Add tests in `tests/`
5. Update API documentation

**Example**: Adding a new player endpoint

```python
# src/api/routes/players.py

@router.get("/players/top")
async def get_top_players(
    position: str = Query(..., description="FWD, DEF, or G"),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Get top players by OVR for a position."""
    loader = get_data_loader()
    
    if position == "FWD":
        players = loader.get_forwards()
    elif position == "DEF":
        players = loader.get_defense()
    else:
        players = loader.get_goalies()
    
    players.sort(key=lambda x: x.overall, reverse=True)
    return players[:limit]
```

### 2. Adding a New Model

1. Define model in the appropriate file in `src/core/models/`:
   - `enums.py` for enumerations
   - `players.py` for player models
   - `combos.py` for combo models
   - `api.py` for API request/response models
   - `goal1.py` for Goal 1 pipeline models
2. Export from `src/core/models/__init__.py`
3. Use in routes or data loader
4. Document in `docs/DATA_MODELS.md`

### 3. Modifying Data Loading

1. Update `src/core/data/loader.py` (for players/combos)
   or `src/core/data/goal1_store.py` (for Goal 1 results)
2. Add tests in `tests/test_data_loader.py` or `tests/test_goal1_storage.py`
3. Clear cache if changing structure: restart server

---

## Environment Variables

Create a `.env` file (optional):

```bash
# Server settings
HOST=0.0.0.0
PORT=8000

# Data directory (default: data/)
DATA_DIR=data/

# Debug mode
DEBUG=true
```

Load in `src/api/main.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Debugging

### Enable Debug Logging

```python
# In src/api/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Interactive Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use IPython
from IPython import embed; embed()
```

### Test Data Loading

```python
# Interactive Python session
from src.core import get_data_loader, get_results_store

# Load players
loader = get_data_loader()
forwards = loader.get_forwards()
print(f"Loaded {len(forwards)} forwards")

# Test filtering
filtered = loader.filter_players(forwards, min_ovr=85, team="DET")
print(f"Filtered to {len(filtered)} players")

# Test Goal 1 storage
store = get_results_store()
runs = store.list_runs()
print(f"Found {len(runs)} Goal 1 runs")
```

---

## Common Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn src.api.main:app --port 8001
```

### Import Errors

```bash
# Make sure you're in backend directory
cd nhl26-line-combos/backend

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Data File Not Found

```bash
# Check data directory exists (from backend/)
ls data/

# Verify all required files
ls data/*.csv
```

---

## Git Workflow

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates

### Commit Messages

```
feat: Add player search endpoint
fix: Correct OVR calculation in optimizer
docs: Update API reference
test: Add data loader tests
refactor: Simplify filter logic
```

### Pull Request Checklist

- [ ] Code follows project style
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No linting errors

---

## Related Documentation

- [Architecture](../ARCHITECTURE.md) - System design

