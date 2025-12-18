"""
Tests for Goal 1 storage layer.

These tests verify the storage and retrieval of Goal 1 pipeline results:
- Run metadata (goal1_runs)
- Stage A abstract results (goal1_stage_a_results)
- Stage B concrete lines (goal1_concrete_lines)

Run with: pytest tests/test_goal1_storage.py -v
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path

from src.core.data import Goal1ResultsStore
from src.core.models import (
    Goal1ConcreteLine,
    OptimizationMode,
    PositionType,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database with Goal 1 tables for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_nhl26.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create Goal 1 tables (same schema as csv_to_sqlite.py)
        cursor.execute("""
            CREATE TABLE goal1_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp TEXT NOT NULL,
                position_type TEXT NOT NULL CHECK(position_type IN ('forward', 'defense')),
                optimization_mode TEXT NOT NULL CHECK(optimization_mode IN ('ovr', 'sal', 'ap', 'ovr_sal', 'ovr_sal_ap')),
                parameters TEXT DEFAULT '{}',
                dataset_hash TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE goal1_stage_a_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES goal1_runs(id) ON DELETE CASCADE,
                solution_rank INTEGER NOT NULL,
                combo_ids TEXT NOT NULL,
                gain_ovr INTEGER DEFAULT 0,
                gain_sal INTEGER DEFAULT 0,
                gain_ap INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE goal1_concrete_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES goal1_runs(id) ON DELETE CASCADE,
                stage_a_solution_id INTEGER REFERENCES goal1_stage_a_results(id) ON DELETE SET NULL,
                player_ids TEXT NOT NULL,
                activated_combo_ids TEXT NOT NULL,
                total_ovr INTEGER DEFAULT 0,
                total_salary REAL DEFAULT 0.0,
                total_ap INTEGER DEFAULT 0,
                ranking_score REAL DEFAULT 0.0,
                line_key TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_goal1_runs_position_mode ON goal1_runs(position_type, optimization_mode)")
        cursor.execute("CREATE INDEX idx_goal1_runs_timestamp ON goal1_runs(run_timestamp)")
        cursor.execute("CREATE INDEX idx_stage_a_run_id ON goal1_stage_a_results(run_id)")
        cursor.execute("CREATE INDEX idx_concrete_lines_run_id ON goal1_concrete_lines(run_id)")
        cursor.execute("CREATE INDEX idx_concrete_lines_key ON goal1_concrete_lines(run_id, line_key)")
        cursor.execute("CREATE INDEX idx_concrete_lines_score ON goal1_concrete_lines(run_id, ranking_score DESC)")
        
        conn.commit()
        conn.close()
        
        yield tmpdir, db_path


@pytest.fixture
def store(temp_db):
    """Create a Goal1ResultsStore instance with the temp database."""
    tmpdir, db_path = temp_db
    return Goal1ResultsStore(data_dir=tmpdir, db_name="test_nhl26.db")


# =============================================================================
# RUN MANAGEMENT TESTS
# =============================================================================

class TestRunManagement:
    """Tests for Goal 1 run CRUD operations."""
    
    def test_create_run(self, store):
        """Can create a Goal 1 run record and get back an ID."""
        run_id = store.create_run(
            position_type="forward",
            optimization_mode="ovr",
        )
        
        assert run_id is not None
        assert isinstance(run_id, int)
        assert run_id > 0
    
    def test_create_run_with_parameters(self, store):
        """Can create a run with custom parameters."""
        params = {"k": 200, "limit": 100, "ovr_weight": 3}
        
        run_id = store.create_run(
            position_type="defense",
            optimization_mode="ovr_sal",
            parameters=params,
            dataset_hash="abc123",
        )
        
        run = store.get_run(run_id)
        
        assert run is not None
        assert run.parameters == params
        assert run.dataset_hash == "abc123"
    
    def test_get_run(self, store):
        """Can retrieve a run by ID."""
        run_id = store.create_run(
            position_type="forward",
            optimization_mode="sal",
        )
        
        run = store.get_run(run_id)
        
        assert run is not None
        assert run.id == run_id
        assert run.position_type == PositionType.FORWARD
        assert run.optimization_mode == OptimizationMode.SAL
        assert run.run_timestamp is not None
    
    def test_get_run_not_found(self, store):
        """Returns None for non-existent run ID."""
        run = store.get_run(99999)
        assert run is None
    
    def test_get_latest_run(self, store):
        """Can get the most recent run."""
        # Create multiple runs
        store.create_run("forward", "ovr")
        store.create_run("forward", "sal")
        run_id_3 = store.create_run("forward", "ap")
        
        latest = store.get_latest_run()
        
        assert latest is not None
        assert latest.id == run_id_3
    
    def test_get_latest_run_filtered(self, store):
        """Can get latest run filtered by type/mode."""
        store.create_run("forward", "ovr")
        run_id_def = store.create_run("defense", "ovr")
        store.create_run("forward", "sal")
        
        latest_def = store.get_latest_run(position_type="defense")
        
        assert latest_def is not None
        assert latest_def.id == run_id_def
        assert latest_def.position_type == PositionType.DEFENSE
    
    def test_list_runs(self, store):
        """Can list runs with pagination."""
        # Create 5 runs
        for i in range(5):
            store.create_run("forward", "ovr")
        
        # List with limit
        runs = store.list_runs(limit=3)
        
        assert len(runs) == 3
        # Should be ordered by timestamp DESC (newest first)
        assert runs[0].id > runs[1].id > runs[2].id
    
    def test_delete_run(self, store):
        """Can delete a run and its associated results."""
        run_id = store.create_run("forward", "ovr")
        
        # Add some results
        store.store_stage_a_result(run_id, 1, [1, 2, 3], gain_ovr=5)
        store.store_concrete_line(run_id, [101, 102, 103], [1, 2], total_ovr=250)
        
        # Delete
        result = store.delete_run(run_id)
        
        assert result is True
        assert store.get_run(run_id) is None
        assert store.get_stage_a_results(run_id) == []
        assert store.get_concrete_lines(run_id=run_id) == []
    
    def test_delete_run_not_found(self, store):
        """Returns False when deleting non-existent run."""
        result = store.delete_run(99999)
        assert result is False


