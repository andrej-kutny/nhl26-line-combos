"""
Data loader for NHL 26 Line Combos Optimizer.

This module handles loading data from CSV files and converting them to domain models.
It serves as the single source of truth for data access across all components.

Usage:
    from src.core import DataLoader
    
    loader = DataLoader("data/")
    forwards = loader.get_forwards()
    combos = loader.get_forward_combos()

Integration Points:
    - API: Uses loader to serve player/combo data via endpoints
    - ASP: Uses loader to generate ASP facts
    - Frontend: Receives data through API (doesn't use loader directly)
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

import pandas as pd

from .models import (
    ForwardPlayer,
    DefensePlayer,
    Goalie,
    ForwardLineCombo,
    DefenseLineCombo,
    ComboCondition,
    RewardType,
    Position,
)


class DataLoader:
    """
    Loads and caches NHL 26 game data from CSV files.
    
    The loader uses LRU caching to avoid repeated file reads.
    Data is loaded lazily on first access.
    
    Attributes:
        data_dir: Path to the data directory containing CSV files
    
    Expected CSV files:
        - fwd_filtered.csv: Forward player cards
        - def_filtered.csv: Defense player cards
        - g_filtered.csv: Goalie player cards
        - skater_id.csv: Skater names (forwards + defense)
        - g_id.csv: Goalie names
        - fwd_line_combos.csv: Forward line combinations (3 players)
        - def_line_combos.csv: Defense line combinations (2 players)
    """
    
    def __init__(self, data_dir: str = "data/"):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Path to directory containing CSV files.
                      Relative paths are resolved from project root.
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.is_absolute():
            # Resolve relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / data_dir
        
        self._validate_data_dir()
    
    def _validate_data_dir(self) -> None:
        """Validate that the data directory exists and contains expected files."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        required_files = [
            "fwd_filtered.csv",
            "def_filtered.csv",
            "g_filtered.csv",
            "skater_id.csv",
            "g_id.csv",
            "fwd_line_combos.csv",
            "def_line_combos.csv",
        ]
        
        missing = [f for f in required_files if not (self.data_dir / f).exists()]
        if missing:
            raise FileNotFoundError(f"Missing required data files: {missing}")

    @lru_cache(maxsize=1)
    def _load_override_attributes(self) -> dict[str, dict]:
        """
        Load optional override attributes (sub_position, salary, ap) from a CSV.
        
        Expected columns:
            id, sub_position, salary, ap
        The file is optional; missing values are ignored.
        """
        override_path = self.data_dir / "player_attributes_override.csv"
        if not override_path.exists():
            return {}
        
        df = pd.read_csv(override_path)
        mapping: dict[str, dict] = {}
        for _, row in df.iterrows():
            pid_raw = row.get("id")
            if pd.isna(pid_raw):
                continue
            pid = str(pid_raw).strip()
            if not pid:
                continue
            entry: dict = {}
            sub_pos = row.get("sub_position")
            if isinstance(sub_pos, str) and sub_pos.strip():
                entry["sub_position"] = sub_pos.strip().upper()
            salary = row.get("salary")
            if pd.notna(salary):
                try:
                    entry["salary"] = int(salary)
                except Exception:
                    pass
            ap = row.get("ap")
            if pd.notna(ap):
                try:
                    entry["ability_points"] = int(ap)
                except Exception:
                    pass
            if entry:
                mapping[pid] = entry
        return mapping

    def _apply_override(self, player) -> None:
        """Apply override attributes to a player instance in-place."""
        override = self._load_override_attributes().get(player.id)
        if not override:
            return
        for key, value in override.items():
            setattr(player, key, value)
    
    # =========================================================================
    # NAME LOOKUPS
    # =========================================================================
    
    @lru_cache(maxsize=1)
    def _load_skater_names(self) -> dict[int, tuple[str, str]]:
        """Load skater names (forwards + defense) into a lookup dict."""
        df = pd.read_csv(self.data_dir / "skater_id.csv")
        return {
            int(row["player_id"]): (row["First name"], row["Second name"])
            for _, row in df.iterrows()
        }
    
    @lru_cache(maxsize=1)
    def _load_goalie_names(self) -> dict[int, tuple[str, str]]:
        """Load goalie names into a lookup dict."""
        df = pd.read_csv(self.data_dir / "g_id.csv")
        return {
            int(row["player_id"]): (row["First name"], row["Second name"])
            for _, row in df.iterrows()
        }
    
    def _get_skater_name(self, skater_id: int) -> tuple[str, str]:
        """Get (first_name, last_name) for a skater ID."""
        names = self._load_skater_names()
        return names.get(skater_id, ("Unknown", "Player"))
    
    def _get_goalie_name(self, goalie_id: int) -> tuple[str, str]:
        """Get (first_name, last_name) for a goalie ID."""
        names = self._load_goalie_names()
        return names.get(goalie_id, ("Unknown", "Goalie"))
    
    # =========================================================================
    # PLAYER LOADING
    # =========================================================================
    
    @lru_cache(maxsize=1)
    def get_forwards(self) -> list[ForwardPlayer]:
        """
        Load all forward players from CSV.
        
        Returns:
            List of ForwardPlayer objects with names resolved
        """
        df = pd.read_csv(self.data_dir / "fwd_filtered.csv")
        players = []
        
        for _, row in df.iterrows():
            player_id = int(row["player_id"])
            first_name, last_name = self._get_skater_name(player_id)
            salary_val = row.get("salary")
            salary = int(salary_val) if pd.notna(salary_val) else None

            player = ForwardPlayer(
                id=str(row["card_id"]).strip(),
                player_id=player_id,
                first_name=first_name,
                last_name=last_name,
                sub_position=str(row.get("position", "")).strip().upper() or None,
                event=str(row["event"]).strip(),
                overall=int(row["overall"]),
                nationality=str(row["nationality"]).strip(),
                league=str(row["league"]).strip(),
                team=str(row["team"]).strip(),
                salary=salary,
                ability_points=None,
            )
            self._apply_override(player)
            players.append(player)
        
        return players
    
    @lru_cache(maxsize=1)
    def get_defense(self) -> list[DefensePlayer]:
        """
        Load all defense players from CSV.
        
        Returns:
            List of DefensePlayer objects with names resolved
        """
        df = pd.read_csv(self.data_dir / "def_filtered.csv")
        players = []
        
        for _, row in df.iterrows():
            player_id = int(row["player_id"])
            first_name, last_name = self._get_skater_name(player_id)
            salary_val = row.get("salary")
            salary = int(salary_val) if pd.notna(salary_val) else None

            player = DefensePlayer(
                id=str(row["card_id"]).strip(),
                player_id=player_id,
                first_name=first_name,
                last_name=last_name,
                sub_position=str(row.get("position", "")).strip().upper() or None,
                event=str(row["event"]).strip(),
                overall=int(row["overall"]),
                nationality=str(row["nationality"]).strip(),
                league=str(row["league"]).strip(),
                team=str(row["team"]).strip(),
                salary=salary,
                ability_points=None,
            )
            self._apply_override(player)
            players.append(player)
        
        return players
    
    @lru_cache(maxsize=1)
    def get_goalies(self) -> list[Goalie]:
        """
        Load all goalies from CSV.
        
        Returns:
            List of Goalie objects with names resolved
        """
        df = pd.read_csv(self.data_dir / "g_filtered.csv")
        players = []
        
        for _, row in df.iterrows():
            player_id = int(row["player_id"])
            first_name, last_name = self._get_goalie_name(player_id)
            salary_val = row.get("salary")
            salary = int(salary_val) if pd.notna(salary_val) else None

            player = Goalie(
                id=str(row["card_id"]).strip(),
                player_id=player_id,
                first_name=first_name,
                last_name=last_name,
                sub_position=None,
                event=str(row["event"]).strip(),
                overall=int(row["overall"]),
                nationality=str(row["nationality"]).strip(),
                league=str(row["league"]).strip(),
                team=str(row["team"]).strip(),
                salary=salary,
                ability_points=None,
            )
            self._apply_override(player)
            players.append(player)
        
        return players
    
    def get_all_players(self) -> dict[str, list]:
        """
        Get all players organized by position.
        
        Returns:
            Dict with keys 'forwards', 'defense', 'goalies'
        """
        return {
            "forwards": self.get_forwards(),
            "defense": self.get_defense(),
            "goalies": self.get_goalies(),
        }
    
    # =========================================================================
    # LINE COMBO LOADING
    # =========================================================================
    
    @lru_cache(maxsize=1)
    def get_forward_combos(self) -> list[ForwardLineCombo]:
        """
        Load forward line combinations (3-player combos).
        
        Returns:
            List of ForwardLineCombo objects
        """
        path = self.data_dir / "fwd_line_combos_v3.csv"
        if not path.exists():
            path = self.data_dir / "fwd_line_combos_v2.csv"
        if not path.exists():
            path = self.data_dir / "fwd_line_combos.csv"
        df = pd.read_csv(path)
        combos = []

        def _clean(val: object) -> str:
            return "" if pd.isna(val) else str(val).strip()
        
        for idx, row in df.iterrows():
            t1, k1 = _clean(row.get("type1")).lower(), _clean(row.get("key1")).upper()
            t2, k2 = _clean(row.get("type2")).lower(), _clean(row.get("key2")).upper()
            t3, k3 = _clean(row.get("type3")).lower(), _clean(row.get("key3")).upper()
            if not (t1 and k1 and t2 and k2 and t3 and k3):
                continue
            combo = ForwardLineCombo(
                id=idx,
                reward_amount=int(row["reward_amount"]),
                reward_type=RewardType(row["reward_type"]),
                condition1=ComboCondition(
                    type=t1,
                    key=k1,
                ),
                condition2=ComboCondition(
                    type=t2,
                    key=k2,
                ),
                condition3=ComboCondition(
                    type=t3,
                    key=k3,
                ),
            )
            combos.append(combo)
        
        return combos
    
    @lru_cache(maxsize=1)
    def get_defense_combos(self) -> list[DefenseLineCombo]:
        """
        Load defense line combinations (2-player combos).
        
        Returns:
            List of DefenseLineCombo objects
        """
        path = self.data_dir / "def_line_combos_v3.csv"
        if not path.exists():
            path = self.data_dir / "def_line_combos_v2.csv"
        if not path.exists():
            path = self.data_dir / "def_line_combos.csv"
        df = pd.read_csv(path)
        combos = []

        def _clean(val: object) -> str:
            return "" if pd.isna(val) else str(val).strip()
        
        for idx, row in df.iterrows():
            t1, k1 = _clean(row.get("type1")).lower(), _clean(row.get("key1")).upper()
            t2, k2 = _clean(row.get("type2")).lower(), _clean(row.get("key2")).upper()
            if not (t1 and k1 and t2 and k2):
                continue
            combo = DefenseLineCombo(
                id=idx,
                reward_amount=int(row["reward_amount"]),
                reward_type=RewardType(row["reward_type"]),
                condition1=ComboCondition(
                    type=t1,
                    key=k1,
                ),
                condition2=ComboCondition(
                    type=t2,
                    key=k2,
                ),
            )
            combos.append(combo)
        
        return combos
    
    def get_all_combos(self) -> dict[str, list]:
        """
        Get all line combinations.
        
        Returns:
            Dict with keys 'forward_combos', 'defense_combos'
        """
        return {
            "forward_combos": self.get_forward_combos(),
            "defense_combos": self.get_defense_combos(),
        }
    
    # =========================================================================
    # FILTERING UTILITIES
    # =========================================================================
    
    def filter_players(
        self,
        players: list,
        min_ovr: int = 0,
        team: Optional[str] = None,
        nationality: Optional[str] = None,
        event: Optional[str] = None,
        excluded_ids: Optional[list[str]] = None,
    ) -> list:
        """
        Filter a list of players by various criteria.
        
        This is useful for pre-filtering before ASP optimization
        to reduce the search space.
        
        Args:
            players: List of player objects to filter
            min_ovr: Minimum overall rating
            team: Filter by team abbreviation
            nationality: Filter by nationality
            event: Filter by event type
            excluded_ids: List of player IDs to exclude
            
        Returns:
            Filtered list of players
        """
        excluded_ids = set(str(e) for e in (excluded_ids or []))
        
        filtered = []
        for player in players:
            if player.overall < min_ovr:
                continue
            if str(player.id) in excluded_ids:
                continue
            if team and player.team.upper() != team.upper():
                continue
            if nationality and player.nationality.upper() != nationality.upper():
                continue
            if event and player.event.upper() != event.upper():
                continue
            filtered.append(player)
        
        return filtered
    
    def get_players_matching_combo_condition(
        self,
        players: list,
        condition: ComboCondition,
    ) -> list:
        """
        Get all players that match a specific combo condition.
        
        Useful for the ASP team to determine which players can
        satisfy which conditions in line combinations.
        
        Args:
            players: List of players to check
            condition: The condition to match against
            
        Returns:
            List of players matching the condition
        """
        return [
            p for p in players
            if p.matches_condition(condition.type, condition.key)
        ]
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> dict:
        """
        Get dataset statistics.
        
        Returns:
            Dictionary with counts and other statistics
        """
        forwards = self.get_forwards()
        defense = self.get_defense()
        goalies = self.get_goalies()
        fwd_combos = self.get_forward_combos()
        def_combos = self.get_defense_combos()
        
        # Get unique values
        all_teams = set()
        all_nationalities = set()
        all_events = set()
        
        for player in forwards + defense + goalies:
            all_teams.add(player.team)
            all_nationalities.add(player.nationality)
            all_events.add(player.event)
        
        return {
            "players": {
                "forwards": len(forwards),
                "defense": len(defense),
                "goalies": len(goalies),
                "total": len(forwards) + len(defense) + len(goalies),
            },
            "unique_players": {
                "forwards": len(set(p.player_id or p.id for p in forwards)),
                "defense": len(set(p.player_id or p.id for p in defense)),
                "goalies": len(set(p.player_id or p.id for p in goalies)),
            },
            "combos": {
                "forward_combos": len(fwd_combos),
                "defense_combos": len(def_combos),
                "total": len(fwd_combos) + len(def_combos),
            },
            "teams": sorted(list(all_teams)),
            "nationalities": sorted(list(all_nationalities)),
            "events": sorted(list(all_events)),
            "team_count": len(all_teams),
            "nationality_count": len(all_nationalities),
            "event_count": len(all_events),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global loader instance for convenience
# Can be imported directly: from src.core.data_loader import data_loader
_data_loader: Optional[DataLoader] = None


def get_data_loader(data_dir: str = "data/") -> DataLoader:
    """
    Get or create the global DataLoader instance.
    
    This provides a singleton-like access pattern while still
    allowing custom data directories when needed.
    
    Usage:
        from src.core.data_loader import get_data_loader
        
        loader = get_data_loader()
        forwards = loader.get_forwards()
    """
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader(data_dir)
    return _data_loader
