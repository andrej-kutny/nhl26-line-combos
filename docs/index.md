# Documentation Hub

Welcome to the NHL 26 Line Combos Optimizer documentation.

## 📚 Documentation Index

### Getting Started
- [Quick Start Guide](../README.md#-quick-start) - Setup and run the project
- [Project Overview](../README.md#-project-goal) - What this project does

### Architecture & Design
- [System Architecture](ARCHITECTURE.md) - How the system is structured
- [Goal 1 Pipeline](GOAL_1.md) - Two-stage ASP optimization pipeline

### API Documentation
- [Swagger UI](http://localhost:8000/docs) - Interactive API docs (when server running)
- [ReDoc](http://localhost:8000/redoc) - Alternative API docs

### Backend Documentation
- [Data Models](backend/DATA_MODELS.md) - Player, combo, and API models
- [ASP Integration](backend/ASP_INTEGRATION.md) - Clingo solver implementation
- [Development Guide](backend/DEVELOPMENT.md) - Setup, testing, contributing

### Frontend Documentation
- [Frontend Integration](FRONTEND_INTEGRATION.md) - Connecting UI to API

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

**Data Layer**: Uses **SQLite** database (seeded from CSV files) for fast search/autocomplete and richer filtering.

## 📁 Project Structure

```
nhl26-line-combos/
├── backend/                 # Python backend
│   ├── data/               # CSV + SQLite database
│   ├── src/
│   │   ├── core/           # Models and data loading
│   │   ├── api/            # FastAPI app
│   │   └── asp/            # Clingo integration
│   ├── scripts/            # Migration scripts
│   └── tests/              # Unit tests
├── docs/                    # 📍 You are here
│   ├── index.md            # This file
│   ├── ARCHITECTURE.md     # System design
│   ├── GOAL_1.md           # Goal 1 pipeline
│   ├── FRONTEND_INTEGRATION.md  # Frontend guide
│   └── backend/            # Backend-specific docs
│       ├── DATA_MODELS.md
│       ├── ASP_INTEGRATION.md
│       └── DEVELOPMENT.md
└── README.md               # Project overview
```

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| API Server | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| GitHub | https://github.com/andrej-kutny/nhl26-line-combos |

