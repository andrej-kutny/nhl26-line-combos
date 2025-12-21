"""
Data access package for NHL 26 Line Combos Optimizer.

This package contains data loading and storage classes:
- DataLoader: Load players and combos from SQLite
- Goal1ResultsStore: Store and retrieve Goal 1 pipeline results

Singleton accessor functions are provided for convenience.
"""

from typing import Optional

from .loader import DataLoader
from .goal1_store import Goal1ResultsStore
from .pipeline_manager import (
    has_results,
    ensure_results,
    get_or_create_run,
)

__all__ = [
    "DataLoader",
    "Goal1ResultsStore",
    "get_data_loader",
    "get_results_store",
    "has_results",
    "ensure_results",
    "get_or_create_run",
]

# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

_data_loader: Optional[DataLoader] = None
_results_store: Optional[Goal1ResultsStore] = None


def get_data_loader(data_dir: str = "data/") -> DataLoader:
    """
    Get or create the global DataLoader instance.
    
    Usage:
        from src.core.data import get_data_loader
        
        loader = get_data_loader()
        forwards = loader.get_forwards(min_ovr=85, team="TOR")
    """
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader(data_dir)
    return _data_loader


def get_results_store(data_dir: str = "data/") -> Goal1ResultsStore:
    """
    Get or create the global Goal1ResultsStore instance.
    
    Usage:
        from src.core.data import get_results_store
        
        store = get_results_store()
        run_id = store.create_run("forward", "ovr")
    """
    global _results_store
    if _results_store is None:
        _results_store = Goal1ResultsStore(data_dir)
    return _results_store
