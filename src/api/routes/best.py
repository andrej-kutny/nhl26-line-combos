"""
Best lines endpoint for NHL 26 Line Combos Optimizer.

Exposes Goal 1 pipeline results to the frontend.

Endpoints:
    GET /best/{pos}/{mode} - Get best concrete lines for position/mode
    GET /best/runs - List available Goal 1 runs
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.data import get_data_loader, get_results_store
from ...core.models import (
    Goal1Run,
    Goal1ConcreteLine,
    OptimizationMode,
    PositionType,
)

router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class PlayerInfo(BaseModel):
    """Basic player info for line display."""
    id: int = Field(..., description="Player card ID")
    player_id: int = Field(..., description="Real player ID")
    first_name: str
    last_name: str
    overall: int
    team: str
    nationality: str
    event: str
    position: str
    salary: float


class ConcreteLineResponse(BaseModel):
    """A concrete line with player details."""
    id: int = Field(..., description="Line ID in database")
    players: list[PlayerInfo] = Field(..., description="Players in this line")
    activated_combo_ids: list[int] = Field(..., description="Activated combo IDs")
    total_ovr: int = Field(..., description="Total OVR including bonuses")
    total_salary: float = Field(..., description="Total salary")
    total_ap: int = Field(..., description="Total AP cost")
    ranking_score: float = Field(..., description="Ranking score")


class BestLinesResponse(BaseModel):
    """Response for /best/{pos}/{mode} endpoint."""
    success: bool = True
    run: Optional[Goal1Run] = Field(None, description="The Goal 1 run these results are from")
    position_type: str = Field(..., description="forward or defense")
    optimization_mode: str = Field(..., description="Optimization mode used")
    total_lines: int = Field(..., description="Total lines available")
    lines: list[ConcreteLineResponse] = Field(..., description="Concrete lines")


class RunListResponse(BaseModel):
    """Response for /best/runs endpoint."""
    runs: list[Goal1Run]
    total: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_player_info(player_ids: list[int], position_type: str) -> list[PlayerInfo]:
    """Fetch player details for a list of player IDs."""
    loader = get_data_loader()
    
    # Get all players of the appropriate type
    if position_type == "forward":
        all_players = loader.get_forwards()
    else:
        all_players = loader.get_defense()
    
    # Build lookup by ID
    player_lookup = {p.id: p for p in all_players}
    
    # Get player info for each ID
    result = []
    for pid in player_ids:
        player = player_lookup.get(pid)
        if player:
            result.append(PlayerInfo(
                id=player.id,
                player_id=player.player_id,
                first_name=player.first_name,
                last_name=player.last_name,
                overall=player.overall,
                team=player.team,
                nationality=player.nationality,
                event=player.event,
                position=player.position,
                salary=player.salary,
            ))
        else:
            # Player not found - include placeholder
            result.append(PlayerInfo(
                id=pid,
                player_id=0,
                first_name="Unknown",
                last_name="Player",
                overall=0,
                team="???",
                nationality="???",
                event="???",
                position="???",
                salary=0.0,
            ))
    
    return result


def _enrich_lines(
    lines: list[Goal1ConcreteLine],
    position_type: str,
) -> list[ConcreteLineResponse]:
    """Enrich concrete lines with player details."""
    result = []
    for line in lines:
        players = _get_player_info(line.player_ids, position_type)
        result.append(ConcreteLineResponse(
            id=line.id,
            players=players,
            activated_combo_ids=line.activated_combo_ids,
            total_ovr=line.total_ovr,
            total_salary=line.total_salary,
            total_ap=line.total_ap,
            ranking_score=line.ranking_score,
        ))
    return result


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    position_type: Optional[str] = Query(
        None,
        description="Filter by position type: forward or defense",
        pattern="^(forward|defense)$",
    ),
    optimization_mode: Optional[str] = Query(
        None,
        description="Filter by optimization mode: ovr, sal, ap, ovr_sal, ovr_sal_ap",
        pattern="^(ovr|sal|ap|ovr_sal|ovr_sal_ap)$",
    ),
    limit: int = Query(20, ge=1, le=100, description="Max runs to return"),
):
    """
    List available Goal 1 pipeline runs.
    
    Use this to see what optimization runs have been performed
    and select a specific run to view results from.
    """
    store = get_results_store()
    runs = store.list_runs(
        position_type=position_type,
        optimization_mode=optimization_mode,
        limit=limit,
    )
    
    return RunListResponse(runs=runs, total=len(runs))


@router.get("/{pos}/{mode}", response_model=BestLinesResponse)
async def get_best_lines(
    pos: str,
    mode: str,
    limit: int = Query(50, ge=1, le=500, description="Max lines to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    run_id: Optional[int] = Query(None, description="Specific run ID (defaults to latest)"),
    order_by: str = Query(
        "ranking_score DESC",
        description="Sort order",
        pattern="^(ranking_score|total_ovr|total_salary|id) (ASC|DESC)$",
    ),
):
    """
    Get best concrete lines for a position type and optimization mode.
    
    ## Path Parameters
    
    - **pos**: Position type - `forward` or `defense`
    - **mode**: Optimization mode - `ovr`, `sal`, `ap`, `ovr_sal`, or `ovr_sal_ap`
    
    ## Query Parameters
    
    - **limit**: Maximum number of lines to return (default: 50)
    - **offset**: Pagination offset (default: 0)
    - **run_id**: Specific run ID to query (default: latest run for pos/mode)
    - **order_by**: Sort order (default: ranking_score DESC)
    
    ## Example
    
    ```
    GET /best/forward/ovr?limit=10
    GET /best/defense/sal?run_id=5&limit=20
    ```
    
    ## Response
    
    Returns the best concrete lines with full player details,
    activated combos, and scores.
    """
    # Validate position type
    if pos not in ("forward", "defense"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid position type: {pos}. Must be 'forward' or 'defense'.",
        )
    
    # Validate optimization mode
    valid_modes = {"ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"}
    if mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optimization mode: {mode}. Must be one of: {', '.join(valid_modes)}",
        )
    
    store = get_results_store()
    
    # Get the run (specified or latest)
    if run_id:
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(
                status_code=404,
                detail=f"Run {run_id} not found.",
            )
        # Verify the run matches requested pos/mode
        if run.position_type.value != pos or run.optimization_mode.value != mode:
            raise HTTPException(
                status_code=400,
                detail=f"Run {run_id} is for {run.position_type.value}/{run.optimization_mode.value}, "
                       f"not {pos}/{mode}.",
            )
    else:
        run = store.get_latest_run(position_type=pos, optimization_mode=mode)
        if not run:
            return BestLinesResponse(
                success=True,
                run=None,
                position_type=pos,
                optimization_mode=mode,
                total_lines=0,
                lines=[],
            )
    
    # Get concrete lines
    lines = store.get_concrete_lines(
        run_id=run.id,
        limit=limit,
        offset=offset,
        order_by=order_by,
    )
    
    # Get total count
    total_lines = store.count_concrete_lines(run.id)
    
    # Enrich with player details
    enriched_lines = _enrich_lines(lines, pos)
    
    return BestLinesResponse(
        success=True,
        run=run,
        position_type=pos,
        optimization_mode=mode,
        total_lines=total_lines,
        lines=enriched_lines,
    )


@router.get("/{pos}/{mode}/summary")
async def get_best_lines_summary(
    pos: str,
    mode: str,
    run_id: Optional[int] = Query(None, description="Specific run ID"),
):
    """
    Get a summary of best lines without full player details.
    
    Lighter endpoint for quick overview of available results.
    """
    if pos not in ("forward", "defense"):
        raise HTTPException(status_code=400, detail=f"Invalid position: {pos}")
    
    valid_modes = {"ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"}
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    
    store = get_results_store()
    
    if run_id:
        run = store.get_run(run_id)
    else:
        run = store.get_latest_run(position_type=pos, optimization_mode=mode)
    
    if not run:
        return {
            "has_results": False,
            "position_type": pos,
            "optimization_mode": mode,
            "run": None,
            "total_lines": 0,
        }
    
    total_lines = store.count_concrete_lines(run.id)
    
    # Get top 3 lines for preview
    top_lines = store.get_concrete_lines(run_id=run.id, limit=3)
    
    return {
        "has_results": True,
        "position_type": pos,
        "optimization_mode": mode,
        "run": {
            "id": run.id,
            "timestamp": run.run_timestamp,
            "parameters": run.parameters,
        },
        "total_lines": total_lines,
        "top_scores": [line.ranking_score for line in top_lines],
    }
