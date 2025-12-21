"""
Pipeline Manager - Auto-run Goal 1 pipeline when results are missing.

Check if pipeline results exist and
automatically run the pipeline if needed. All functions are async to avoid
blocking the FastAPI event loop.
"""

import asyncio
import logging
from typing import Literal, Optional

from .goal1_store import Goal1ResultsStore

logger = logging.getLogger(__name__)


def _get_results_store():
    """Get results store instance (avoid circular import)."""
    from . import get_results_store
    return get_results_store()


def _run_pipeline(*args, **kwargs):
    """Run pipeline (lazy import to avoid circular dependency)."""
    from ...asp.pipeline import run_goal1_pipeline
    return run_goal1_pipeline(*args, **kwargs)


async def has_results(
    position_type: Literal["forward", "defense"],
    optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
    min_lines: int = 1,
) -> bool:
    """
    Check if results exist for a given position type and optimization mode.
    
    Args:
        position_type: "forward" or "defense"
        optimization_mode: Optimization mode to check
        min_lines: Minimum number of concrete lines required (default: 1)
        
    Returns:
        True if results exist with at least min_lines, False otherwise
    """
    # Run synchronous check in thread pool to avoid blocking
    store = await asyncio.to_thread(_get_results_store)
    
    # Check if a run exists
    run = await asyncio.to_thread(
        store.get_latest_run,
        position_type=position_type,
        optimization_mode=optimization_mode,
    )
    if not run:
        return False
    
    # Check if the run has concrete lines
    line_count = await asyncio.to_thread(store.count_concrete_lines, run.id)
    return line_count >= min_lines


async def ensure_results(
    position_type: Literal["forward", "defense"],
    optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
    top_k: int = 50,
    player_limit: int = 50,
    min_lines: int = 1,
    auto_run: bool = True,
) -> Optional[int]:
    """
    Ensure results exist for a given position type and optimization mode.
    
    If results don't exist (or have fewer than min_lines), automatically
    runs the pipeline to generate them. Runs in a thread pool to avoid
    blocking the event loop, allowing other requests to be handled concurrently.
    
    Args:
        position_type: "forward" or "defense"
        optimization_mode: Optimization mode
        top_k: Number of Stage A solutions to generate (default: 50)
        player_limit: Max players per Stage B candidate pool (default: 50)
        min_lines: Minimum number of concrete lines required (default: 1)
        auto_run: If True, automatically run pipeline if results missing (default: True)
        
    Returns:
        Run ID if results exist or were generated, None if auto_run=False and no results
    """
    # Check if results already exist (run in thread pool to avoid blocking)
    if await has_results(position_type, optimization_mode, min_lines=min_lines):
        store = await asyncio.to_thread(_get_results_store)
        run = await asyncio.to_thread(
            store.get_latest_run,
            position_type=position_type,
            optimization_mode=optimization_mode,
        )
        line_count = await asyncio.to_thread(store.count_concrete_lines, run.id)
        logger.info(
            f"Results already exist for {position_type}/{optimization_mode}: "
            f"run_id={run.id}, lines={line_count}"
        )
        return run.id
    
    if not auto_run:
        logger.info(
            f"No results found for {position_type}/{optimization_mode} and auto_run=False"
        )
        return None
    
    # Run the pipeline in a thread pool to avoid blocking
    logger.info(
        f"Running pipeline for {position_type}/{optimization_mode} "
        f"(top_k={top_k}, player_limit={player_limit}) in background thread"
    )
    
    try:
        # Run blocking pipeline in thread pool
        result = await asyncio.to_thread(
            _run_pipeline,
            position_type=position_type,
            optimization_mode=optimization_mode,
            top_k=top_k,
            player_limit=player_limit,
            store_results=True,
        )
        
        if result.run_id and result.stage_b_lines_total >= min_lines:
            logger.info(
                f"Pipeline completed successfully: run_id={result.run_id}, "
                f"lines={result.stage_b_lines_total}, "
                f"time={result.total_time_ms:.0f}ms"
            )
            return result.run_id
        else:
            logger.warning(
                f"Pipeline completed but generated only {result.stage_b_lines_total} lines "
                f"(minimum: {min_lines})"
            )
            return result.run_id if result.run_id else None
            
    except Exception as e:
        logger.error(
            f"Pipeline failed for {position_type}/{optimization_mode}: {e}",
            exc_info=True,
        )
        raise


async def get_or_create_run(
    position_type: Literal["forward", "defense"],
    optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
    top_k: int = 50,
    player_limit: int = 50,
    min_lines: int = 1,
) -> Optional[int]:
    """
    Get existing run ID or create a new run by executing the pipeline.
    
    Convenience wrapper around ensure_results with auto_run=True.
    
    Args:
        position_type: "forward" or "defense"
        optimization_mode: Optimization mode
        top_k: Number of Stage A solutions to generate
        player_limit: Max players per Stage B candidate pool
        min_lines: Minimum number of concrete lines required
        
    Returns:
        Run ID, or None if pipeline failed
    """
    return await ensure_results(
        position_type=position_type,
        optimization_mode=optimization_mode,
        top_k=top_k,
        player_limit=player_limit,
        min_lines=min_lines,
        auto_run=True,
    )
