"""
Line combination endpoints for NHL 26 Line Combos Optimizer.

These endpoints provide access to line combinations and their rewards.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from ...core.data_loader import get_data_loader
from ...core.models import ForwardLineCombo, DefenseLineCombo, RewardType

router = APIRouter()


# =============================================================================
# FORWARD COMBO ENDPOINTS
# =============================================================================

@router.get("/forward", response_model=list[ForwardLineCombo])
async def get_forward_combos(
    reward_type: Optional[str] = Query(
        default=None, 
        description="Filter by reward type: OVR, SAL, AP"
    ),
    min_reward: int = Query(default=0, description="Minimum reward amount"),
    team: Optional[str] = Query(
        default=None, 
        description="Filter combos that include this team condition"
    ),
    nationality: Optional[str] = Query(
        default=None, 
        description="Filter combos that include this nationality condition"
    ),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum results"),
):
    """
    Get all forward line combinations (3-player combos).
    
    Forward combos require 3 players, each satisfying one condition.
    
    Reward Types:
    - OVR: Adds to overall rating
    - SAL: Reduces effective salary
    - AP: Adds ability points
    
    Example:
        GET /combos/forward?reward_type=OVR&min_reward=2
    """
    loader = get_data_loader()
    combos = loader.get_forward_combos()
    
    filtered = []
    for combo in combos:
        # Filter by reward type
        if reward_type and combo.reward_type.value != reward_type.upper():
            continue
        
        # Filter by minimum reward
        if combo.reward_amount < min_reward:
            continue
        
        # Filter by team condition
        if team:
            team_upper = team.upper()
            has_team = any(
                c.type == "team" and c.key == team_upper 
                for c in combo.get_conditions()
            )
            if not has_team:
                continue
        
        # Filter by nationality condition
        if nationality:
            nat_upper = nationality.upper()
            has_nat = any(
                c.type == "nationality" and c.key == nat_upper 
                for c in combo.get_conditions()
            )
            if not has_nat:
                continue
        
        filtered.append(combo)
    
    # Sort by reward amount descending
    filtered.sort(key=lambda x: x.reward_amount, reverse=True)
    
    return filtered[:limit]


@router.get("/forward/{combo_id}", response_model=ForwardLineCombo)
async def get_forward_combo_by_id(combo_id: int):
    """
    Get a specific forward combo by ID.
    
    Use this to get details about a specific combo and its conditions.
    """
    loader = get_data_loader()
    combos = loader.get_forward_combos()
    
    for combo in combos:
        if combo.id == combo_id:
            return combo
    
    raise HTTPException(status_code=404, detail=f"Forward combo with ID {combo_id} not found")


@router.get("/forward/{combo_id}/matching-players")
async def get_forward_combo_matching_players(
    combo_id: int,
    min_ovr: int = Query(default=0, description="Minimum player OVR"),
):
    """
    Get players that can satisfy each condition of a forward combo.
    
    This is useful for:
    - Understanding which players can activate a combo
    - Pre-filtering candidates for the ASP solver
    
    Returns players grouped by condition slot (1, 2, 3).
    """
    loader = get_data_loader()
    combos = loader.get_forward_combos()
    
    combo = None
    for c in combos:
        if c.id == combo_id:
            combo = c
            break
    
    if not combo:
        raise HTTPException(status_code=404, detail=f"Forward combo with ID {combo_id} not found")
    
    forwards = loader.get_forwards()
    if min_ovr > 0:
        forwards = [p for p in forwards if p.overall >= min_ovr]
    
    result = {
        "combo": combo,
        "slot1_players": [],
        "slot2_players": [],
        "slot3_players": [],
    }
    
    conditions = combo.get_conditions()
    for player in forwards:
        if player.matches_condition(conditions[0].type, conditions[0].key):
            result["slot1_players"].append(player)
        if player.matches_condition(conditions[1].type, conditions[1].key):
            result["slot2_players"].append(player)
        if player.matches_condition(conditions[2].type, conditions[2].key):
            result["slot3_players"].append(player)
    
    # Sort each slot by OVR
    for key in ["slot1_players", "slot2_players", "slot3_players"]:
        result[key].sort(key=lambda x: x.overall, reverse=True)
    
    # Add counts
    result["slot1_count"] = len(result["slot1_players"])
    result["slot2_count"] = len(result["slot2_players"])
    result["slot3_count"] = len(result["slot3_players"])
    
    return result


# =============================================================================
# DEFENSE COMBO ENDPOINTS
# =============================================================================

@router.get("/defense", response_model=list[DefenseLineCombo])
async def get_defense_combos(
    reward_type: Optional[str] = Query(
        default=None, 
        description="Filter by reward type: OVR, SAL, AP"
    ),
    min_reward: int = Query(default=0, description="Minimum reward amount"),
    team: Optional[str] = Query(
        default=None, 
        description="Filter combos that include this team condition"
    ),
    nationality: Optional[str] = Query(
        default=None, 
        description="Filter combos that include this nationality condition"
    ),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum results"),
):
    """
    Get all defense line combinations (2-player combos).
    
    Defense combos require 2 players (defense pair or defense + goalie),
    each satisfying one condition.
    
    Example:
        GET /combos/defense?reward_type=SAL&min_reward=5
    """
    loader = get_data_loader()
    combos = loader.get_defense_combos()
    
    filtered = []
    for combo in combos:
        if reward_type and combo.reward_type.value != reward_type.upper():
            continue
        
        if combo.reward_amount < min_reward:
            continue
        
        if team:
            team_upper = team.upper()
            has_team = any(
                c.type == "team" and c.key == team_upper 
                for c in combo.get_conditions()
            )
            if not has_team:
                continue
        
        if nationality:
            nat_upper = nationality.upper()
            has_nat = any(
                c.type == "nationality" and c.key == nat_upper 
                for c in combo.get_conditions()
            )
            if not has_nat:
                continue
        
        filtered.append(combo)
    
    filtered.sort(key=lambda x: x.reward_amount, reverse=True)
    return filtered[:limit]


@router.get("/defense/{combo_id}", response_model=DefenseLineCombo)
async def get_defense_combo_by_id(combo_id: int):
    """Get a specific defense combo by ID."""
    loader = get_data_loader()
    combos = loader.get_defense_combos()
    
    for combo in combos:
        if combo.id == combo_id:
            return combo
    
    raise HTTPException(status_code=404, detail=f"Defense combo with ID {combo_id} not found")


@router.get("/defense/{combo_id}/matching-players")
async def get_defense_combo_matching_players(
    combo_id: int,
    min_ovr: int = Query(default=0, description="Minimum player OVR"),
):
    """
    Get players that can satisfy each condition of a defense combo.
    
    Returns defense players grouped by condition slot (1, 2).
    Note: May also include goalies depending on the combo type.
    """
    loader = get_data_loader()
    combos = loader.get_defense_combos()
    
    combo = None
    for c in combos:
        if c.id == combo_id:
            combo = c
            break
    
    if not combo:
        raise HTTPException(status_code=404, detail=f"Defense combo with ID {combo_id} not found")
    
    defense = loader.get_defense()
    if min_ovr > 0:
        defense = [p for p in defense if p.overall >= min_ovr]
    
    result = {
        "combo": combo,
        "slot1_players": [],
        "slot2_players": [],
    }
    
    conditions = combo.get_conditions()
    for player in defense:
        if player.matches_condition(conditions[0].type, conditions[0].key):
            result["slot1_players"].append(player)
        if player.matches_condition(conditions[1].type, conditions[1].key):
            result["slot2_players"].append(player)
    
    for key in ["slot1_players", "slot2_players"]:
        result[key].sort(key=lambda x: x.overall, reverse=True)
    
    result["slot1_count"] = len(result["slot1_players"])
    result["slot2_count"] = len(result["slot2_players"])
    
    return result


# =============================================================================
# SUMMARY ENDPOINTS
# =============================================================================

@router.get("/summary")
async def get_combos_summary():
    """
    Get a summary of all available line combinations.
    
    Useful for frontend to display combo statistics and filter options.
    """
    loader = get_data_loader()
    fwd_combos = loader.get_forward_combos()
    def_combos = loader.get_defense_combos()
    
    def summarize_combos(combos):
        reward_types = {}
        max_rewards = {"OVR": 0, "SAL": 0, "AP": 0}
        teams = set()
        nationalities = set()
        events = set()
        
        for combo in combos:
            rt = combo.reward_type.value
            reward_types[rt] = reward_types.get(rt, 0) + 1
            max_rewards[rt] = max(max_rewards[rt], combo.reward_amount)
            
            for cond in combo.get_conditions():
                if cond.type == "team":
                    teams.add(cond.key)
                elif cond.type == "nationality":
                    nationalities.add(cond.key)
                elif cond.type == "event":
                    events.add(cond.key)
        
        return {
            "count": len(combos),
            "by_reward_type": reward_types,
            "max_rewards": max_rewards,
            "teams_in_combos": sorted(list(teams)),
            "nationalities_in_combos": sorted(list(nationalities)),
            "events_in_combos": sorted(list(events)),
        }
    
    return {
        "forward_combos": summarize_combos(fwd_combos),
        "defense_combos": summarize_combos(def_combos),
    }

