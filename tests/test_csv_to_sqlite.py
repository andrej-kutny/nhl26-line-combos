"""
Tests for CSV to SQLite migration script.

Tests:
1. Idempotency: Running twice produces same metadata
2. Data integrity: SQLite rows match CSV rows
3. Row counts: SQLite table size matches CSV row count
"""

import sqlite3
import shutil
import pandas as pd
import pytest
from pathlib import Path
from scripts.csv_to_sqlite import create_database


@pytest.fixture(scope="module")
def test_data_dir(tmp_path_factory):
    """Create a temporary test data directory with CSV files."""
    # Create temp directory
    test_dir = tmp_path_factory.mktemp("data-test")
    
    # Copy all CSV files from data/ to data-test/
    source_dir = Path(__file__).parent.parent / "data"
    for csv_file in source_dir.glob("*.csv"):
        shutil.copy(csv_file, test_dir / csv_file.name)
    
    yield test_dir
    
    # Cleanup: remove test directory
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def db_path(test_data_dir):
    """Return the database path in test directory."""
    return test_data_dir / "nhl26.db"


@pytest.fixture(scope="module", autouse=True)
def setup_database(test_data_dir, db_path):
    """
    Setup fixture that creates the database before any tests run.
    
    This fixture is autouse=True and module-scoped, ensuring it runs once
    before any tests in this module, regardless of which tests are selected.
    """
    # Remove any existing db
    if db_path.exists():
        db_path.unlink()
    
    # Create the database (first run)
    create_database(test_data_dir, db_path)
    
    # Verify database was created
    assert db_path.exists(), "Database should be created by setup"
    assert db_path.stat().st_size > 0, "Database should not be empty"


