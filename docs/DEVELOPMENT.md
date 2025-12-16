# Development Guide

This guide covers setting up the development environment, running the API, and executing tests.

## Prerequisites

- Python 3.11+ (recommended; Clingo wheels can be fragile on very new Python versions)
- pip
- Git

## Setup

### 1. Clone Repository

```bash
git clone git@github.com:andrej-kutny/nhl26-line-combos.git
cd nhl26-line-combos
```

### 2. Create Virtual Environment

```bash
# Create venv
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

### 4. Verify Installation

```bash
# Test data loading
python -c "from src.core.data_loader import get_data_loader; print(get_data_loader().get_stats())"

# Should output dataset statistics
```

---

## Running the Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

### macOS workflow (Terminal tabs)

When Clingo is solving, a single-worker dev server can appear “frozen” because the request is CPU-bound.
For interactive debugging, use multiple workers and run a dedicated health-check in a separate Terminal tab.

**Tab T1 (start API on port 8000)**

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
source venv/bin/activate
lsof -nP -iTCP:8000 -sTCP:LISTEN
kill -9 <PID>
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --workers 2 --log-level warning
```

Replace `<PID>` with the numeric PID printed by `lsof`.

**Tab T2 (health-check)**

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
source venv/bin/activate
curl -m 5 -sS http://127.0.0.1:8000/docs -o /dev/null
echo $?
```

An exit code `0` means the server responded within the timeout.

**Tab T3 (forward line examples)**

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
source venv/bin/activate
curl -m 30 -sS http://127.0.0.1:8000/optimize/forward-line -H "Content-Type: application/json" -d '{"constraints":{"min_ovr":90,"require_center":false,"max_salary":110},"optimization_target":"ovr","num_solutions":1}' | python3 -m json.tool
curl -m 30 -sS http://127.0.0.1:8000/optimize/forward-line -H "Content-Type: application/json" -d '{"constraints":{"min_ovr":80,"require_center":false,"max_salary":110},"optimization_target":"salary","num_solutions":1}' | python3 -m json.tool
```

The `salary` target is intended to surface strong SAL bonuses (e.g., `FANT+FANT+FANT -> +20 SAL`) while staying under the effective cap.

### Offline full-team runs (recommended for long searches)

Full-team optimization can be large enough that interactive API calls time out on the client side (or tie up the dev server for too long).
For long experiments (e.g., 30–120 minutes), use the offline runner which:
- runs locally (no FastAPI request/response timeout),
- uses explicit candidate-pool caps (`--max-fwd/--max-def/--max-g`),
- enforces an explicit Clingo time limit (`--time-limit-seconds`),
- writes results to a JSON file for later inspection.

**Tab T4 (offline full-team runner, e.g. 2 hours)**

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
source venv/bin/activate
python scripts/run_full_team_offline.py --min-ovr 80 --max-salary 110 --target ovr --time-limit-seconds 7200 --threads 4 --max-fwd 24 --max-def 14 --max-g 4 --json-out out/full_team_solution.json
```

### Stepwise scaling (recommended)

If a full-team run becomes impractically slow, scale the candidate caps gradually and observe where runtime starts to explode.
The goal is to keep the search space just large enough to find good solutions without turning the solve into an hours-long run.

Example progression (same constraints/target, increasing caps):

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
source venv/bin/activate
python scripts/run_full_team_offline.py --min-ovr 80 --max-salary 110 --target ovr --time-limit-seconds 1800 --threads 4 --max-fwd 24 --max-def 14 --max-g 4 --json-out out/full_team_24_14_4.json
python scripts/run_full_team_offline.py --min-ovr 80 --max-salary 110 --target ovr --time-limit-seconds 1800 --threads 4 --max-fwd 32 --max-def 18 --max-g 6 --json-out out/full_team_32_18_6.json
python scripts/run_full_team_offline.py --min-ovr 80 --max-salary 110 --target ovr --time-limit-seconds 1800 --threads 4 --max-fwd 40 --max-def 24 --max-g 8 --json-out out/full_team_40_24_8.json
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
├── data/                      # CSV data files (do not modify)
│   ├── fwd_filtered.csv
│   ├── def_filtered.csv
│   ├── g_filtered.csv
│   ├── skater_id.csv
│   ├── g_id.csv
│   ├── fwd_line_combos.csv
│   └── def_line_combos.csv
├── docs/                      # Documentation
│   ├── index.md              # Doc hub
│   ├── ARCHITECTURE.md
│   ├── DATA_MODELS.md
│   ├── ASP_INTEGRATION.md
│   ├── FRONTEND_INTEGRATION.md
│   └── DEVELOPMENT.md        # This file
├── src/
│   ├── __init__.py
│   ├── core/                 # Shared code
│   │   ├── __init__.py
│   │   ├── models.py         # Pydantic models
│   │   └── data_loader.py    # Data loading
│   ├── api/                  # FastAPI app
│   │   ├── __init__.py
│   │   ├── main.py           # App entry point
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── players.py
│   │       ├── combos.py
│   │       ├── optimize.py
│   │       └── stats.py
│   └── asp/                  # ASP module (to implement)
│       ├── __init__.py
│       ├── solver.py         # Clingo wrapper
│       └── rules/            # ASP rule files
├── tests/
│   ├── __init__.py
│   └── test_data_loader.py
├── .gitignore
├── requirements.txt
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
2. Add Pydantic models to `src/core/models.py` if needed
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

1. Define model in `src/core/models.py`
2. Use in routes or data loader
3. Document in `docs/DATA_MODELS.md`

### 3. Modifying Data Loading

1. Update `src/core/data_loader.py`
2. Add tests in `tests/test_data_loader.py`
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
from src.core.data_loader import get_data_loader

loader = get_data_loader()
forwards = loader.get_forwards()
print(f"Loaded {len(forwards)} forwards")

# Test filtering
filtered = loader.filter_players(forwards, min_ovr=85, team="DET")
print(f"Filtered to {len(filtered)} players")
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
# Make sure you're in project root
cd nhl26-line-combos

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Data File Not Found

```bash
# Check data directory exists
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

- [Architecture](ARCHITECTURE.md) - System design
- [ASP Integration](ASP_INTEGRATION.md) - ASP team guide
- [Frontend Integration](FRONTEND_INTEGRATION.md) - Frontend guide
