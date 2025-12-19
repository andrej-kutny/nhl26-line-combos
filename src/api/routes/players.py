"""
Player endpoints for NHL 26 Line Combos Optimizer.

These endpoints provide access to player data for forwards, defense, and goalies.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from ...core.data import get_data_loader
from ...core.models import ForwardPlayer, DefensePlayer, Goalie, Position

router = APIRouter()


# =============================================================================
# FORWARD ENDPOINTS
# =============================================================================

@router.get("/forwards", response_model=list[ForwardPlayer])
async def get_forwards(
    min_ovr: int = Query(default=0, ge=0, le=99, description="Minimum overall rating"),
    max_ovr: int = Query(default=99, ge=0, le=99, description="Maximum overall rating"),
    team: Optional[str] = Query(default=None, description="Filter by team (e.g., DET, TOR)"),
    nationality: Optional[str] = Query(default=None, description="Filter by nationality"),
    event: Optional[str] = Query(default=None, description="Filter by event (e.g., ICON, CAP)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
):
    """
    Get all forward players with optional filters.
    
    Use this endpoint to:
    - Browse available forwards
    - Pre-filter players before optimization
    - Build player selection UI
    
    Example:
        GET /players/forwards?min_ovr=85&team=DET&limit=20
    """
    loader = get_data_loader()
    players = loader.get_forwards()
    
    # Apply filters
    filtered = []
    for p in players:
        if p.overall < min_ovr or p.overall > max_ovr:
            continue
        if team and p.team.upper() != team.upper():
            continue
        if nationality and p.nationality.upper() != nationality.upper():
            continue
        if event and p.event.upper() != event.upper():
            continue
        filtered.append(p)
    
    # Sort by OVR descending
    filtered.sort(key=lambda x: x.overall, reverse=True)
    
    # Apply pagination
    return filtered[offset:offset + limit]


@router.get("/forwards/{player_id}", response_model=ForwardPlayer)
async def get_forward_by_id(player_id: int):
    """
    Get a specific forward player by ID.
    
    Note: A player may have multiple cards (different events).
    This returns the first matching card.
    """
    loader = get_data_loader()
    players = loader.get_forwards()
    
    for p in players:
        if p.id == player_id:
            return p
    
    raise HTTPException(status_code=404, detail=f"Forward with ID {player_id} not found")


@router.get("/forwards/{player_id}/cards", response_model=list[ForwardPlayer])
async def get_forward_cards(player_id: int):
    """
    Get all cards for a specific forward player.
    
    A single player can have multiple cards from different events
    (e.g., base card, ICON, TOTW, etc.).
    """
    loader = get_data_loader()
    players = loader.get_forwards()
    
    cards = [p for p in players if p.id == player_id]
    if not cards:
        raise HTTPException(status_code=404, detail=f"Forward with ID {player_id} not found")
    
    return sorted(cards, key=lambda x: x.overall, reverse=True)


# =============================================================================
# DEFENSE ENDPOINTS
# =============================================================================

@router.get("/defense", response_model=list[DefensePlayer])
async def get_defense(
    min_ovr: int = Query(default=0, ge=0, le=99, description="Minimum overall rating"),
    max_ovr: int = Query(default=99, ge=0, le=99, description="Maximum overall rating"),
    team: Optional[str] = Query(default=None, description="Filter by team"),
    nationality: Optional[str] = Query(default=None, description="Filter by nationality"),
    event: Optional[str] = Query(default=None, description="Filter by event"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results to skip"),
):
    """
    Get all defense players with optional filters.
    
    Example:
        GET /players/defense?min_ovr=84&nationality=CANADA
    """
    loader = get_data_loader()
    players = loader.get_defense()
    
    filtered = []
    for p in players:
        if p.overall < min_ovr or p.overall > max_ovr:
            continue
        if team and p.team.upper() != team.upper():
            continue
        if nationality and p.nationality.upper() != nationality.upper():
            continue
        if event and p.event.upper() != event.upper():
            continue
        filtered.append(p)
    
    filtered.sort(key=lambda x: x.overall, reverse=True)
    return filtered[offset:offset + limit]


@router.get("/defense/{player_id}", response_model=DefensePlayer)
async def get_defense_by_id(player_id: int):
    """Get a specific defense player by ID."""
    loader = get_data_loader()
    players = loader.get_defense()
    
    for p in players:
        if p.id == player_id:
            return p
    
    raise HTTPException(status_code=404, detail=f"Defense player with ID {player_id} not found")


@router.get("/defense/{player_id}/cards", response_model=list[DefensePlayer])
async def get_defense_cards(player_id: int):
    """Get all cards for a specific defense player."""
    loader = get_data_loader()
    players = loader.get_defense()
    
    cards = [p for p in players if p.id == player_id]
    if not cards:
        raise HTTPException(status_code=404, detail=f"Defense player with ID {player_id} not found")
    
    return sorted(cards, key=lambda x: x.overall, reverse=True)


# =============================================================================
# GOALIE ENDPOINTS
# =============================================================================

@router.get("/goalies", response_model=list[Goalie])
async def get_goalies(
    min_ovr: int = Query(default=0, ge=0, le=99, description="Minimum overall rating"),
    max_ovr: int = Query(default=99, ge=0, le=99, description="Maximum overall rating"),
    team: Optional[str] = Query(default=None, description="Filter by team"),
    nationality: Optional[str] = Query(default=None, description="Filter by nationality"),
    event: Optional[str] = Query(default=None, description="Filter by event"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results to skip"),
):
    """
    Get all goalies with optional filters.
    
    Example:
        GET /players/goalies?min_ovr=86&team=MTL
    """
    loader = get_data_loader()
    players = loader.get_goalies()
    
    filtered = []
    for p in players:
        if p.overall < min_ovr or p.overall > max_ovr:
            continue
        if team and p.team.upper() != team.upper():
            continue
        if nationality and p.nationality.upper() != nationality.upper():
            continue
        if event and p.event.upper() != event.upper():
            continue
        filtered.append(p)
    
    filtered.sort(key=lambda x: x.overall, reverse=True)
    return filtered[offset:offset + limit]


@router.get("/goalies/{player_id}", response_model=Goalie)
async def get_goalie_by_id(player_id: int):
    """Get a specific goalie by ID."""
    loader = get_data_loader()
    players = loader.get_goalies()
    
    for p in players:
        if p.id == player_id:
            return p
    
    raise HTTPException(status_code=404, detail=f"Goalie with ID {player_id} not found")


# =============================================================================
# SEARCH ENDPOINT
# =============================================================================

@router.get("/search")
async def search_players(
    q: str = Query(..., min_length=2, description="Search query (name)"),
    position: Optional[str] = Query(default=None, description="Filter by position: FWD, DEF, G"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
):
    """
    Search players by name across all positions.
    
    Example:
        GET /players/search?q=gretzky&position=FWD
    """
    loader = get_data_loader()
    results = []
    
    query = q.upper()
    
    # Search forwards
    if position is None or position.upper() == "FWD":
        for p in loader.get_forwards():
            if query in p.first_name.upper() or query in p.last_name.upper():
                results.append({"player": p, "position": "FWD"})
    
    # Search defense
    if position is None or position.upper() == "DEF":
        for p in loader.get_defense():
            if query in p.first_name.upper() or query in p.last_name.upper():
                results.append({"player": p, "position": "DEF"})
    
    # Search goalies
    if position is None or position.upper() == "G":
        for p in loader.get_goalies():
            if query in p.first_name.upper() or query in p.last_name.upper():
                results.append({"player": p, "position": "G"})
    
    # Sort by OVR and deduplicate by ID
    seen_ids = set()
    unique_results = []
    for r in sorted(results, key=lambda x: x["player"].overall, reverse=True):
        if r["player"].id not in seen_ids:
            seen_ids.add(r["player"].id)
            unique_results.append(r)
    
    return unique_results[:limit]

