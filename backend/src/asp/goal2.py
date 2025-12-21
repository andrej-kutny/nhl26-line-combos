"""
Goal 2: Direct Concrete Line Optimization.

This module handles:
1. Generating Goal 2 input from player and combo data
2. Running the Goal 2 solver (Clingo-based direct optimization)

Goal 2 is the interactive optimization goal that directly optimizes
over concrete lines with real players without requiring an abstraction stage.
"""

import time
import clingo
from typing import Literal
from pathlib import Path

from ..core.data import get_data_loader
from ..core.models import ForwardLineCombo, DefenseLineCombo
from .interfaces import (
    Goal2Input,
    Goal2Output,
    Goal2ConcreteLineResult,
    Goal2Solver,
    CandidatePlayer,
)


# =============================================================================
# INPUT GENERATOR
# =============================================================================

class Goal2InputGenerator:
    """
    Generates Goal 2 input from player and combo data.
    
    Prepares candidate players and combo definitions for direct optimization.
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def generate(
        self,
        position_type: Literal["forward", "defense"],
        optimization_target: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
        players: list[CandidatePlayer],
        combo_ids: list[int] | None = None,
        num_solutions: int = 10,
    ) -> Goal2Input:
        """
        Generate Goal 2 input for the given position and players.
        
        Args:
            position_type: "forward" or "defense"
            optimization_target: Which metrics to optimize
            players: Candidate players for the line
            combo_ids: Specific combos to enforce (None = all relevant)
            num_solutions: Number of solutions to return
            
        Returns:
            Goal2Input ready for solver
        """
        # Get combos from database
        if position_type == "forward":
            all_combos = self.loader.get_forward_combos()
        else:
            all_combos = self.loader.get_defense_combos()
        
        # Filter combos if specific IDs provided
        if combo_ids:
            combo_map = {c.id: c for c in all_combos}
            combos = [combo_map[cid] for cid in combo_ids if cid in combo_map]
        else:
            combos = all_combos
        
        # Generate facts
        player_facts = self._generate_player_facts(players)
        combo_facts = self._generate_combo_facts(combos, position_type)
        
        # Get weights
        ovr_weight, sal_weight, ap_weight = self._get_weights(position_type, optimization_target)
        
        return Goal2Input(
            position_type=position_type,
            optimization_target=optimization_target,
            players=players,
            player_facts=player_facts,
            combo_facts=combo_facts,
            required_combo_ids=combo_ids or [],
            num_solutions=num_solutions,
            ovr_weight=ovr_weight,
            sal_weight=sal_weight,
            ap_weight=ap_weight,
        )
    
    def _generate_player_facts(self, players: list[CandidatePlayer]) -> list[str]:
        """
        Generate ASP facts for candidate players.
        
        Format: player(CardID, OVR, Team, Nationality, Event).
        """
        facts = []
        for player in players:
            fact = (
                f'player({player.card_id}, {player.overall}, '
                f'"{player.team}", "{player.nationality}", "{player.event}").'
            )
            facts.append(fact)
            
            # Add additional facts for bonuses
            facts.append(f'ovr({player.card_id}, {player.overall}).')
            facts.append(f'salary_val({player.card_id}, {int(player.salary)}).')
            facts.append(f'ap_val({player.card_id}, {player.ap}).')
            
            # Add player ID mapping for uniqueness
            facts.append(f'card_player({player.card_id}, {player.player_id}).')
        
        return facts
    
    def _generate_combo_facts(
        self,
        combos: list[ForwardLineCombo | DefenseLineCombo],
        position_type: str,
    ) -> list[str]:
        """
        Generate ASP facts for combos.
        
        Format:
        - Forward: fwd_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2, entry3).
        - Defense: def_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2).
        """
        facts = []
        
        for combo in combos:
            c1 = combo.condition1
            c2 = combo.condition2
            
            if position_type == "forward":
                c3 = combo.condition3
                fact = (
                    f'fwd_combo({combo.id}, {combo.reward_amount}, '
                    f'"{combo.reward_type.value}", '
                    f'{c1.type}("{c1.key}"), '
                    f'{c2.type}("{c2.key}"), '
                    f'{c3.type}("{c3.key}")).'
                )
            else:  # defense
                fact = (
                    f'def_combo({combo.id}, {combo.reward_amount}, '
                    f'"{combo.reward_type.value}", '
                    f'{c1.type}("{c1.key}"), '
                    f'{c2.type}("{c2.key}")).'
                )
            
            facts.append(fact)
        
        return facts
    
    def _get_weights(
        self,
        position_type: str,
        target: str,
    ) -> tuple[float, float, float]:
        """Get optimization weights based on position and target."""
        if position_type == "forward":
            base_ovr, base_sal = 3.0, 1.0
        else:
            base_ovr, base_sal = 2.0, 1.0
        
        base_ap = 1.0
        
        if target == "ovr":
            return (1.0, 0.0, 0.0)
        elif target == "sal":
            return (0.0, 1.0, 0.0)
        elif target == "ap":
            return (0.0, 0.0, 1.0)
        elif target == "ovr_sal":
            return (base_ovr, base_sal, 0.0)
        else:  # ovr_sal_ap
            return (base_ovr, base_sal, base_ap)


# =============================================================================
# GOAL 2 SOLVER
# =============================================================================

class ClingoGoal2Solver(Goal2Solver):
    """
    Goal 2 solver using Clingo ASP.
    
    Directly optimizes over concrete lines without abstraction stage.
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def solve(self, input_data: Goal2Input) -> Goal2Output:
        """
        Run Goal 2 optimization using Clingo.
        
        Args:
            input_data: Players, combos, and parameters
            
        Returns:
            Goal2Output with top-N concrete lines
        """
        start_time = time.time()
        
        # Determine rules based on position
        current_dir = Path(__file__).parent
        base_path = current_dir / "g2"
        
        rules = [str(base_path / "common.lp")]
        
        if input_data.position_type == "forward":
            rules.append(str(base_path / "fwd_main.lp"))
            rules.append(str(base_path / f"fwd_{input_data.optimization_target}.lp"))
        else:
            rules.append(str(base_path / "def_main.lp"))
            rules.append(str(base_path / f"def_{input_data.optimization_target}.lp"))
        
        # Combine facts
        all_facts = "\n".join(input_data.player_facts + input_data.combo_facts)
        
        # Add constraint facts for required combos
        if input_data.required_combo_ids:
            for combo_id in input_data.required_combo_ids:
                all_facts += f"\nrequired_combo({combo_id})."
        
        # Solve
        res, models, opt, models_c = self._clingo_solve(
            rules,
            all_facts,
            ctl_opts=[str(input_data.num_solutions)]
        )
        
        lines: list[Goal2ConcreteLineResult] = []
        
        for rank, model_symbols in enumerate(models, 1):
            line = self._parse_line_model(model_symbols, input_data)
            if line:
                line.rank = rank
                lines.append(line)
        
        solve_time = (time.time() - start_time) * 1000
        
        return Goal2Output(
            lines=lines,
            solve_time_ms=solve_time,
            total_models_found=models_c
        )
    
    def _clingo_solve(
        self,
        files: list[str],
        extra_rules: str = "",
        ctl_opts: list[str] | None = None
    ) -> tuple:
        """
        Run Clingo solver.
        
        Returns:
            (result, models, opt, models_count)
        """
        opts = list(ctl_opts or [])
        
        try:
            ctl = clingo.Control(opts)
            
            for f in files:
                if Path(f).exists():
                    ctl.load(f)
            
            if extra_rules.strip():
                ctl.add("base", [], extra_rules)
                ctl.ground([("base", [])])
            else:
                ctl.ground([("base", [])])
            
            models, opt = [], None
            models_c = 0
            
            def on_model(m):
                nonlocal opt, models_c
                models_c += 1
                models.append(m.symbols(shown=True))
                if m.cost:
                    opt = tuple(m.cost)
            
            res = ctl.solve(on_model=on_model)
            return res, models, opt, models_c
        
        except ImportError:
            raise RuntimeError(
                "Clingo not available. Install via: pip install clingo"
            )
    
    def _parse_line_model(
        self,
        model_symbols,
        input_data: Goal2Input,
    ) -> Goal2ConcreteLineResult | None:
        """
        Parse a Clingo model into a Goal2ConcreteLineResult.
        
        Expects: select(CardID, SlotNumber) facts from ASP output.
        """
        line_result = Goal2ConcreteLineResult(
            rank=0,
            player_card_ids=[],
            player_ids=[],
            activated_combo_ids=[],
            total_base_ovr=0,
            total_base_salary=0.0,
            total_base_ap=0,
            ovr_bonus=0,
            sal_bonus=0,
            ap_bonus=0,
        )
        
        # Build card -> player mapping
        card_to_player = {p.card_id: p.player_id for p in input_data.players}
        
        # Parse symbols
        selected_cards = {}  # slot -> card_id
        
        for symbol in model_symbols:
            if symbol.name == "select":
                # select(CardID, Slot)
                args = symbol.arguments
                if len(args) >= 2:
                    card_id = args[0].number
                    slot = args[1].number
                    selected_cards[slot] = card_id
            
            elif symbol.name == "combo_active" or symbol.name == "fwd_active_combo" or symbol.name == "def_active_combo":
                # combo_active(ComboID) or fwd_active_combo(ID, Amt, Type)
                args = symbol.arguments
                if len(args) >= 1:
                    combo_id = args[0].number
                    line_result.activated_combo_ids.append(combo_id)
            
            elif symbol.name == "total_base_ovr":
                if len(symbol.arguments) > 0:
                    line_result.total_base_ovr = symbol.arguments[0].number
            
            elif symbol.name == "total_salary":
                if len(symbol.arguments) > 0:
                    line_result.total_base_salary = float(symbol.arguments[0].number)
            
            elif symbol.name == "total_ap":
                if len(symbol.arguments) > 0:
                    line_result.total_base_ap = symbol.arguments[0].number
            
            elif symbol.name == "total_ovr_bonus":
                if len(symbol.arguments) > 0:
                    line_result.ovr_bonus = symbol.arguments[0].number
            
            elif symbol.name == "total_salary_bonus":
                if len(symbol.arguments) > 0:
                    line_result.sal_bonus = symbol.arguments[0].number
            
            elif symbol.name == "total_ap_bonus":
                if len(symbol.arguments) > 0:
                    line_result.ap_bonus = symbol.arguments[0].number
        
        # Build player lists
        num_slots = 3 if input_data.position_type == "forward" else 2
        
        if len(selected_cards) == num_slots:
            for slot in range(1, num_slots + 1):
                if slot in selected_cards:
                    card_id = selected_cards[slot]
                    line_result.player_card_ids.append(card_id)
                    line_result.player_ids.append(card_to_player.get(card_id, -1))
            
            return line_result
        
        return None


# =============================================================================
# FACTORY
# =============================================================================

def get_goal2_solver() -> Goal2Solver:
    """
    Get the Goal 2 solver instance.
    
    Returns:
        ClingoGoal2Solver (Clingo-based concrete line optimizer)
    """
    return ClingoGoal2Solver()
