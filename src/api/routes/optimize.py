"""
Optimization endpoints for NHL 26 Line Combos Optimizer.

These endpoints integrate with the Clingo ASP solver to find optimal line combinations.

=============================================================================
ASP TEAM INTEGRATION GUIDE
=============================================================================

This file contains the API endpoints that call the ASP solver.
The ASP team needs to implement the solver module (src/asp/solver.py).

Current structure:
1. API receives OptimizationRequest from frontend
2. API calls ASP solver with constraints
3. ASP solver returns solutions
4. API formats and returns OptimizationResponse

The ASP solver interface is defined below. Implement it in src/asp/solver.py

=============================================================================
"""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException

from ...core.data import get_data_loader
from ...core.models import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationConstraints,
    OptimizationTarget,
    LineSolution,
    ActiveCombo,
    Player,
    Position,
    RewardType,
)

# Optional (non-ASP) demo solver for Goal 2, used to unblock interactive demo work.
try:
    from ...asp.goal2_bruteforce import Goal2BruteForceSolver
except Exception:  # pragma: no cover
    Goal2BruteForceSolver = None  # type: ignore

# ASP Solver import - to be implemented by ASP team
# from ...asp.solver import ASPSolver

router = APIRouter()


# =============================================================================
# ASP SOLVER INTERFACE (For ASP Team to implement)
# =============================================================================

