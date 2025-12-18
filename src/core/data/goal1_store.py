"""
Goal 1 Results Store for NHL 26 Line Combos Optimizer.

Storage layer for Goal 1 pipeline results including runs, Stage A results,
and Stage B concrete lines.

Usage:
    from src.core.data import Goal1ResultsStore
    
    store = Goal1ResultsStore("data/")
    run_id = store.create_run("forward", "ovr")
    store.store_concrete_line(run_id, [101, 205, 317], [1, 5], total_ovr=264)
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..models import (
    Goal1Run,
    Goal1StageAResult,
    Goal1ConcreteLine,
    OptimizationMode,
    PositionType,
)


class Goal1ResultsStore:
    """
    Storage layer for Goal 1 pipeline results.
    
    Handles CRUD operations for:
    - goal1_runs: Pipeline run metadata
    - goal1_stage_a_results: Abstract combo selections
    - goal1_concrete_lines: Concrete player line assignments
    """
    
    def __init__(self, data_dir: str = "data/", db_name: str = "nhl26.db"):
        """Initialize the results store."""
        self.data_dir = Path(data_dir)
        if not self.data_dir.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = project_root / data_dir
        
        self.db_path = self.data_dir / db_name
        
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}\n"
                f"Please run: python scripts/csv_to_sqlite.py"
            )
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # =========================================================================
    # RUN MANAGEMENT
    # =========================================================================
    
    def create_run(
        self,
        position_type: str,
        optimization_mode: str,
        parameters: Optional[dict] = None,
        dataset_hash: Optional[str] = None,
    ) -> int:
        """
        Create a new Goal 1 run record.
        
        Returns:
            The ID of the created run
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO goal1_runs (run_timestamp, position_type, optimization_mode, parameters, dataset_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            position_type,
            optimization_mode,
            json.dumps(parameters or {}),
            dataset_hash,
        ))
        
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return run_id
    
    def get_run(self, run_id: int) -> Optional[Goal1Run]:
        """Get a run by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM goal1_runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Goal1Run(
            id=row["id"],
            run_timestamp=row["run_timestamp"],
            position_type=PositionType(row["position_type"]),
            optimization_mode=OptimizationMode(row["optimization_mode"]),
            parameters=json.loads(row["parameters"]) if row["parameters"] else {},
            dataset_hash=row["dataset_hash"],
        )
    
    def get_latest_run(
        self,
        position_type: Optional[str] = None,
        optimization_mode: Optional[str] = None,
    ) -> Optional[Goal1Run]:
        """Get the most recent run, optionally filtered by type/mode."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM goal1_runs WHERE 1=1"
        params = []
        
        if position_type:
            query += " AND position_type = ?"
            params.append(position_type)
        
        if optimization_mode:
            query += " AND optimization_mode = ?"
            params.append(optimization_mode)
        
        query += " ORDER BY run_timestamp DESC LIMIT 1"
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Goal1Run(
            id=row["id"],
            run_timestamp=row["run_timestamp"],
            position_type=PositionType(row["position_type"]),
            optimization_mode=OptimizationMode(row["optimization_mode"]),
            parameters=json.loads(row["parameters"]) if row["parameters"] else {},
            dataset_hash=row["dataset_hash"],
        )
    
    def list_runs(
        self,
        position_type: Optional[str] = None,
        optimization_mode: Optional[str] = None,
        limit: int = 20,
    ) -> list[Goal1Run]:
        """List runs with optional filters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM goal1_runs WHERE 1=1"
        params = []
        
        if position_type:
            query += " AND position_type = ?"
            params.append(position_type)
        
        if optimization_mode:
            query += " AND optimization_mode = ?"
            params.append(optimization_mode)
        
        query += " ORDER BY run_timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Goal1Run(
                id=row["id"],
                run_timestamp=row["run_timestamp"],
                position_type=PositionType(row["position_type"]),
                optimization_mode=OptimizationMode(row["optimization_mode"]),
                parameters=json.loads(row["parameters"]) if row["parameters"] else {},
                dataset_hash=row["dataset_hash"],
            )
            for row in rows
        ]
    
    def delete_run(self, run_id: int) -> bool:
        """Delete a run and all associated results."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM goal1_runs WHERE id = ?", (run_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute("DELETE FROM goal1_concrete_lines WHERE run_id = ?", (run_id,))
        cursor.execute("DELETE FROM goal1_stage_a_results WHERE run_id = ?", (run_id,))
        cursor.execute("DELETE FROM goal1_runs WHERE id = ?", (run_id,))
        
        conn.commit()
        conn.close()
        return True
    
    # =========================================================================
    # STAGE A RESULTS
    # =========================================================================
    
    def store_stage_a_result(
        self,
        run_id: int,
        solution_rank: int,
        combo_ids: list[int],
        gain_ovr: int = 0,
        gain_sal: int = 0,
        gain_ap: int = 0,
    ) -> int:
        """Store a Stage A (abstract) solution."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO goal1_stage_a_results (run_id, solution_rank, combo_ids, gain_ovr, gain_sal, gain_ap)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            solution_rank,
            json.dumps(combo_ids),
            gain_ovr,
            gain_sal,
            gain_ap,
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_stage_a_results(self, run_id: int) -> list[Goal1StageAResult]:
        """Get all Stage A results for a run, ordered by rank."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM goal1_stage_a_results
            WHERE run_id = ?
            ORDER BY solution_rank
        """, (run_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Goal1StageAResult(
                id=row["id"],
                run_id=row["run_id"],
                solution_rank=row["solution_rank"],
                combo_ids=json.loads(row["combo_ids"]),
                gain_ovr=row["gain_ovr"],
                gain_sal=row["gain_sal"],
                gain_ap=row["gain_ap"],
            )
            for row in rows
        ]
    
    # =========================================================================
    # CONCRETE LINES (STAGE B RESULTS)
    # =========================================================================
    
    def store_concrete_line(
        self,
        run_id: int,
        player_ids: list[int],
        activated_combo_ids: list[int],
        total_ovr: int = 0,
        total_salary: float = 0.0,
        total_ap: int = 0,
        ranking_score: float = 0.0,
        stage_a_solution_id: Optional[int] = None,
        dedupe: bool = True,
    ) -> Optional[int]:
        """
        Store a concrete line from Stage B.
        
        Returns:
            The ID of the stored line, or None if skipped due to deduplication
        """
        line_key = ",".join(str(pid) for pid in sorted(player_ids))
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if dedupe:
            cursor.execute("""
                SELECT id FROM goal1_concrete_lines
                WHERE run_id = ? AND line_key = ?
            """, (run_id, line_key))
            
            if cursor.fetchone():
                conn.close()
                return None
        
        cursor.execute("""
            INSERT INTO goal1_concrete_lines 
            (run_id, stage_a_solution_id, player_ids, activated_combo_ids, 
             total_ovr, total_salary, total_ap, ranking_score, line_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            stage_a_solution_id,
            json.dumps(player_ids),
            json.dumps(activated_combo_ids),
            total_ovr,
            total_salary,
            total_ap,
            ranking_score,
            line_key,
        ))
        
        line_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return line_id
    
    def store_concrete_lines_batch(
        self,
        run_id: int,
        lines: list[Goal1ConcreteLine],
        dedupe: bool = True,
    ) -> int:
        """Store multiple concrete lines in a batch."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stored_count = 0
        existing_keys = set()
        
        if dedupe:
            cursor.execute("""
                SELECT line_key FROM goal1_concrete_lines WHERE run_id = ?
            """, (run_id,))
            existing_keys = {row["line_key"] for row in cursor.fetchall()}
        
        for line in lines:
            line_key = line.line_key()
            
            if dedupe and line_key in existing_keys:
                continue
            
            cursor.execute("""
                INSERT INTO goal1_concrete_lines 
                (run_id, stage_a_solution_id, player_ids, activated_combo_ids, 
                 total_ovr, total_salary, total_ap, ranking_score, line_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                line.stage_a_solution_id,
                json.dumps(line.player_ids),
                json.dumps(line.activated_combo_ids),
                line.total_ovr,
                line.total_salary,
                line.total_ap,
                line.ranking_score,
                line_key,
            ))
            
            existing_keys.add(line_key)
            stored_count += 1
        
        conn.commit()
        conn.close()
        
        return stored_count
    
    def get_concrete_lines(
        self,
        run_id: Optional[int] = None,
        position_type: Optional[str] = None,
        optimization_mode: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "ranking_score DESC",
    ) -> list[Goal1ConcreteLine]:
        """Query concrete lines with flexible filtering."""
        if run_id is None:
            latest_run = self.get_latest_run(position_type, optimization_mode)
            if not latest_run:
                return []
            run_id = latest_run.id
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        allowed_orders = {
            "ranking_score DESC", "ranking_score ASC",
            "total_ovr DESC", "total_ovr ASC",
            "total_salary ASC", "total_salary DESC",
            "id ASC", "id DESC",
        }
        if order_by not in allowed_orders:
            order_by = "ranking_score DESC"
        
        cursor.execute(f"""
            SELECT * FROM goal1_concrete_lines
            WHERE run_id = ?
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """, (run_id, limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Goal1ConcreteLine(
                id=row["id"],
                run_id=row["run_id"],
                stage_a_solution_id=row["stage_a_solution_id"],
                player_ids=json.loads(row["player_ids"]),
                activated_combo_ids=json.loads(row["activated_combo_ids"]),
                total_ovr=row["total_ovr"],
                total_salary=row["total_salary"],
                total_ap=row["total_ap"],
                ranking_score=row["ranking_score"],
            )
            for row in rows
        ]
    
    def count_concrete_lines(self, run_id: int) -> int:
        """Get the count of concrete lines for a run."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM goal1_concrete_lines WHERE run_id = ?
        """, (run_id,))
        
        count = cursor.fetchone()["count"]
        conn.close()
        
        return count
