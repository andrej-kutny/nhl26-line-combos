"""
NHL 26 Line Combos Optimizer - FastAPI Application

This is the main entry point for the API server.

Running the server:
    # Development (with auto-reload)
    uvicorn src.api.main:app --reload --port 8000
    
    # Or from project root
    python -m uvicorn src.api.main:app --reload --port 8000

API Documentation:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - OpenAPI JSON: http://localhost:8000/openapi.json

Integration:
    - Frontend: Connect to http://localhost:8000
    - ASP Team: The /optimize endpoints call the ASP solver
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import players, combos, optimize, stats
from ..core.data_loader import get_data_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Initializes the data loader on startup to validate data files
    and pre-cache data for faster first requests.
    """
    # Startup: Initialize and validate data
    print("Starting NHL 26 Line Combos Optimizer API...")
    try:
        loader = get_data_loader()
        stats = loader.get_stats()
        print(f"  Loaded {stats['players']['total']} player cards")
        print(f"  Loaded {stats['combos']['total']} line combinations")
        print("  Data validation successful!")
    except FileNotFoundError as e:
        print(f"  WARNING: {e}")
        print("  API will start but some endpoints may fail.")
    
    yield  # Server is running
    
    # Shutdown: Cleanup if needed
    print("Shutting down API...")


# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = FastAPI(
    title="NHL 26 Line Combos Optimizer",
    description="""
## Overview

API for finding optimal NHL 26 HUT line combinations using Answer Set Programming (ASP).

## Features

- **Player Data**: Browse and filter players by position, team, nationality, OVR
- **Line Combinations**: View all available line combos and their rewards
- **Optimization**: Find optimal lines using Clingo ASP solver
- **Constraints**: Apply salary cap, AP limits, player exclusions

## Integration

- **ASP Team**: Optimization endpoints call the Clingo solver
- **Frontend Team**: Use these endpoints to build the UI

## Quick Start

1. Get all forwards: `GET /players/forwards`
2. Get forward combos: `GET /combos/forward`
3. Optimize a line: `POST /optimize/forward-line`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

# Allow frontend to connect from any origin during development
# In production, restrict this to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to ["http://localhost:5173"] for Vite, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ROUTES
# =============================================================================

app.include_router(players.router, prefix="/players", tags=["Players"])
app.include_router(combos.router, prefix="/combos", tags=["Line Combinations"])
app.include_router(optimize.router, prefix="/optimize", tags=["Optimization"])
app.include_router(stats.router, prefix="/stats", tags=["Statistics"])


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint - API health check.
    
    Returns basic API information and status.
    """
    return {
        "name": "NHL 26 Line Combos Optimizer",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "players": "/players",
            "combos": "/combos",
            "optimize": "/optimize",
            "stats": "/stats",
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Used by monitoring systems and load balancers.
    """
    try:
        loader = get_data_loader()
        loader.get_stats()  # Verify data is accessible
        return {"status": "healthy", "data": "loaded"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

