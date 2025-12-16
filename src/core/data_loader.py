"""
Data loader for NHL 26 Line Combos Optimizer.

This module handles loading data from SQLite database and converting them to domain models.
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
import sqlite3
from pathlib import Path
from functools import lru_cache
from typing import Optional

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
    Loads and caches NHL 26 game data from SQLite database.
    
    The loader uses LRU caching to avoid repeated database queries.
    Data is loaded lazily on first access.
    
    Attributes:
        db_path: Path to the SQLite database file
    
    Expected database schema:
        Tables: skater_names, goalie_names, forwards, defense, goalies,
                forward_combos, defense_combos
        
        Note: Players can have multiple cards (same player_id, different events),
              so the primary key is an auto-increment id, not the player_id.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the data loader.
        
        Args:
            db_path: Path to database file.
        """
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            # Resolve relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / db_path
        
        self._validate_database()
    
    def _validate_database(self) -> None:
        """Validate that the database exists and contains expected tables."""
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}\n"
                f"Please run the migration script: python scripts/csv_to_sqlite.py"
            )
        
        # Check that all required tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        required_tables = {
            "skater_names",
            "goalie_names",
            "forwards",
            "defense",
            "goalies",
            "forward_combos",
            "defense_combos",
        }
        
        missing = required_tables - tables
        conn.close()
        
        if missing:
            raise ValueError(f"Database missing required tables: {missing}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    # =========================================================================
    # NAME LOOKUPS
    # =========================================================================
    
    @lru_cache(maxsize=1)
    def _load_skater_names(self) -> dict[int, tuple[str, str]]:
        """Load skater names (forwards + defense) into a lookup dict."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, first_name, last_name FROM skater_names")
        names = {row["id"]: (row["first_name"], row["last_name"]) for row in cursor.fetchall()}
        
        conn.close()
        return names
    
    @lru_cache(maxsize=1)
    def _load_goalie_names(self) -> dict[int, tuple[str, str]]:
        """Load goalie names into a lookup dict."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, first_name, last_name FROM goalie_names")
        names = {row["id"]: (row["first_name"], row["last_name"]) for row in cursor.fetchall()}
        
        conn.close()
        return names
    
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
        Load all forward players from database.
        
        Returns:
            List of ForwardPlayer objects with names resolved
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT skater_id, event, overall, nationality, league, team
            FROM forwards
            ORDER BY overall DESC, skater_id
        """)
        
        players = []
        for row in cursor.fetchall():
            skater_id = row["skater_id"]
            first_name, last_name = self._get_skater_name(skater_id)
            
            player = ForwardPlayer(
                id=skater_id,
                first_name=first_name,
                last_name=last_name,
                event=str(row["event"]).strip(),
                overall=int(row["overall"]),
                nationality=str(row["nationality"]).strip(),
                league=str(row["league"]).strip(),
                team=str(row["team"]).strip(),
            )
            players.append(player)
        
        conn.close()
        return players
    
    @lru_cache(maxsize=1)
    def get_defense(self) -> list[DefensePlayer]:
        """
        Load all defense players from database.
        
        Returns:
            List of DefensePlayer objects with names resolved
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT skater_id, event, overall, nationality, league, team
            FROM defense
            ORDER BY overall DESC, skater_id
        """)
        
        players = []
        for row in cursor.fetchall():
            skater_id = row["skater_id"]
            first_name, last_name = self._get_skater_name(skater_id)
            
            player = DefensePlayer(
                id=skater_id,
                first_name=first_name,
                last_name=last_name,
                event=str(row["event"]).strip(),
                overall=int(row["overall"]),
                nationality=str(row["nationality"]).strip(),
                league=str(row["league"]).strip(),
                team=str(row["team"]).strip(),
            )
            players.append(player)
        
        conn.close()
        return players
    
    @lru_cache(maxsize=1)
    def get_goalies(self) -> list[Goalie]:
        """
        Load all goalies from database.
        
        Returns:
            List of Goalie objects with names resolved
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT goalie_id, event, overall, nationality, league, team
            FROM goalies
            ORDER BY overall DESC, goalie_id
        """)
        
        players = []
        for row in cursor.fetchall():
            goalie_id = row["goalie_id"]
            first_name, last_name = self._get_goalie_name(goalie_id)
            
            player = Goalie(
                id=goalie_id,
                first_name=first_name,
                last_name=last_name,
                event=str(row["event"]).strip(),
                overall=int(row["overall"]),
                nationality=str(row["nationality"]).strip(),
                league=str(row["league"]).strip(),
                team=str(row["team"]).strip(),
            )
            players.append(player)
        
        conn.close()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, reward_amount, reward_type,
                   type1, key1, type2, key2, type3, key3
            FROM forward_combos
            ORDER BY id
        """)
        
        combos = []
        for row in cursor.fetchall():
            combo = ForwardLineCombo(
                id=row["id"],
                reward_amount=row["reward_amount"],
                reward_type=RewardType(row["reward_type"]),
                condition1=ComboCondition(
                    type=row["type1"].lower(),
                    key=row["key1"].upper(),
                ),
                condition2=ComboCondition(
                    type=row["type2"].lower(),
                    key=row["key2"].upper(),
                ),
                condition3=ComboCondition(
                    type=row["type3"].lower(),
                    key=row["key3"].upper(),
                ),
            )
            combos.append(combo)
        
        conn.close()
        return combos
    
    @lru_cache(maxsize=1)
    def get_defense_combos(self) -> list[DefenseLineCombo]:
        """
        Load defense line combinations (2-player combos).
        
        Returns:
            List of DefenseLineCombo objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, reward_amount, reward_type,
                   type1, key1, type2, key2
            FROM defense_combos
            ORDER BY id
        """)
        
        combos = []
        for row in cursor.fetchall():
            combo = DefenseLineCombo(
                id=row["id"],
                reward_amount=row["reward_amount"],
                reward_type=RewardType(row["reward_type"]),
                condition1=ComboCondition(
                    type=row["type1"].lower(),
                    key=row["key1"].upper(),
                ),
                condition2=ComboCondition(
                    type=row["type2"].lower(),
                    key=row["key2"].upper(),
                ),
            )
            combos.append(combo)
        
        conn.close()
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
        excluded_ids: Optional[list[int]] = None,
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
        excluded_ids = excluded_ids or []
        
        filtered = []
        for player in players:
            if player.overall < min_ovr:
                continue
            if player.id in excluded_ids:
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
        all_team = set()
        all_nationalities = set()
        all_events = set()
        
        for player in forwards + defense + goalies:
            all_team.add(player.team)
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
                "forwards": len(set(p.id for p in forwards)),
                "defense": len(set(p.id for p in defense)),
                "goalies": len(set(p.id for p in goalies)),
            },
            "combos": {
                "forward_combos": len(fwd_combos),
                "defense_combos": len(def_combos),
                "total": len(fwd_combos) + len(def_combos),
            },
            "team": sorted(list(all_team)),
            "nationalities": sorted(list(all_nationalities)),
            "events": sorted(list(all_events)),
            "team_count": len(all_team),
            "nationality_count": len(all_nationalities),
            "event_count": len(all_events),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global loader instance for convenience
# Can be imported directly: from src.core.data_loader import data_loader
_data_loader: Optional[DataLoader] = None


def get_data_loader(db_path: str = "data/nhl26.db") -> DataLoader:
    """
    Get or create the global DataLoader instance.
    
    This provides a singleton-like access pattern while still
    allowing custom database paths when needed.
    
    Usage:
        from src.core.data_loader import get_data_loader
        
        loader = get_data_loader()
        forwards = loader.get_forwards()
    """
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader(db_path)
    return _data_loader
