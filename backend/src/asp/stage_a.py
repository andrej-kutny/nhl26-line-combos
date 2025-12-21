"""
Stage A: Abstract Optimization (Combo-First).

This module handles:
1. Generating ASP facts from combo templates
2. Running the Stage A solver (mock implementation provided)

Stage A optimizes over line combination templates without considering
specific players. It returns the top-K abstract solutions.
"""

import time
from typing import Literal
import clingo
from pathlib import Path

from ..core.data import get_data_loader
from ..core.models import ForwardLineCombo, DefenseLineCombo, RewardType
from .interfaces import (
    StageAInput,
    StageAOutput,
    StageASolution,
    StageASolver,
    ActiveComboInfo,
    PlayerAttribute,
)


# =============================================================================
# INPUT GENERATOR
# =============================================================================

class StageAInputGenerator:
    """
    Generates Stage A input from database combo templates.
    
    Converts combo data into ASP facts for the solver.
    """
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def generate(
        self,
        position_type: Literal["forward", "defense"],
        optimization_mode: Literal["ovr", "sal", "ap", "ovr_sal", "ovr_sal_ap"],
        top_k: int = 200,
    ) -> StageAInput:
        """
        Generate Stage A input for the given position and mode.
        
        Args:
            position_type: "forward" or "defense"
            optimization_mode: Which metrics to optimize
            top_k: Number of solutions to find
            
        Returns:
            StageAInput with combo facts ready for ASP
        """
        # Get combos from database
        if position_type == "forward":
            combos = self.loader.get_forward_combos()
            combo_facts = self._generate_forward_facts(combos, optimization_mode)
        else:
            combos = self.loader.get_defense_combos()
            combo_facts = self._generate_defense_facts(combos, optimization_mode)
        
        # Set weights based on position and mode
        ovr_weight, sal_weight, ap_weight = self._get_weights(position_type, optimization_mode)
        
        return StageAInput(
            position_type=position_type,
            optimization_mode=optimization_mode,
            combo_facts=combo_facts,
            top_k=top_k,
            ovr_weight=ovr_weight,
            sal_weight=sal_weight,
            ap_weight=ap_weight,
        )
    
    def _generate_forward_facts(
        self,
        combos: list[ForwardLineCombo],
        mode: str,
    ) -> list[str]:
        """
        Generate ASP facts for forward combos.
        
        Format matches ASP team's expected input:
        forward_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2, entry3).
        
        Where entries are: team("X"), nationality("Y"), event("Z")
        """
        facts = []
        
        for combo in combos:
            # Filter by mode if needed
            if not self._combo_matches_mode(combo.reward_type, mode):
                continue
            
            c1 = combo.condition1
            c2 = combo.condition2
            c3 = combo.condition3
            
            # Format: forward_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2, entry3).
            # Entries use functor notation: team("OTT"), nationality("USA"), event("HH")
            fact = (
                f'forward_combo({combo.id}, {combo.reward_amount}, "{combo.reward_type.value}", '
                f'{c1.type}("{c1.key}"), '
                f'{c2.type}("{c2.key}"), '
                f'{c3.type}("{c3.key}")).'
            )
            facts.append(fact)
        
        return facts
    
    def _generate_defense_facts(
        self,
        combos: list[DefenseLineCombo],
        mode: str,
    ) -> list[str]:
        """
        Generate ASP facts for defense combos.
        
        Format matches ASP team's expected input:
        defense_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2).
        
        Where entries are: team("X"), nationality("Y"), event("Z")
        """
        facts = []
        
        for combo in combos:
            if not self._combo_matches_mode(combo.reward_type, mode):
                continue
            
            c1 = combo.condition1
            c2 = combo.condition2
            
            # Format: defense_combo(id, reward_amount, "REWARD_TYPE", entry1, entry2).
            fact = (
                f'defense_combo({combo.id}, {combo.reward_amount}, "{combo.reward_type.value}", '
                f'{c1.type}("{c1.key}"), '
                f'{c2.type}("{c2.key}")).'
            )
            facts.append(fact)
        
        return facts
    
    def _combo_matches_mode(self, reward_type: RewardType, mode: str) -> bool:
        """Check if combo's reward type is relevant for the optimization mode."""
        if mode == "ovr":
            return reward_type == RewardType.OVR
        elif mode == "sal":
            return reward_type == RewardType.SAL
        elif mode == "ap":
            return reward_type == RewardType.AP
        else:
            # Combined modes include all types
            return True
    
    def _get_weights(
        self,
        position_type: str,
        mode: str,
    ) -> tuple[float, float, float]:
        """Get optimization weights based on position and mode."""
        # Default weights from GOAL_1.md
        if position_type == "forward":
            base_ovr, base_sal = 3.0, 1.0
        else:
            base_ovr, base_sal = 2.0, 1.0
        
        base_ap = 1.0
        
        # Adjust based on mode
        if mode == "ovr":
            return (1.0, 0.0, 0.0)
        elif mode == "sal":
            return (0.0, 1.0, 0.0)
        elif mode == "ap":
            return (0.0, 0.0, 1.0)
        elif mode == "ovr_sal":
            return (base_ovr, base_sal, 0.0)
        else:  # ovr_sal_ap
            return (base_ovr, base_sal, base_ap)


