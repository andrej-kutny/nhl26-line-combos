"""
Best lines endpoint for NHL 26 Line Combos Optimizer.

Exposes Goal 1 pipeline results to the frontend.

Endpoints:
    GET /best/{pos}/{mode} - Get best concrete lines for position/mode
    GET /best/runs - List available Goal 1 runs
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.data import get_data_loader, get_results_store, ensure_results
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
    auto_run: bool = Query(
        True,
        description="Automatically run pipeline if no results exist (default: True)",
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
    - **auto_run**: Automatically run pipeline if no results exist (default: True)
    
    ## Auto-Run Feature
    
    If `auto_run=True` (default) and no results exist for the requested position/mode,
    the endpoint will automatically execute the Goal 1 pipeline to generate results.
    This ensures the frontend always has data to display, even on first access.
    
    To disable auto-run (e.g., for faster responses when you know results exist),
    set `auto_run=False`.
    
    ## Example
    
    ```
    GET /best/forward/ovr?limit=10
    GET /best/defense/sal?run_id=5&limit=20
    GET /best/forward/ovr?auto_run=false  # Skip auto-generation
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
        # Auto-run pipeline if no results exist (if enabled)
        # Use async ensure_results to run pipeline in thread pool,
        # allowing other requests to be handled concurrently instead of blocking
        run_id_auto = None
        if auto_run:
            try:
                run_id_auto = await ensure_results(
                    position_type=pos,
                    optimization_mode=mode,
                    top_k=50,  # Reasonable default for auto-generation
                    player_limit=50,  # Reasonable default to avoid long computation
                    min_lines=1,
                    auto_run=True,
                )
            except Exception as e:
                # Log error but don't fail the request - return empty results instead
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to auto-run pipeline for {pos}/{mode}: {e}", exc_info=True)
        
        if run_id_auto:
            run = store.get_run(run_id_auto)
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


@router.post("/{pos}/{mode}/generate")
async def generate_best_lines(
    pos: str,
    mode: str,
    top_k: int = Query(50, ge=1, le=200, description="Number of Stage A solutions"),
    player_limit: int = Query(50, ge=10, le=200, description="Max players per Stage B pool"),
):
    """
    Manually trigger pipeline execution to generate best lines.
    
    This endpoint runs the Goal 1 pipeline for the specified position and mode,
    generating and storing results in the database.
    
    Returns the run ID and statistics.
    """
    if pos not in ("forward", "defense"):
        raise HTTPException(status_code=400, detail=f"Invalid position: {pos}")
    
    valid_modes = {"ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"}
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    
    try:
        from ...asp.pipeline import run_goal1_pipeline
        
        result = run_goal1_pipeline(
            position_type=pos,
            optimization_mode=mode,
            top_k=top_k,
            player_limit=player_limit,
            store_results=True,
        )
        
        return {
            "success": True,
            "run_id": result.run_id,
            "position_type": pos,
            "optimization_mode": mode,
            "stage_a_solutions": result.stage_a_solutions,
            "stage_b_lines_total": result.stage_b_lines_total,
            "total_time_ms": result.total_time_ms,
            "stage_a_time_ms": result.stage_a_time_ms,
            "stage_b_time_ms": result.stage_b_time_ms,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}",
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
