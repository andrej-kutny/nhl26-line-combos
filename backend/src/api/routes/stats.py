"""
Statistics endpoints for NHL 26 Line Combos Optimizer.

These endpoints provide dataset statistics and metadata.
"""

from fastapi import APIRouter

from ...core.data import get_data_loader

router = APIRouter()


@router.get("/")
async def get_all_stats():
    """
    Get complete dataset statistics.
    
    Returns counts of players, combos, and available filter values
    (teams, nationalities, events).
    
    Useful for:
    - Frontend to populate filter dropdowns
    - Dashboard/summary displays
    - Debugging data loading issues
    """
    loader = get_data_loader()
    return loader.get_stats()


@router.get("/players")
async def get_player_stats():
    """
    Get player-specific statistics.
    
    Returns:
    - Card counts by position
    - Unique player counts
    - OVR distributions
    """
    loader = get_data_loader()
    
    forwards = loader.get_forwards()
    defense = loader.get_defense()
    goalies = loader.get_goalies()
    
    def calc_ovr_stats(players):
        if not players:
            return {"min": 0, "max": 0, "avg": 0}
        ovrs = [p.overall for p in players]
        return {
            "min": min(ovrs),
            "max": max(ovrs),
            "avg": round(sum(ovrs) / len(ovrs), 1),
        }
    
    return {
        "forwards": {
            "card_count": len(forwards),
            "unique_players": len(set(p.id for p in forwards)),
            "ovr_stats": calc_ovr_stats(forwards),
        },
        "defense": {
            "card_count": len(defense),
            "unique_players": len(set(p.id for p in defense)),
            "ovr_stats": calc_ovr_stats(defense),
        },
        "goalies": {
            "card_count": len(goalies),
            "unique_players": len(set(p.id for p in goalies)),
            "ovr_stats": calc_ovr_stats(goalies),
        },
    }


@router.get("/combos")
async def get_combo_stats():
    """
    Get line combination statistics.
    
    Returns:
    - Combo counts by reward type
    - Max/min rewards
    - Condition type distributions
    """
    loader = get_data_loader()
    
    fwd_combos = loader.get_forward_combos()
    def_combos = loader.get_defense_combos()
    
    def analyze_combos(combos):
        by_type = {"OVR": 0, "SAL": 0, "AP": 0}
        rewards = {"OVR": [], "SAL": [], "AP": []}
        condition_types = {"team": 0, "nationality": 0, "event": 0}
        
        for combo in combos:
            rt = combo.reward_type.value
            by_type[rt] += 1
            rewards[rt].append(combo.reward_amount)
            
            for cond in combo.get_conditions():
                if cond.type in condition_types:
                    condition_types[cond.type] += 1
        
        reward_stats = {}
        for rt, vals in rewards.items():
            if vals:
                reward_stats[rt] = {
                    "min": min(vals),
                    "max": max(vals),
                    "avg": round(sum(vals) / len(vals), 1),
                }
            else:
                reward_stats[rt] = {"min": 0, "max": 0, "avg": 0}
        
        return {
            "count": len(combos),
            "by_reward_type": by_type,
            "reward_stats": reward_stats,
            "condition_distribution": condition_types,
        }
    
    return {
        "forward_combos": analyze_combos(fwd_combos),
        "defense_combos": analyze_combos(def_combos),
    }


@router.get("/teams")
async def get_available_teams():
    """
    Get list of all teams available in the dataset.
    
    Returns team abbreviations that can be used for filtering.
    """
    loader = get_data_loader()
    stats = loader.get_stats()
    return {
        "teams": stats["teams"],
        "count": stats["team_count"],
    }


@router.get("/nationalities")
async def get_available_nationalities():
    """
    Get list of all nationalities available in the dataset.
    
    Returns nationality values that can be used for filtering.
    """
    loader = get_data_loader()
    stats = loader.get_stats()
    return {
        "nationalities": stats["nationalities"],
        "count": stats["nationality_count"],
    }


@router.get("/events")
async def get_available_events():
    """
    Get list of all events available in the dataset.
    
    Events represent different card releases (ICON, CAP, TOTW, etc.).
    """
    loader = get_data_loader()
    stats = loader.get_stats()
    return {
        "events": stats["events"],
        "count": stats["event_count"],
    }

