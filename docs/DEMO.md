# Demo guide (backend + API)

This guide provides a minimal, copy/paste friendly checklist to run an
interactive demo of the project using the FastAPI backend.

## 1) Start the API

From repo root:

```bash
cd "/Users/sandstrom/NHL 26 Line Combos Optimizer/nhl26-line-combos"
venv/bin/python -m uvicorn src.api.main:app --reload --port 8000
```

Open Swagger UI:
- http://127.0.0.1:8000/docs

## 2) Health check

```bash
curl -sS "http://127.0.0.1:8000/health"
```

## 3) Explore data

Players:

```bash
curl -sS "http://127.0.0.1:8000/players/forwards?limit=5" | python -m json.tool
curl -sS "http://127.0.0.1:8000/players/defense?limit=5" | python -m json.tool
```

Combos:

```bash
curl -sS "http://127.0.0.1:8000/combos/forward?limit=5" | python -m json.tool
curl -sS "http://127.0.0.1:8000/combos/defense?limit=5" | python -m json.tool
```

## 4) Optimize endpoints (interactive)

Forward line (3 players):

```bash
curl -sS -X POST "http://127.0.0.1:8000/optimize/forward-line" \
  -H "Content-Type: application/json" \
  -d '{"constraints":{"min_ovr":80},"optimization_target":"ovr","num_solutions":3}' \
  | python -m json.tool | head -n 120
```

Defense pair (2 players):

```bash
curl -sS -X POST "http://127.0.0.1:8000/optimize/defense-pair" \
  -H "Content-Type: application/json" \
  -d '{"constraints":{"min_ovr":80},"optimization_target":"ovr","num_solutions":3}' \
  | python -m json.tool | head -n 120
```

Validate a user-selected line/pair (shows activated combos + totals):

```bash
curl -sS -X POST "http://127.0.0.1:8000/optimize/validate?position_type=forward" \
  -H "Content-Type: application/json" \
  -d '[1,2,3]' | python -m json.tool
```

## 5) Solver status

```bash
curl -sS "http://127.0.0.1:8000/optimize/status" | python -m json.tool
```