# =============================================================================
# STAGE A RESULTS TESTS
# =============================================================================

class TestStageAResults:
    """Tests for Stage A (abstract combo selection) storage."""
    
    def test_store_stage_a_result(self, store):
        """Can store a Stage A result."""
        run_id = store.create_run("forward", "ovr")
        
        result_id = store.store_stage_a_result(
            run_id=run_id,
            solution_rank=1,
            combo_ids=[1, 5, 12],
            gain_ovr=6,
            gain_sal=0,
            gain_ap=0,
        )
        
        assert result_id is not None
        assert result_id > 0
    
    def test_get_stage_a_results(self, store):
        """Can retrieve Stage A results for a run."""
        run_id = store.create_run("forward", "ovr")
        
        # Store multiple solutions
        store.store_stage_a_result(run_id, 1, [1, 5, 12], gain_ovr=6)
        store.store_stage_a_result(run_id, 2, [3, 8], gain_ovr=4, gain_sal=2)
        store.store_stage_a_result(run_id, 3, [2, 7, 9], gain_ovr=3)
        
        results = store.get_stage_a_results(run_id)
        
        assert len(results) == 3
        # Should be ordered by rank
        assert results[0].solution_rank == 1
        assert results[1].solution_rank == 2
        assert results[2].solution_rank == 3
        
        # Check data integrity
        assert results[0].combo_ids == [1, 5, 12]
        assert results[0].gain_ovr == 6
        assert results[1].gain_sal == 2


# =============================================================================
# CONCRETE LINES (STAGE B) TESTS
# =============================================================================