class ClingoStageASolver(StageASolver):
    """
    Mock Stage A solver for development/testing.
    
    Returns synthetic solutions based on actual combo data.
    ASP team will replace this with real Clingo implementation.
    """

    def _Clingo_solve(self, files, extra_rules="", consts=None, ctl_opts=None):
        opts = list(ctl_opts or [])
        if consts:
            for k, v in consts.items():
                opts.append(f"-c {k}={v}")
        
        ctl = clingo.Control(opts)
        for f in files:
            ctl.load(f)
        
        if extra_rules.strip():
            ctl.add("extra", [], extra_rules)
            ctl.ground([("base", []), ("extra", [])])
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

    
    def __init__(self):
        self.loader = get_data_loader()
    
    def solve(self, input_data: StageAInput) -> StageAOutput:
        """
        Run Stage A optimization using Clingo.
        """
        start_time = time.time()
        
        # Determine rules based on position
        current_dir = Path(__file__).parent
        base_path = current_dir / "g1a_abstraction"
        
        rules = [
            str(base_path / "target_threshold_lookup.lp"),
            str(base_path / "rules.lp")
        ]
        
        if input_data.position_type == "forward":
            rules.append(str(base_path / "fwd_rules.lp"))
        else:
            rules.append(str(base_path / "def_rules.lp"))
            
        # Use generated facts from input
        extra_rules = "\n".join(input_data.combo_facts)
        
        # Weights
        consts = {
            "w_ovr": int(input_data.ovr_weight),
            "w_sal": int(input_data.sal_weight),
            "w_ap": int(input_data.ap_weight)
        }
        
        # Solve
        res, models, opt, models_c = self._Clingo_solve(rules, extra_rules, consts=consts, ctl_opts=["0"])
        
        solutions: list[StageASolution] = []
        
        for model_symbols in models:
            sol = StageASolution(rank=0, combo_ids=[]) # rank updated later
            
            for symbol in model_symbols:
                if symbol.name == "fwd_active_combo" or symbol.name == "def_active_combo":
                    # fwd_active_combo(ID, Reward, Type)
                    args = symbol.arguments
                    if len(args) >= 3:
                        c_id = args[0].number
                        reward = args[1].number
                        # Handle string/symbol for type
                        r_type_sym = args[2]
                        r_type = r_type_sym.string if r_type_sym.type == clingo.SymbolType.String else str(r_type_sym)
                        # Remove quotes if present (clingo string conversion might keep them)
                        r_type = r_type.replace('"', '')
                        
                        sol.active_combos.append(ActiveComboInfo(
                            combo_id=c_id,
                            reward_amount=reward,
                            reward_type=r_type
                        ))
                        sol.combo_ids.append(c_id)
                        
                        if r_type == "OVR":
                            sol.gain_ovr += reward
                        elif r_type == "SAL":
                            sol.gain_sal += reward
                        elif r_type == "AP":
                            sol.gain_ap += reward
                        
                elif symbol.name == "player_attr":
                    # player_attr(Slot, attr(Val))
                    args = symbol.arguments
                    if len(args) >= 2:
                        slot = args[0].number
                        attr_fun = args[1]
                        attr_type = attr_fun.name
                        # Value might be string or function/constant
                        if len(attr_fun.arguments) > 0:
                            attr_val_sym = attr_fun.arguments[0]
                            attr_val = attr_val_sym.string if attr_val_sym.type == clingo.SymbolType.String else str(attr_val_sym)
                            attr_val = attr_val.replace('"', '')
                            
                            sol.player_attrs.append(PlayerAttribute(
                                slot=slot,
                                attr_type=attr_type,
                                attr_value=attr_val
                            ))
                    
                elif symbol.name == "total_reward":
                    if len(symbol.arguments) > 0:
                        sol.total_reward = symbol.arguments[0].number

            solutions.append(sol)
            
        # Sort by total gain (highest first)
        solutions.sort(key=lambda x: x.total_gain, reverse=True)
        
        # Take top K
        solutions = solutions[:input_data.top_k]
        
        # Assign ranks
        for i, sol in enumerate(solutions):
            sol.rank = i + 1
        
        solve_time = (time.time() - start_time) * 1000
        
        return StageAOutput(
            solutions=solutions,
            solve_time_ms=solve_time,
            total_models_found=len(models)
        )
    
    def _combo_matches_mode(self, reward_type: RewardType, mode: str) -> bool:
        """Check if combo's reward type is relevant for the optimization mode."""
        if mode == "ovr":
            return reward_type == RewardType.OVR
        elif mode == "sal":
            return reward_type == RewardType.SAL
        elif mode == "ap":
            return reward_type == RewardType.AP
        return True


# =============================================================================
# FACTORY
# =============================================================================

def get_stage_a_solver() -> StageASolver:
    """
    Get the Stage A solver instance.
    
    Returns MockStageASolver until ASP team provides real implementation.
    
    TODO: Replace with real Clingo solver when available:
        from .clingo_solver import ClingoStageASolver
        return ClingoStageASolver()
    """
    return ClingoStageASolver()