def get_table_metadata(db_path: Path) -> dict:
    """
    Extract metadata from database tables.
    
    Returns dict with:
    - table_name -> {
        'columns': [(name, type), ...],
        'row_count': int,
        'indexes': [index_name, ...]
      }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    metadata = {}
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        # Get column info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [(row[1], row[2]) for row in cursor.fetchall()]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # Get indexes
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table}'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        metadata[table] = {
            'columns': columns,
            'row_count': row_count,
            'indexes': sorted(indexes)
        }
    
    conn.close()
    return metadata


class TestCSVToSQLiteIdempotency:
    """
    Test that running the migration script multiple times produces same results.
    
    These tests verify idempotency by running the migration script multiple times
    and comparing the results. The initial database setup is handled by the
    setup_database fixture, so these tests can run in any order.
    """
    
    def test_database_exists_after_setup(self, db_path):
        """Verify database was created by setup fixture."""
        assert db_path.exists(), "Database should exist after setup"
        assert db_path.stat().st_size > 0, "Database should not be empty"
    
    def test_all_expected_tables_exist(self, db_path):
        """Verify all expected tables were created."""
        metadata = get_table_metadata(db_path)
        
        expected_tables = {
            'skater_names', 'goalie_names',
            'forwards', 'defense', 'goalies',
            'forward_combos', 'defense_combos'
        }
        assert set(metadata.keys()) == expected_tables, \
            f"Expected tables: {expected_tables}, got: {set(metadata.keys())}"
    
    def test_second_run_produces_same_metadata(self, test_data_dir, db_path):
        """Running migration again should produce identical metadata (idempotency test)."""
        # Get metadata from current state (created by setup_database fixture)
        metadata_before = get_table_metadata(db_path)
        
        # Run migration again (directly calling create_database)
        create_database(test_data_dir, db_path)
        
        # Get metadata after second run
        metadata_after = get_table_metadata(db_path)
        
        # Compare metadata (should be identical)
        assert metadata_before.keys() == metadata_after.keys(), \
            "Tables should be the same after re-running migration"
        
        for table in metadata_before.keys():
            assert metadata_before[table]['columns'] == metadata_after[table]['columns'], \
                f"Columns differ for table {table}"
            assert metadata_before[table]['row_count'] == metadata_after[table]['row_count'], \
                f"Row count differs for table {table}: {metadata_before[table]['row_count']} vs {metadata_after[table]['row_count']}"
            assert metadata_before[table]['indexes'] == metadata_after[table]['indexes'], \
                f"Indexes differ for table {table}"


class TestForwardsTable:
    """Test forwards table data integrity."""
    
    def test_row_count_matches_csv(self, test_data_dir, db_path):
        """Forwards table row count should match CSV."""
        csv_df = pd.read_csv(test_data_dir / "fwd_filtered.csv")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM forwards")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == len(csv_df)
    
    def test_all_csv_rows_in_database(self, test_data_dir, db_path):
        """Every CSV row should exist in database (excluding card_id)."""
        csv_df = pd.read_csv(test_data_dir / "fwd_filtered.csv")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM forwards")
        db_rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # For each CSV row, find matching database row
        for _, csv_row in csv_df.iterrows():
            # Find matching row in database (by player_id and overall)
            matching_rows = [
                db_row for db_row in db_rows
                if db_row['player_id'] == csv_row['player_id']
                and db_row['overall'] == csv_row['overall']
                and db_row['event'].upper() == str(csv_row['event']).upper()
                and db_row['team'].upper() == str(csv_row['team']).upper()
            ]
            
            assert len(matching_rows) > 0, \
                f"No matching row found for player_id={csv_row['player_id']}, overall={csv_row['overall']}"
            
            # Verify key fields match (with uppercase conversion)
            db_row = matching_rows[0]
            assert db_row['nationality'].upper() == str(csv_row['nationality']).upper()
            assert db_row['position'] == csv_row['position']
            assert db_row['salary'] == csv_row['salary']
            assert db_row['weight'] == csv_row['weight']
            assert db_row['height'] == csv_row['height']


class TestDefenseTable:
    """Test defense table data integrity."""
    
    def test_row_count_matches_csv(self, test_data_dir, db_path):
        """Defense table row count should match CSV."""
        csv_df = pd.read_csv(test_data_dir / "def_filtered.csv")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM defense")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == len(csv_df)
    
    def test_all_csv_rows_in_database(self, test_data_dir, db_path):
        """Every CSV row should exist in database."""
        csv_df = pd.read_csv(test_data_dir / "def_filtered.csv")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM defense")
        db_rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        for _, csv_row in csv_df.iterrows():
            matching_rows = [
                db_row for db_row in db_rows
                if db_row['player_id'] == csv_row['player_id']
                and db_row['overall'] == csv_row['overall']
                and db_row['event'].upper() == str(csv_row['event']).upper()
                and db_row['team'].upper() == str(csv_row['team']).upper()
            ]
            
            assert len(matching_rows) > 0, \
                f"No matching row found for player_id={csv_row['player_id']}, overall={csv_row['overall']}"
            
            db_row = matching_rows[0]
            assert db_row['nationality'].upper() == str(csv_row['nationality']).upper()
            assert db_row['position'] == csv_row['position']


class TestGoaliesTable:
    """Test goalies table data integrity."""
    
    def test_row_count_matches_csv(self, test_data_dir, db_path):
        """Goalies table row count should match CSV."""
        csv_df = pd.read_csv(test_data_dir / "g_filtered.csv")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM goalies")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == len(csv_df)
    
    def test_all_csv_rows_in_database(self, test_data_dir, db_path):
        """Every CSV row should exist in database."""
        csv_df = pd.read_csv(test_data_dir / "g_filtered.csv")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goalies")
        db_rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        for _, csv_row in csv_df.iterrows():
            matching_rows = [
                db_row for db_row in db_rows
                if db_row['player_id'] == csv_row['player_id']
                and db_row['overall'] == csv_row['overall']
                and db_row['event'].upper() == str(csv_row['event']).upper()
            ]
            
            assert len(matching_rows) > 0, \
                f"No matching row found for player_id={csv_row['player_id']}, overall={csv_row['overall']}"


class TestSkaterNamesTable:
    """Test skater_names table data integrity."""
    
    def test_row_count_matches_csv(self, test_data_dir, db_path):
        """Skater names table row count should match CSV."""
        csv_df = pd.read_csv(test_data_dir / "skater_id.csv")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM skater_names")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == len(csv_df)
    
    def test_all_names_in_database(self, test_data_dir, db_path):
        """Every name from CSV should exist in database."""
        csv_df = pd.read_csv(test_data_dir / "skater_id.csv")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skater_names")
        db_rows = {row['player_id']: (row['first_name'], row['last_name']) for row in cursor.fetchall()}
        conn.close()
        
        for _, csv_row in csv_df.iterrows():
            player_id = csv_row['player_id']
            assert player_id in db_rows
            assert db_rows[player_id][0] == csv_row['First name']
            assert db_rows[player_id][1] == csv_row['Second name']


class TestGoalieNamesTable:
    """Test goalie_names table data integrity."""
    
    def test_row_count_matches_csv(self, test_data_dir, db_path):
        """Goalie names table row count should match CSV."""
        csv_df = pd.read_csv(test_data_dir / "g_id.csv")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM goalie_names")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == len(csv_df)


class TestForwardCombosTable:
    """Test forward_combos table data integrity."""
    
    def test_row_count_matches_csv(self, test_data_dir, db_path):
        """Forward combos table row count should match CSV."""
        csv_df = pd.read_csv(test_data_dir / "fwd_line_combos.csv")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM forward_combos")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == len(csv_df)
    
    def test_combo_conditions_uppercase(self, db_path):
        """Verify that type and key fields are uppercase."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM forward_combos LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            for i in [1, 2, 3]:
                type_col = f'type{i}'
                key_col = f'key{i}'
                assert row[type_col] == row[type_col].upper(), f"{type_col} should be uppercase"
                assert row[key_col] == row[key_col].upper(), f"{key_col} should be uppercase"