class ASPSolverInterface:
    """
    Interface for the ASP solver.
    
    ASP TEAM: Implement this interface in src/asp/solver.py
    
    The solver should:
    1. Generate ASP facts from player/combo data
    2. Apply constraints as ASP rules
    3. Run Clingo to find optimal solutions
    4. Parse and return results
    
    Example implementation structure:
    
    ```python
    import clingo
    from src.core.data_loader import get_data_loader
    
    class ASPSolver:
        def __init__(self):
            self.loader = get_data_loader()
        
        def optimize_forward_line(
            self,
            constraints: OptimizationConstraints,
            target: OptimizationTarget,
            num_solutions: int = 5,
        ) -> list[LineSolution]:
            # 1. Get candidate players
            forwards = self.loader.get_forwards()
            combos = self.loader.get_forward_combos()
            
            # 2. Apply pre-filters
            forwards = self._filter_players(forwards, constraints)
            
            # 3. Generate ASP program
            program = self._generate_asp_program(forwards, combos, constraints)
            
            # 4. Run Clingo
            ctl = clingo.Control()
            ctl.add("base", [], program)
            ctl.ground([("base", [])])
            
            solutions = []
            with ctl.solve(yield_=True) as handle:
                for model in handle:
                    solution = self._parse_model(model, forwards, combos)
                    solutions.append(solution)
                    if len(solutions) >= num_solutions:
                        break
            
            return solutions
    ```
    """
    
    def optimize_forward_line(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        """
        Find optimal forward line (3 players).
        
        Args:
            constraints: User-defined constraints
            target: What to optimize for (OVR, salary, AP, balanced)
            num_solutions: Number of solutions to return
            
        Returns:
            List of LineSolution objects, sorted by optimality
        """
        raise NotImplementedError("ASP team: Implement this method")
    
    def optimize_defense_pair(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        """
        Find optimal defense pair (2 players).
        """
        raise NotImplementedError("ASP team: Implement this method")
    
    def optimize_full_team(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        """
        Find optimal full team (4 FWD lines + 3 DEF pairs + 2 goalies).
        """
        raise NotImplementedError("ASP team: Implement this method")
    
    def validate_line(
        self,
        player_ids: list[int],
        position_type: str,  # "forward" or "defense"
    ) -> dict:
        """
        Validate a user-selected line and return active combos.
        
        Args:
            player_ids: List of player IDs in the line
            position_type: "forward" (3 players) or "defense" (2 players)
            
        Returns:
            Dict with validation results and active combos
        """
        raise NotImplementedError("ASP team: Implement this method")


# =============================================================================
# PLACEHOLDER SOLVER (Remove when ASP team implements real solver)
# =============================================================================

class PlaceholderSolver(ASPSolverInterface):
    """
    Placeholder solver that returns mock data.
    
    This allows the API and frontend to be developed in parallel with ASP.
    Replace with real ASPSolver when ready.
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def optimize_forward_line(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        """Return top N forwards by OVR as placeholder."""
        forwards = self.loader.get_forwards()
        
        # Apply basic filters
        filtered = self.loader.filter_players(
            forwards,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )
        
        # Sort by OVR
        filtered.sort(key=lambda x: x.overall, reverse=True)
        
        # Get unique players (best card per player)
        seen_ids = set()
        unique = []
        for p in filtered:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique.append(p)
        
        solutions = []
        # Create mock solutions using top players
        for i in range(min(num_solutions, len(unique) // 3)):
            start = i * 3
            players = unique[start:start + 3]
            if len(players) < 3:
                break
            
            # Convert to generic Player objects
            line_players = [
                Player(
                    id=p.id,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    event=p.event,
                    overall=p.overall,
                    nationality=p.nationality,
                    league=p.league,
                    team=p.team,
                    position=Position.FORWARD,
                )
                for p in players
            ]
            
            total_ovr = sum(p.overall for p in players)
            
            solution = LineSolution(
                rank=i + 1,
                players=line_players,
                total_base_ovr=total_ovr,
                ovr_bonus=0,  # Placeholder - ASP will calculate real bonus
                effective_ovr=total_ovr,
                total_salary=0,  # Placeholder - need salary data
                total_ap=0,  # Placeholder - need AP data
                active_combos=[],  # Placeholder - ASP will find combos
            )
            solutions.append(solution)
        
        return solutions
    
    def optimize_defense_pair(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        """Return top N defense players by OVR as placeholder."""
        defense = self.loader.get_defense()
        
        filtered = self.loader.filter_players(
            defense,
            min_ovr=constraints.min_ovr,
            team=constraints.required_team,
            nationality=constraints.required_nationality,
            event=constraints.required_event,
            excluded_ids=constraints.excluded_player_ids,
        )
        
        filtered.sort(key=lambda x: x.overall, reverse=True)
        
        seen_ids = set()
        unique = []
        for p in filtered:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique.append(p)
        
        solutions = []
        for i in range(min(num_solutions, len(unique) // 2)):
            start = i * 2
            players = unique[start:start + 2]
            if len(players) < 2:
                break
            
            line_players = [
                Player(
                    id=p.id,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    event=p.event,
                    overall=p.overall,
                    nationality=p.nationality,
                    league=p.league,
                    team=p.team,
                    position=Position.DEFENSE,
                )
                for p in players
            ]
            
            total_ovr = sum(p.overall for p in players)
            
            solution = LineSolution(
                rank=i + 1,
                players=line_players,
                total_base_ovr=total_ovr,
                ovr_bonus=0,
                effective_ovr=total_ovr,
                total_salary=0,
                total_ap=0,
                active_combos=[],
            )
            solutions.append(solution)
        
        return solutions
    
    def optimize_full_team(
        self,
        constraints: OptimizationConstraints,
        target: OptimizationTarget,
        num_solutions: int = 5,
    ) -> list[LineSolution]:
        """Placeholder - full team optimization not yet implemented."""
        raise NotImplementedError(
            "Full team optimization requires ASP implementation. "
            "Use forward-line or defense-pair endpoints for now."
        )
    
    def validate_line(
        self,
        player_ids: list[int],
        position_type: str,
    ) -> dict:
        """Validate a line and find active combos (placeholder)."""
        if position_type == "forward":
            players = self.loader.get_forwards()
            combos = self.loader.get_forward_combos()
            expected_count = 3
        else:
            players = self.loader.get_defense()
            combos = self.loader.get_defense_combos()
            expected_count = 2
        
        if len(player_ids) != expected_count:
            return {
                "valid": False,
                "error": f"Expected {expected_count} players, got {len(player_ids)}",
            }
        
        # Find players
        selected = []
        for pid in player_ids:
            found = next((p for p in players if p.id == pid), None)
            if not found:
                return {
                    "valid": False,
                    "error": f"Player {pid} not found",
                }
            selected.append(found)
        
        # Check combos (simplified - ASP will do proper matching)
        active = []
        for combo in combos:
            conditions = combo.get_conditions()
            matches = 0
            for i, cond in enumerate(conditions):
                if i < len(selected) and selected[i].matches_condition(cond.type, cond.key):
                    matches += 1
            
            if matches == len(conditions):
                active.append({
                    "id": combo.id,
                    "reward_type": combo.reward_type.value,
                    "reward_amount": combo.reward_amount,
                })
        
        total_ovr = sum(p.overall for p in selected)
        ovr_bonus = sum(c["reward_amount"] for c in active if c["reward_type"] == "OVR")
        
        return {
            "valid": True,
            "players": [
                {
                    "id": p.id,
                    "name": f"{p.first_name} {p.last_name}",
                    "overall": p.overall,
                    "team": p.team,
                    "nationality": p.nationality,
                }
                for p in selected
            ],
            "total_base_ovr": total_ovr,
            "ovr_bonus": ovr_bonus,
            "effective_ovr": total_ovr + ovr_bonus,
            "active_combos": active,
        }


# Use placeholder for now - replace with real solver when ASP team implements it
# solver = ASPSolver()  # Real implementation
if Goal2BruteForceSolver is not None:
    solver = Goal2BruteForceSolver()
else:
    solver = PlaceholderSolver()  # Placeholder


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/forward-line", response_model=OptimizationResponse)
async def optimize_forward_line(request: OptimizationRequest):
    """
    Find optimal forward line (3 players).
    
    This endpoint uses the Clingo ASP solver to find the best
    forward line combinations based on the given constraints.
    
    ## Request Body
    
    ```json
    {
        "constraints": {
            "min_ovr": 80,
            "max_salary": 30000000,
            "max_ap": 9,
            "require_center": true,
            "excluded_player_ids": [2029, 1063],
            "required_team": "DET",
            "required_nationality": null,
            "required_event": null
        },
        "optimization_target": "ovr",
        "num_solutions": 5
    }
    ```
    
    ## Response
    
    Returns up to `num_solutions` optimal lines, each with:
    - Players in the line
    - Total OVR (base + bonus)
    - Active combos that give bonuses
    - Computation statistics
    """
    start_time = time.time()
    
    try:
        solutions = solver.optimize_forward_line(
            constraints=request.constraints,
            target=request.optimization_target,
            num_solutions=request.num_solutions,
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        candidates_evaluated = getattr(solver, "last_combinations_evaluated", 0)
        if not candidates_evaluated:
            candidates_evaluated = getattr(solver, "last_candidates_evaluated", 0)

        return OptimizationResponse(
            success=True,
            message=f"Found {len(solutions)} solution(s)",
            solutions=solutions,
            computation_time_ms=elapsed_ms,
            candidates_evaluated=int(candidates_evaluated),
        )
    
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}",
        )


@router.post("/defense-pair", response_model=OptimizationResponse)
async def optimize_defense_pair(request: OptimizationRequest):
    """
    Find optimal defense pair (2 players).
    
    Similar to forward-line but for defense players.
    """
    start_time = time.time()
    
    try:
        solutions = solver.optimize_defense_pair(
            constraints=request.constraints,
            target=request.optimization_target,
            num_solutions=request.num_solutions,
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        candidates_evaluated = getattr(solver, "last_combinations_evaluated", 0)
        if not candidates_evaluated:
            candidates_evaluated = getattr(solver, "last_candidates_evaluated", 0)

        return OptimizationResponse(
            success=True,
            message=f"Found {len(solutions)} solution(s)",
            solutions=solutions,
            computation_time_ms=elapsed_ms,
            candidates_evaluated=int(candidates_evaluated),
        )
    
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/full-team", response_model=OptimizationResponse)
async def optimize_full_team(request: OptimizationRequest):
    """
    Find optimal full team.
    
    This is the most complex optimization:
    - 4 forward lines (12 forwards)
    - 3 defense pairs (6 defensemen)
    - 2 goalies
    
    Total: 20 players (or 23 with extras)
    
    **Note**: This endpoint requires full ASP implementation.
    May take longer to compute due to the large search space.
    """
    start_time = time.time()
    
    try:
        solutions = solver.optimize_full_team(
            constraints=request.constraints,
            target=request.optimization_target,
            num_solutions=request.num_solutions,
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return OptimizationResponse(
            success=True,
            message=f"Found {len(solutions)} solution(s)",
            solutions=solutions,
            computation_time_ms=elapsed_ms,
            candidates_evaluated=0,
        )
    
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/validate")
async def validate_line(
    player_ids: list[int],
    position_type: str = "forward",
):
    """
    Validate a user-selected line and show active combos.
    
    Use this endpoint to:
    - Check if a manually selected line is valid
    - See which combos are activated
    - Calculate total OVR bonus
    
    ## Parameters
    
    - `player_ids`: List of player IDs (3 for forward, 2 for defense)
    - `position_type`: "forward" or "defense"
    
    ## Example
    
    ```
    POST /optimize/validate?position_type=forward
    Body: [2029, 1437, 1221]
    ```
    """
    if position_type not in ["forward", "defense"]:
        raise HTTPException(
            status_code=400,
            detail="position_type must be 'forward' or 'defense'",
        )
    
    result = solver.validate_line(player_ids, position_type)
    
    if not result.get("valid", False):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Invalid line"),
        )
    
    return result


@router.get("/status")
async def get_solver_status():
    """
    Get ASP solver status.
    
    Returns information about the solver implementation status.
    Useful for frontend to know which features are available.
    """
    solver_class = solver.__class__.__name__
    is_placeholder = isinstance(solver, PlaceholderSolver)
    is_goal2_bruteforce = solver_class == "Goal2BruteForceSolver"
    
    return {
        "solver_type": (
            "placeholder"
            if is_placeholder
            else "goal2_bruteforce"
            if is_goal2_bruteforce
            else "clingo"
        ),
        "features": {
            "forward_line": True,
            "defense_pair": True,
            "full_team": not is_placeholder,
            "validate": True,
        },
        "message": (
            "Using placeholder solver. ASP team: implement src/asp/solver.py"
            if is_placeholder
            else "Using brute-force demo solver (Goal 2)."
            if is_goal2_bruteforce
            else "Clingo ASP solver active"
        ),
    }
