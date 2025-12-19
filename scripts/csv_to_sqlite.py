"""
Migration script to convert CSV files to SQLite database.

This script reads all CSV files from the data/ directory and creates
a SQLite database at data/nhl26.db with the following tables:
- skater_names: Player ID to name mappings for forwards and defense
- goalie_names: Player ID to name mappings for goalies
- forwards: Forward player cards with all stats
- defense: Defense player cards with all stats
- goalies: Goalie player cards with all stats
- forward_combos: Forward line combinations (3 players)
- defense_combos: Defense line combinations (2 players)
- goal1_runs: Goal 1 pipeline run metadata (timestamp, mode, parameters)
- goal1_stage_a_results: Stage A abstract combo selections
- goal1_concrete_lines: Stage B concrete lines with player assignments

Usage:
    python scripts/csv_to_sqlite.py
"""

import sqlite3
import pandas as pd
from pathlib import Path


def create_database(data_dir: Path, db_path: Path):
    """Create SQLite database from CSV files."""
    
    print(f"Creating database at: {db_path}")
    
    # Remove existing database if it exists
    if db_path.exists():
        print(f"Removing existing database...")
        db_path.unlink()
    
    # Connect to database (creates it)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # =========================================================================
    # CREATE TABLES
    # =========================================================================
    
    print("Creating tables...")
    
    # Skater names table (player_id -> name mapping)
    cursor.execute("""
        CREATE TABLE skater_names (
            player_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    """)
    
    # Goalie names table (player_id -> name mapping)
    cursor.execute("""
        CREATE TABLE goalie_names (
            player_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    """)
    
    # Forwards table (multiple cards per player possible)
    cursor.execute("""
        CREATE TABLE forwards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            img VARCHAR(100) NOT NULL,
            position VARCHAR(2) NOT NULL,
            nationality VARCHAR(20) NOT NULL,
            event VARCHAR(10) NOT NULL,
            league VARCHAR(10) NOT NULL,
            team VARCHAR(3) NOT NULL,
            weight REAL NOT NULL,
            height INTEGER NOT NULL,
            salary REAL NOT NULL,
            overall INTEGER NOT NULL,
            deking INTEGER NOT NULL,
            hand_eye INTEGER NOT NULL,
            passing INTEGER NOT NULL,
            puck_control INTEGER NOT NULL,
            slap_shot_accuracy INTEGER NOT NULL,
            slap_shot_power INTEGER NOT NULL,
            wrist_shot_accuracy INTEGER NOT NULL,
            wrist_shot_power INTEGER NOT NULL,
            acceleration INTEGER NOT NULL,
            agility INTEGER NOT NULL,
            balance INTEGER NOT NULL,
            endurance INTEGER NOT NULL,
            speed INTEGER NOT NULL,
            discipline INTEGER NOT NULL,
            off_awareness INTEGER NOT NULL,
            def_awareness INTEGER NOT NULL,
            faceoffs INTEGER NOT NULL,
            shot_blocking INTEGER NOT NULL,
            stick_checking INTEGER NOT NULL,
            aggression INTEGER NOT NULL,
            body_checking INTEGER NOT NULL,
            durability INTEGER NOT NULL,
            fighting_skill INTEGER NOT NULL,
            strength INTEGER NOT NULL
        )
    """)
    
    # Defense table (multiple cards per player possible)
    cursor.execute("""
        CREATE TABLE defense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            img VARCHAR(100) NOT NULL,
            position VARCHAR(2) NOT NULL,
            nationality VARCHAR(20) NOT NULL,
            event VARCHAR(10) NOT NULL,
            league VARCHAR(10) NOT NULL,
            team VARCHAR(3) NOT NULL,
            weight REAL NOT NULL,
            height INTEGER NOT NULL,
            salary REAL NOT NULL,
            overall INTEGER NOT NULL,
            deking INTEGER NOT NULL,
            hand_eye INTEGER NOT NULL,
            passing INTEGER NOT NULL,
            puck_control INTEGER NOT NULL,
            slap_shot_accuracy INTEGER NOT NULL,
            slap_shot_power INTEGER NOT NULL,
            wrist_shot_accuracy INTEGER NOT NULL,
            wrist_shot_power INTEGER NOT NULL,
            acceleration INTEGER NOT NULL,
            agility INTEGER NOT NULL,
            balance INTEGER NOT NULL,
            endurance INTEGER NOT NULL,
            speed INTEGER NOT NULL,
            discipline INTEGER NOT NULL,
            off_awareness INTEGER NOT NULL,
            def_awareness INTEGER NOT NULL,
            faceoffs INTEGER NOT NULL,
            shot_blocking INTEGER NOT NULL,
            stick_checking INTEGER NOT NULL,
            aggression INTEGER NOT NULL,
            body_checking INTEGER NOT NULL,
            durability INTEGER NOT NULL,
            fighting_skill INTEGER NOT NULL,
            strength INTEGER NOT NULL
        )
    """)
    
    # Goalies table (multiple cards per player possible)
    cursor.execute("""
        CREATE TABLE goalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            img VARCHAR(100) NOT NULL,
            nationality VARCHAR(20) NOT NULL,
            event VARCHAR(10) NOT NULL,
            league VARCHAR(10) NOT NULL,
            team VARCHAR(3) NOT NULL,
            weight REAL NOT NULL,
            height INTEGER NOT NULL,
            salary REAL NOT NULL,
            overall INTEGER NOT NULL,
            passing INTEGER NOT NULL,
            agility INTEGER NOT NULL,
            speed INTEGER NOT NULL,
            aggression INTEGER NOT NULL,
            glove_high INTEGER NOT NULL,
            glove_low INTEGER NOT NULL,
            five_hole INTEGER NOT NULL,
            stick_high INTEGER NOT NULL,
            stick_low INTEGER NOT NULL,
            shot_recovery INTEGER NOT NULL,
            positioning INTEGER NOT NULL,
            breakaway INTEGER NOT NULL,
            vision INTEGER NOT NULL,
            poke_check INTEGER NOT NULL,
            rebound_control INTEGER NOT NULL
        )
    """)
    
    # Forward combos table
    cursor.execute("""
        CREATE TABLE forward_combos (
            -- Persist stable IDs from CSV (combo_id) to avoid SQLite row-id drift.
            id INTEGER PRIMARY KEY,
            reward_amount INTEGER NOT NULL,
            reward_type TEXT NOT NULL,
            type1 TEXT NOT NULL,
            key1 TEXT NOT NULL,
            type2 TEXT NOT NULL,
            key2 TEXT NOT NULL,
            type3 TEXT NOT NULL,
            key3 TEXT NOT NULL
        )
    """)
    
    # Defense combos table
    cursor.execute("""
        CREATE TABLE defense_combos (
            -- Persist stable IDs from CSV (combo_id) to avoid SQLite row-id drift.
            id INTEGER PRIMARY KEY,
            reward_amount INTEGER NOT NULL,
            reward_type TEXT NOT NULL,
            type1 TEXT NOT NULL,
            key1 TEXT NOT NULL,
            type2 TEXT NOT NULL,
            key2 TEXT NOT NULL
        )
    """)
    
    # Create indexes for better query performance
    print("Creating indexes...")
    
    # Forward indexes (for important filtering fields)
    cursor.execute("CREATE INDEX idx_forwards_player_id ON forwards(player_id)")
    cursor.execute("CREATE INDEX idx_forwards_overall ON forwards(overall)")
    cursor.execute("CREATE INDEX idx_forwards_team ON forwards(team)")
    cursor.execute("CREATE INDEX idx_forwards_nationality ON forwards(nationality)")
    cursor.execute("CREATE INDEX idx_forwards_event ON forwards(event)")
    cursor.execute("CREATE INDEX idx_forwards_position ON forwards(position)")
    
    # Defense indexes (for important filtering fields)
    cursor.execute("CREATE INDEX idx_defense_player_id ON defense(player_id)")
    cursor.execute("CREATE INDEX idx_defense_overall ON defense(overall)")
    cursor.execute("CREATE INDEX idx_defense_team ON defense(team)")
    cursor.execute("CREATE INDEX idx_defense_nationality ON defense(nationality)")
    cursor.execute("CREATE INDEX idx_defense_event ON defense(event)")
    cursor.execute("CREATE INDEX idx_defense_position ON defense(position)")
    
    # Goalie indexes (for important filtering fields)
    cursor.execute("CREATE INDEX idx_goalies_player_id ON goalies(player_id)")
    cursor.execute("CREATE INDEX idx_goalies_overall ON goalies(overall)")
    cursor.execute("CREATE INDEX idx_goalies_team ON goalies(team)")
    cursor.execute("CREATE INDEX idx_goalies_nationality ON goalies(nationality)")
    cursor.execute("CREATE INDEX idx_goalies_event ON goalies(event)")
    
    # No additional indexes needed for combos (id is already primary key)
    
    # =========================================================================
    # GOAL 1 RESULT TABLES
    # =========================================================================
    
    print("Creating Goal 1 result tables...")
    
    # Goal 1 run metadata
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
    
    # Stage A results (abstract combo selections)
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
    
    # Stage B results (concrete lines)
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
    
    # Create indexes for Goal 1 tables
    print("Creating Goal 1 indexes...")
    cursor.execute("CREATE INDEX idx_goal1_runs_position_mode ON goal1_runs(position_type, optimization_mode)")
    cursor.execute("CREATE INDEX idx_goal1_runs_timestamp ON goal1_runs(run_timestamp)")
    cursor.execute("CREATE INDEX idx_stage_a_run_id ON goal1_stage_a_results(run_id)")
    cursor.execute("CREATE INDEX idx_stage_a_rank ON goal1_stage_a_results(run_id, solution_rank)")
    cursor.execute("CREATE INDEX idx_concrete_lines_run_id ON goal1_concrete_lines(run_id)")
    cursor.execute("CREATE INDEX idx_concrete_lines_stage_a ON goal1_concrete_lines(stage_a_solution_id)")
    cursor.execute("CREATE INDEX idx_concrete_lines_key ON goal1_concrete_lines(run_id, line_key)")
    cursor.execute("CREATE INDEX idx_concrete_lines_score ON goal1_concrete_lines(run_id, ranking_score DESC)")
    
    # =========================================================================
    # LOAD DATA FROM CSV FILES
    # =========================================================================
    
    print("\nLoading data from CSV files...")
    
    # Load skater names
    print("  - Loading skater_id.csv...")
    df = pd.read_csv(data_dir / "skater_id.csv")
    df.rename(columns={
        "ID": "player_id",
        "First name": "first_name",
        "Second name": "last_name"
    }, inplace=True)
    df = df[["player_id", "first_name", "last_name"]]
    df.to_sql("skater_names", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} skater names")
    
    # Load goalie names
    print("  - Loading g_id.csv...")
    df = pd.read_csv(data_dir / "g_id.csv")
    df.rename(columns={
        "ID": "player_id",
        "First name": "first_name",
        "Second name": "last_name"
    }, inplace=True)
    df = df[["player_id", "first_name", "last_name"]]
    df.to_sql("goalie_names", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} goalie names")
    
    # Load forwards
    print("  - Loading fwd_filtered.csv...")
    df = pd.read_csv(data_dir / "fwd_filtered.csv")
    # Convert important filtering fields to uppercase
    df['nationality'] = df['nationality'].str.upper()
    df['event'] = df['event'].str.upper()
    df['team'] = df['team'].str.upper()
    # Select only the columns we need (excluding POS and card_id)
    df = df[[
        "player_id", "img", "position",
        "nationality", "event", "league", "team",
        "weight", "height", "salary", "overall",
        "deking", "hand_eye", "passing", "puck_control",
        "slap_shot_accuracy", "slap_shot_power",
        "wrist_shot_accuracy", "wrist_shot_power",
        "acceleration", "agility", "balance", "endurance", "speed",
        "discipline", "off_awareness", "def_awareness", "faceoffs",
        "shot_blocking", "stick_checking",
        "aggression", "body_checking", "durability", "fighting_skill", "strength"
    ]]
    df.to_sql("forwards", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} forwards")
    
    # Load defense
    print("  - Loading def_filtered.csv...")
    df = pd.read_csv(data_dir / "def_filtered.csv")
    # Convert important filtering fields to uppercase
    df['nationality'] = df['nationality'].str.upper()
    df['event'] = df['event'].str.upper()
    df['team'] = df['team'].str.upper()
    # Select only the columns we need (excluding POS and card_id)
    df = df[[
        "player_id", "img", "position",
        "nationality", "event", "league", "team",
        "weight", "height", "salary", "overall",
        "deking", "hand_eye", "passing", "puck_control",
        "slap_shot_accuracy", "slap_shot_power",
        "wrist_shot_accuracy", "wrist_shot_power",
        "acceleration", "agility", "balance", "endurance", "speed",
        "discipline", "off_awareness", "def_awareness", "faceoffs",
        "shot_blocking", "stick_checking",
        "aggression", "body_checking", "durability", "fighting_skill", "strength"
    ]]
    df.to_sql("defense", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} defense players")
    
    # Load goalies
    print("  - Loading g_filtered.csv...")
    df = pd.read_csv(data_dir / "g_filtered.csv")
    # Convert important filtering fields to uppercase
    df['nationality'] = df['nationality'].str.upper()
    df['event'] = df['event'].str.upper()
    df['team'] = df['team'].str.upper()
    # Select only the columns we need (excluding card_id)
    df = df[[
        "player_id", "img",
        "nationality", "event", "league", "team",
        "weight", "height", "salary", "overall",
        "passing", "agility", "speed", "aggression",
        "glove_high", "glove_low", "five_hole",
        "stick_high", "stick_low", "shot_recovery",
        "positioning", "breakaway", "vision",
        "poke_check", "rebound_control"
    ]]
    df.to_sql("goalies", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} goalies")
    
    # Load forward combos
    print("  - Loading fwd_line_combos.csv...")
    df = pd.read_csv(data_dir / "fwd_line_combos.csv")
    if "combo_id" not in df.columns:
        raise ValueError("Expected column 'combo_id' in fwd_line_combos.csv")
    if df["combo_id"].isna().any():
        raise ValueError("Found missing combo_id values in fwd_line_combos.csv")
    if df["combo_id"].duplicated().any():
        dupes = df.loc[df["combo_id"].duplicated(), "combo_id"].tolist()[:10]
        raise ValueError(f"Found duplicate combo_id values in fwd_line_combos.csv (sample: {dupes})")
    # Convert type and key fields to uppercase
    for i in [1, 2, 3]:
        df[f'type{i}'] = df[f'type{i}'].str.upper()
        df[f'key{i}'] = df[f'key{i}'].str.upper()
    # Persist stable IDs from CSV (combo_id) in the SQLite `id` column.
    df = df.rename(columns={"combo_id": "id"})
    df = df[['id', 'reward_amount', 'reward_type', 'type1', 'key1', 'type2', 'key2', 'type3', 'key3']]
    df.to_sql("forward_combos", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} forward combos")
    
    # Load defense combos
    print("  - Loading def_line_combos.csv...")
    df = pd.read_csv(data_dir / "def_line_combos.csv")
    if "combo_id" not in df.columns:
        raise ValueError("Expected column 'combo_id' in def_line_combos.csv")
    if df["combo_id"].isna().any():
        raise ValueError("Found missing combo_id values in def_line_combos.csv")
    if df["combo_id"].duplicated().any():
        dupes = df.loc[df["combo_id"].duplicated(), "combo_id"].tolist()[:10]
        raise ValueError(f"Found duplicate combo_id values in def_line_combos.csv (sample: {dupes})")
    # Convert type and key fields to uppercase
    for i in [1, 2]:
        df[f'type{i}'] = df[f'type{i}'].str.upper()
        df[f'key{i}'] = df[f'key{i}'].str.upper()
    # Persist stable IDs from CSV (combo_id) in the SQLite `id` column.
    df = df.rename(columns={"combo_id": "id"})
    df = df[['id', 'reward_amount', 'reward_type', 'type1', 'key1', 'type2', 'key2']]
    df.to_sql("defense_combos", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} defense combos")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"\n✓ Database created successfully at: {db_path}")
    print(f"  Size: {db_path.stat().st_size / 1024:.2f} KB")


def main():
    """Main function."""
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    db_path = data_dir / "nhl26.db"
    
    # Validate data directory exists
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return
    
    # Check all required CSV files exist
    required_files = [
        "fwd_filtered.csv",
        "def_filtered.csv",
        "g_filtered.csv",
        "skater_id.csv",
        "g_id.csv",
        "fwd_line_combos.csv",
        "def_line_combos.csv",
    ]
    
    missing = [f for f in required_files if not (data_dir / f).exists()]
    if missing:
        print(f"Error: Missing required CSV files: {missing}")
        return
    
    # Create database
    create_database(data_dir, db_path)


if __name__ == "__main__":
    main()