class TestConcreteLines:
    """Tests for Stage B (concrete line) storage."""
    
    def test_store_concrete_line(self, store):
        """Can store a concrete line."""
        run_id = store.create_run("forward", "ovr")
        
        line_id = store.store_concrete_line(
            run_id=run_id,
            player_ids=[101, 205, 317],
            activated_combo_ids=[1, 5, 12],
            total_ovr=264,
            total_salary=15000000.0,
            total_ap=6,
            ranking_score=270.5,
        )
        
        assert line_id is not None
        assert line_id > 0
    
    def test_get_concrete_lines(self, store):
        """Can retrieve concrete lines for a run."""
        run_id = store.create_run("forward", "ovr")
        
        store.store_concrete_line(run_id, [101, 205, 317], [1, 5], total_ovr=264, ranking_score=270.0)
        store.store_concrete_line(run_id, [102, 206, 318], [1, 12], total_ovr=261, ranking_score=265.0)
        
        lines = store.get_concrete_lines(run_id=run_id)
        
        assert len(lines) == 2
        # Default order is ranking_score DESC
        assert lines[0].ranking_score >= lines[1].ranking_score
    
    def test_deduplication(self, store):
        """Storing the same line twice doesn't create duplicates."""
        run_id = store.create_run("forward", "ovr")
        
        # Same players, different order
        line_id_1 = store.store_concrete_line(run_id, [101, 205, 317], [1, 5], total_ovr=264)
        line_id_2 = store.store_concrete_line(run_id, [317, 101, 205], [1, 5], total_ovr=264)  # Same line
        
        assert line_id_1 is not None
        assert line_id_2 is None  # Should be skipped
        
        lines = store.get_concrete_lines(run_id=run_id)
        assert len(lines) == 1
    
    def test_deduplication_disabled(self, store):
        """Can disable deduplication if needed."""
        run_id = store.create_run("forward", "ovr")
        
        line_id_1 = store.store_concrete_line(run_id, [101, 205, 317], [1, 5], dedupe=False)
        line_id_2 = store.store_concrete_line(run_id, [317, 101, 205], [1, 5], dedupe=False)
        
        assert line_id_1 is not None
        assert line_id_2 is not None
        
        lines = store.get_concrete_lines(run_id=run_id)
        assert len(lines) == 2
    
    def test_query_by_position_and_mode(self, store):
        """Can query lines by position type and optimization mode."""
        # Create runs for different types/modes
        run_fwd_ovr = store.create_run("forward", "ovr")
        run_def_ovr = store.create_run("defense", "ovr")
        run_fwd_sal = store.create_run("forward", "sal")
        
        # Store lines in each run
        store.store_concrete_line(run_fwd_ovr, [101, 102, 103], [1], total_ovr=250)
        store.store_concrete_line(run_def_ovr, [201, 202], [2], total_ovr=180)
        store.store_concrete_line(run_fwd_sal, [301, 302, 303], [3], total_ovr=240)
        
        # Query by position type
        fwd_lines = store.get_concrete_lines(position_type="forward")
        assert len(fwd_lines) == 1
        assert fwd_lines[0].player_ids == [301, 302, 303]  # Latest forward run
        
        # Query by mode
        ovr_lines = store.get_concrete_lines(position_type="defense", optimization_mode="ovr")
        assert len(ovr_lines) == 1
        assert ovr_lines[0].player_ids == [201, 202]
    
    def test_query_latest_run(self, store):
        """Querying without run_id uses the latest matching run."""
        run_id_1 = store.create_run("forward", "ovr")
        store.store_concrete_line(run_id_1, [101, 102, 103], [1], total_ovr=250)
        
        run_id_2 = store.create_run("forward", "ovr")
        store.store_concrete_line(run_id_2, [201, 202, 203], [2], total_ovr=260)
        
        # Should return lines from run_id_2 (latest)
        lines = store.get_concrete_lines(position_type="forward", optimization_mode="ovr")
        
        assert len(lines) == 1
        assert lines[0].run_id == run_id_2
        assert lines[0].player_ids == [201, 202, 203]
    
    def test_pagination(self, store):
        """Can paginate concrete line results."""
        run_id = store.create_run("forward", "ovr")
        
        # Store 10 lines
        for i in range(10):
            store.store_concrete_line(
                run_id, 
                [100 + i, 200 + i, 300 + i], 
                [1],
                ranking_score=100 - i,  # Decreasing scores
            )
        
        # Get first page
        page_1 = store.get_concrete_lines(run_id=run_id, limit=3, offset=0)
        assert len(page_1) == 3
        assert page_1[0].ranking_score == 100  # Highest score first
        
        # Get second page
        page_2 = store.get_concrete_lines(run_id=run_id, limit=3, offset=3)
        assert len(page_2) == 3
        assert page_2[0].ranking_score == 97
    
    def test_count_concrete_lines(self, store):
        """Can count lines for a run."""
        run_id = store.create_run("forward", "ovr")
        
        for i in range(7):
            store.store_concrete_line(run_id, [100 + i, 200 + i, 300 + i], [1])
        
        count = store.count_concrete_lines(run_id)
        assert count == 7
    
    def test_batch_store(self, store):
        """Can store multiple lines efficiently in a batch."""
        run_id = store.create_run("forward", "ovr")
        
        lines = [
            Goal1ConcreteLine(
                run_id=run_id,
                player_ids=[100 + i, 200 + i, 300 + i],
                activated_combo_ids=[1, 2],
                total_ovr=250 + i,
                ranking_score=250 + i,
            )
            for i in range(5)
        ]
        
        stored = store.store_concrete_lines_batch(run_id, lines)
        
        assert stored == 5
        assert store.count_concrete_lines(run_id) == 5
    
    def test_batch_store_with_dedupe(self, store):
        """Batch store respects deduplication."""
        run_id = store.create_run("forward", "ovr")
        
        # First, store one line
        store.store_concrete_line(run_id, [101, 201, 301], [1])
        
        # Batch with one duplicate
        lines = [
            Goal1ConcreteLine(run_id=run_id, player_ids=[301, 201, 101], activated_combo_ids=[1]),  # Duplicate
            Goal1ConcreteLine(run_id=run_id, player_ids=[102, 202, 302], activated_combo_ids=[2]),  # New
            Goal1ConcreteLine(run_id=run_id, player_ids=[103, 203, 303], activated_combo_ids=[3]),  # New
        ]
        
        stored = store.store_concrete_lines_batch(run_id, lines, dedupe=True)
        
        assert stored == 2  # Only 2 new lines stored
        assert store.count_concrete_lines(run_id) == 3


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestFullPipeline:
    """Integration tests simulating the full Goal 1 pipeline."""
    
    def test_full_pipeline_with_mock_data(self, store):
        """
        Simulate the full pipeline:
        1. Create run
        2. Store mock Stage A results
        3. Store mock Stage B results
        4. Query back and verify
        """
        # Step 1: Create run
        run_id = store.create_run(
            position_type="forward",
            optimization_mode="ovr",
            parameters={"k": 200, "limit": 100},
        )
        
        # Step 2: Store Stage A results (mock)
        stage_a_mock = [
            {"rank": 1, "combo_ids": [1, 5, 12], "gain_ovr": 6, "gain_sal": 0},
            {"rank": 2, "combo_ids": [3, 8], "gain_ovr": 4, "gain_sal": 2},
            {"rank": 3, "combo_ids": [2, 7, 9], "gain_ovr": 3, "gain_sal": 0},
        ]
        
        stage_a_ids = []
        for sol in stage_a_mock:
            result_id = store.store_stage_a_result(
                run_id=run_id,
                solution_rank=sol["rank"],
                combo_ids=sol["combo_ids"],
                gain_ovr=sol["gain_ovr"],
                gain_sal=sol["gain_sal"],
            )
            stage_a_ids.append(result_id)
        
        # Step 3: Store Stage B results (mock concrete lines)
        stage_b_mock = [
            # Lines for Stage A solution 1
            {"players": [101, 205, 317], "combos": [1, 5, 12], "ovr": 264, "score": 270.0},
            {"players": [102, 205, 318], "combos": [1, 5], "ovr": 261, "score": 265.0},
            # Lines for Stage A solution 2
            {"players": [201, 206, 301], "combos": [3, 8], "ovr": 258, "score": 264.0},
        ]
        
        for i, line in enumerate(stage_b_mock):
            stage_a_id = stage_a_ids[0] if i < 2 else stage_a_ids[1]
            store.store_concrete_line(
                run_id=run_id,
                player_ids=line["players"],
                activated_combo_ids=line["combos"],
                total_ovr=line["ovr"],
                ranking_score=line["score"],
                stage_a_solution_id=stage_a_id,
            )
        
        # Step 4: Query and verify
        run = store.get_run(run_id)
        assert run is not None
        assert run.optimization_mode == OptimizationMode.OVR
        
        stage_a_results = store.get_stage_a_results(run_id)
        assert len(stage_a_results) == 3
        assert stage_a_results[0].gain_ovr == 6
        
        lines = store.get_concrete_lines(run_id=run_id)
        assert len(lines) == 3
        # Best line first (by ranking_score)
        assert lines[0].ranking_score == 270.0
        assert lines[0].total_ovr == 264
    
    def test_reproducibility(self, store):
        """Results can be reproduced by querying the same run_id."""
        run_id = store.create_run("forward", "ovr")
        
        store.store_concrete_line(run_id, [101, 102, 103], [1, 2], total_ovr=260)
        store.store_concrete_line(run_id, [201, 202, 203], [3], total_ovr=255)
        
        # Query twice
        lines_1 = store.get_concrete_lines(run_id=run_id)
        lines_2 = store.get_concrete_lines(run_id=run_id)
        
        # Should return identical results
        assert len(lines_1) == len(lines_2)
        for l1, l2 in zip(lines_1, lines_2):
            assert l1.id == l2.id
            assert l1.player_ids == l2.player_ids
            assert l1.total_ovr == l2.total_ovr


# =============================================================================
# MODEL TESTS
# =============================================================================

class TestGoal1ConcreteLineModel:
    """Tests for the Goal1ConcreteLine model."""
    
    def test_line_key_canonical(self):
        """Line key is canonical (same regardless of player order)."""
        line1 = Goal1ConcreteLine(
            run_id=1,
            player_ids=[101, 205, 317],
            activated_combo_ids=[1],
        )
        
        line2 = Goal1ConcreteLine(
            run_id=1,
            player_ids=[317, 101, 205],  # Different order
            activated_combo_ids=[1],
        )
        
        assert line1.line_key() == line2.line_key()
        assert line1.line_key() == "101,205,317"
