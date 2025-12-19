"""
Data loader for NHL 26 Line Combos Optimizer.

This module handles loading data from SQLite database and converting them to domain models.
It serves as the single source of truth for player and combo data access.

Usage:
    from src.core.data import DataLoader
    
    loader = DataLoader("data/")
    forwards = loader.get_forwards(min_ovr=85, team="TOR")
"""

import sqlite3
from pathlib import Path
from functools import lru_cache
from typing import Optional

from ..models import (
    ForwardPlayer,
    DefensePlayer,
    Goalie,
    ForwardLineCombo,
    DefenseLineCombo,
    ComboCondition,
    RewardType,
)


class DataLoader:
    """
    Loads NHL 26 game data from SQLite database using efficient SQL queries.
    
    This loader leverages SQLite's indexing and WHERE clauses for filtering,
    rather than loading everything into memory. Only small lookup tables
    (player names) are cached.
    
    Attributes:
        data_dir: Path to the data directory containing the database
        db_path: Path to the SQLite database file
    
    Expected database schema:
        Tables: skater_names, goalie_names, forwards, defense, goalies,
                forward_combos, defense_combos
    """
    
    def __init__(self, data_dir: str = "data/", db_name: str = "nhl26.db"):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Path to directory containing database file.
            db_name: Name of the SQLite database file.
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = project_root / data_dir
        
        self.db_path = self.data_dir / db_name
        self._validate_database()
    
    def _validate_database(self) -> None:
        """Validate that the database exists and contains expected tables."""
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}\n"
                f"Please run the migration script: python scripts/csv_to_sqlite.py"
            )
        
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
        conn.row_factory = sqlite3.Row
        return conn
    
    # =========================================================================
    # NAME LOOKUPS (Cached)
    # =========================================================================
    
    @lru_cache(maxsize=1)
    def _load_skater_names(self) -> dict[int, tuple[str, str]]:
        """Load skater names into a lookup dict."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM skater_names")
        names = {row["player_id"]: (row["first_name"], row["last_name"]) for row in cursor.fetchall()}
        
        conn.close()
        return names
    
    @lru_cache(maxsize=1)
    def _load_goalie_names(self) -> dict[int, tuple[str, str]]:
        """Load goalie names into a lookup dict."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM goalie_names")
        names = {row["player_id"]: (row["first_name"], row["last_name"]) for row in cursor.fetchall()}
        
        conn.close()
        return names
    
    def _get_skater_name(self, player_id: int) -> tuple[str, str]:
        """Get (first_name, last_name) for a player ID."""
        names = self._load_skater_names()
        return names.get(player_id, ("Unknown", "Player"))
    
    def _get_goalie_name(self, player_id: int) -> tuple[str, str]:
        """Get (first_name, last_name) for a goalie ID."""
        names = self._load_goalie_names()
        return names.get(player_id, ("Unknown", "Goalie"))
    
    # =========================================================================
    # PLAYER LOADING
    # =========================================================================
    
    def get_forwards(
        self,
        min_ovr: int = 0,
        max_ovr: int = 99,
        team: Optional[str] = None,
        nationality: Optional[str] = None,
        event: Optional[str] = None,
        position: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[ForwardPlayer]:
        """Load forward players from database with optional SQL filters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        where_clauses = ["overall >= ?", "overall <= ?"]
        params = [min_ovr, max_ovr]
        
        if team:
            where_clauses.append("team = ?")
            params.append(team.upper())
        
        if nationality:
            where_clauses.append("nationality = ?")
            params.append(nationality.upper())
        
        if event:
            where_clauses.append("event = ?")
            params.append(event.upper())
        
        if position:
            where_clauses.append("position = ?")
            params.append(position.upper())
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
            SELECT *
            FROM forwards
            WHERE {where_sql}
            ORDER BY overall DESC, player_id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        
        cursor.execute(query, params)
        
        players = []
        for row in cursor.fetchall():
            player_id = row["player_id"]
            first_name, last_name = self._get_skater_name(player_id)
            
            player = ForwardPlayer(
                id=row["id"],
                player_id=player_id,
                first_name=first_name,
                last_name=last_name,
                img=row["img"],
                position=row["position"],
                nationality=row["nationality"],
                event=row["event"],
                league=row["league"],
                team=row["team"],
                weight=row["weight"],
                height=row["height"],
                salary=row["salary"],
                overall=row["overall"],
                deking=row["deking"],
                hand_eye=row["hand_eye"],
                passing=row["passing"],
                puck_control=row["puck_control"],
                slap_shot_accuracy=row["slap_shot_accuracy"],
                slap_shot_power=row["slap_shot_power"],
                wrist_shot_accuracy=row["wrist_shot_accuracy"],
                wrist_shot_power=row["wrist_shot_power"],
                acceleration=row["acceleration"],
                agility=row["agility"],
                balance=row["balance"],
                endurance=row["endurance"],
                speed=row["speed"],
                discipline=row["discipline"],
                off_awareness=row["off_awareness"],
                def_awareness=row["def_awareness"],
                faceoffs=row["faceoffs"],
                shot_blocking=row["shot_blocking"],
                stick_checking=row["stick_checking"],
                aggression=row["aggression"],
                body_checking=row["body_checking"],
                durability=row["durability"],
                fighting_skill=row["fighting_skill"],
                strength=row["strength"],
            )
            players.append(player)
        
        conn.close()
        return players
    
    def get_defense(
        self,
        min_ovr: int = 0,
        max_ovr: int = 99,
        team: Optional[str] = None,
        nationality: Optional[str] = None,
        event: Optional[str] = None,
        position: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[DefensePlayer]:
        """Load defense players from database with optional SQL filters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        where_clauses = ["overall >= ?", "overall <= ?"]
        params = [min_ovr, max_ovr]
        
        if team:
            where_clauses.append("team = ?")
            params.append(team.upper())
        
        if nationality:
            where_clauses.append("nationality = ?")
            params.append(nationality.upper())
        
        if event:
            where_clauses.append("event = ?")
            params.append(event.upper())
        
        if position:
            where_clauses.append("position = ?")
            params.append(position.upper())
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
            SELECT *
            FROM defense
            WHERE {where_sql}
            ORDER BY overall DESC, player_id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        
        cursor.execute(query, params)
        
        players = []
        for row in cursor.fetchall():
            player_id = row["player_id"]
            first_name, last_name = self._get_skater_name(player_id)
            
            player = DefensePlayer(
                id=row["id"],
                player_id=player_id,
                first_name=first_name,
                last_name=last_name,
                img=row["img"],
                position=row["position"],
                nationality=row["nationality"],
                event=row["event"],
                league=row["league"],
                team=row["team"],
                weight=row["weight"],
                height=row["height"],
                salary=row["salary"],
                overall=row["overall"],
                deking=row["deking"],
                hand_eye=row["hand_eye"],
                passing=row["passing"],
                puck_control=row["puck_control"],
                slap_shot_accuracy=row["slap_shot_accuracy"],
                slap_shot_power=row["slap_shot_power"],
                wrist_shot_accuracy=row["wrist_shot_accuracy"],
                wrist_shot_power=row["wrist_shot_power"],
                acceleration=row["acceleration"],
                agility=row["agility"],
                balance=row["balance"],
                endurance=row["endurance"],
                speed=row["speed"],
                discipline=row["discipline"],
                off_awareness=row["off_awareness"],
                def_awareness=row["def_awareness"],
                faceoffs=row["faceoffs"],
                shot_blocking=row["shot_blocking"],
                stick_checking=row["stick_checking"],
                aggression=row["aggression"],
                body_checking=row["body_checking"],
                durability=row["durability"],
                fighting_skill=row["fighting_skill"],
                strength=row["strength"],
            )
            players.append(player)
        
        conn.close()
        return players
    
    def get_goalies(
        self,
        min_ovr: int = 0,
        max_ovr: int = 99,
        team: Optional[str] = None,
        nationality: Optional[str] = None,
        event: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[Goalie]:
        """Load goalies from database with optional SQL filters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        where_clauses = ["overall >= ?", "overall <= ?"]
        params = [min_ovr, max_ovr]
        
        if team:
            where_clauses.append("team = ?")
            params.append(team.upper())
        
        if nationality:
            where_clauses.append("nationality = ?")
            params.append(nationality.upper())
        
        if event:
            where_clauses.append("event = ?")
            params.append(event.upper())
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
            SELECT *
            FROM goalies
            WHERE {where_sql}
            ORDER BY overall DESC, player_id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        
        cursor.execute(query, params)
        
        players = []
        for row in cursor.fetchall():
            player_id = row["player_id"]
            first_name, last_name = self._get_goalie_name(player_id)
            
            player = Goalie(
                id=row["id"],
                player_id=player_id,
                first_name=first_name,
                last_name=last_name,
                img=row["img"],
                position="G",
                nationality=row["nationality"],
                event=row["event"],
                league=row["league"],
                team=row["team"],
                weight=row["weight"],
                height=row["height"],
                salary=row["salary"],
                overall=row["overall"],
                passing=row["passing"],
                agility=row["agility"],
                speed=row["speed"],
                aggression=row["aggression"],
                glove_high=row["glove_high"],
                glove_low=row["glove_low"],
                five_hole=row["five_hole"],
                stick_high=row["stick_high"],
                stick_low=row["stick_low"],
                shot_recovery=row["shot_recovery"],
                positioning=row["positioning"],
                breakaway=row["breakaway"],
                vision=row["vision"],
                poke_check=row["poke_check"],
                rebound_control=row["rebound_control"],
            )
            players.append(player)
        
        conn.close()
        return players
    
    def get_all_players(self) -> dict[str, list]:
        """Get all players organized by position."""
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
        """Load forward line combinations (3-player combos)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM forward_combos ORDER BY id")
        
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
        """Load defense line combinations (2-player combos)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM defense_combos ORDER BY id")
        
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
        """Get all line combinations."""
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
        
        **DEPRECATED**: Use the filter parameters in get_forwards(), etc. instead.
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
        """Get all players that match a specific combo condition."""
        return [
            p for p in players
            if p.matches_condition(condition.type, condition.key)
        ]
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> dict:
        """Get dataset statistics using efficient SQL aggregation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM forwards")
        forward_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM defense")
        defense_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM goalies")
        goalie_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(DISTINCT player_id) as count FROM forwards")
        unique_forwards = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(DISTINCT player_id) as count FROM defense")
        unique_defense = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(DISTINCT player_id) as count FROM goalies")
        unique_goalies = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM forward_combos")
        fwd_combo_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM defense_combos")
        def_combo_count = cursor.fetchone()["count"]
        
        cursor.execute("""
            SELECT DISTINCT team FROM (
                SELECT team FROM forwards
                UNION SELECT team FROM defense
                UNION SELECT team FROM goalies
            ) ORDER BY team
        """)
        teams = [row["team"] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT DISTINCT nationality FROM (
                SELECT nationality FROM forwards
                UNION SELECT nationality FROM defense
                UNION SELECT nationality FROM goalies
            ) ORDER BY nationality
        """)
        nationalities = [row["nationality"] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT DISTINCT event FROM (
                SELECT event FROM forwards
                UNION SELECT event FROM defense
                UNION SELECT event FROM goalies
            ) ORDER BY event
        """)
        events = [row["event"] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "players": {
                "forwards": forward_count,
                "defense": defense_count,
                "goalies": goalie_count,
                "total": forward_count + defense_count + goalie_count,
            },
            "unique_players": {
                "forwards": unique_forwards,
                "defense": unique_defense,
                "goalies": unique_goalies,
            },
            "combos": {
                "forward_combos": fwd_combo_count,
                "defense_combos": def_combo_count,
                "total": fwd_combo_count + def_combo_count,
            },
            "teams": teams,
            "nationalities": nationalities,
            "events": events,
            "team_count": len(teams),
            "nationality_count": len(nationalities),
            "event_count": len(events),
        }
