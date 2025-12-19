# Documentation Hub

Welcome to the NHL 26 Line Combos Optimizer documentation.

## 📚 Documentation Index

### Getting Started
- [Quick Start Guide](../README.md#-quick-start) - Setup and run the project
- [Project Overview](../README.md#-project-goal) - What this project does

### Demo
- [Demo Guide](DEMO.md) - Run API + demo endpoints

### Architecture & Design
- [System Architecture](ARCHITECTURE.md) - How the system is structured
- [Data Models](DATA_MODELS.md) - Player, combo, and API models
- [Goal 1](GOAL_1.md) - Goal 1 pipeline (abstract combo optimization → player grounding)

### API Documentation
- [Swagger UI](http://localhost:8000/docs) - Interactive API docs (when server running)
- [ReDoc](http://localhost:8000/redoc) - Alternative API docs

### Team Integration Guides
- [ASP Team Guide](ASP_INTEGRATION.md) - Clingo solver implementation
- [Frontend Team Guide](FRONTEND_INTEGRATION.md) - Connecting UI to API

### Development
- [Development Guide](DEVELOPMENT.md) - Setup, testing, contributing
- [Workflow](WORKFLOW.md) - Branching and demo checks

---

## 🗺️ System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                           (Angular v21)                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP/REST
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  /players   │  │  /combos    │  │  /optimize  │  │   /stats    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core Module   │    │   ASP Module    │    │   Data Layer    │
│   data_loader   │◄───│   Clingo        │    │   CSV Files     │
│   models        │    │   solver        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Planned**: migrate the Data Layer to **SQLite** (seeded from `data/*.csv`) to support fast search/autocomplete and richer filtering.

## 📁 Project Structure

```
nhl26-line-combos/
├── data/                    # Game data (CSV)
├── docs/                    # 📍 You are here
│   ├── index.md            # This file
│   ├── ARCHITECTURE.md     # System design
│   ├── DATA_MODELS.md      # Model definitions
│   ├── ASP_INTEGRATION.md  # ASP team guide
│   ├── FRONTEND_INTEGRATION.md  # Frontend guide
│   └── DEVELOPMENT.md      # Dev guide
├── src/
│   ├── core/               # Shared code
│   ├── api/                # FastAPI app
│   └── asp/                # Clingo integration
├── tests/                  # Unit tests
└── README.md               # Project overview
```

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| API Server | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| GitHub | https://github.com/andrej-kutny/nhl26-line-combos |