class TestDefenseCombosTable:
    """Test defense_combos table data integrity."""
    
    def test_row_count_matches_csv(self, test_data_dir, db_path):
        """Defense combos table row count should match CSV."""
        csv_df = pd.read_csv(test_data_dir / "def_line_combos.csv")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM defense_combos")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == len(csv_df)
    
    def test_combo_conditions_uppercase(self, db_path):
        """Verify that type and key fields are uppercase."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM defense_combos LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            for i in [1, 2]:
                type_col = f'type{i}'
                key_col = f'key{i}'
                assert row[type_col] == row[type_col].upper(), f"{type_col} should be uppercase"
                assert row[key_col] == row[key_col].upper(), f"{key_col} should be uppercase"


class TestDatabaseSchema:
    """Test database schema and indexes."""
    
    def test_all_expected_indexes_exist(self, db_path):
        """Verify all expected indexes are created."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Expected indexes for important filtering fields
        expected_indexes = [
            'idx_forwards_player_id',
            'idx_forwards_overall',
            'idx_forwards_team',
            'idx_forwards_nationality',
            'idx_forwards_event',
            'idx_forwards_position',
            'idx_defense_player_id',
            'idx_defense_overall',
            'idx_defense_team',
            'idx_defense_nationality',
            'idx_defense_event',
            'idx_defense_position',
            'idx_goalies_player_id',
            'idx_goalies_overall',
            'idx_goalies_team',
            'idx_goalies_nationality',
            'idx_goalies_event',
        ]
        
        for expected in expected_indexes:
            assert expected in indexes, f"Index {expected} not found"
    
    def test_efficient_data_types(self, db_path):
        """Verify efficient data types are used."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check forwards table
        cursor.execute("PRAGMA table_info(forwards)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert 'VARCHAR' in columns['position'], "position should use VARCHAR"
        assert 'VARCHAR' in columns['team'], "team should use VARCHAR"
        assert 'VARCHAR' in columns['event'], "event should use VARCHAR"
        assert 'VARCHAR' in columns['nationality'], "nationality should use VARCHAR"
        
        conn.close()

