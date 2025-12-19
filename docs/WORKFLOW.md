# Workflow (PRs, demo readiness)

## Branching

- Always branch from `dev`.
- Keep PRs small and scoped to a single task.

## Quick checks

Run tests:

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
venv/bin/python -m pytest -q
```

Run API smoke:

```bash
venv/bin/python -m uvicorn src.api.main:app --reload --port 8000
curl -sS "http://127.0.0.1:8000/health"
```

