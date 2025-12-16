"""
Migration script to convert CSV files to SQLite database.

This script reads all CSV files from the data/ directory and creates
a SQLite database at data/nhl26.db with the following tables:
- skater_names: ID to name mappings for forwards and defense
- goalie_names: ID to name mappings for goalies
- forwards: Forward player cards
- defense: Defense player cards
- goalies: Goalie player cards
- forward_combos: Forward line combinations (3 players)
- defense_combos: Defense line combinations (2 players)

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
    
    # Skater names table
    cursor.execute("""
        CREATE TABLE skater_names (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    """)
    
    # Goalie names table
    cursor.execute("""
        CREATE TABLE goalie_names (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    """)
    
    # Forwards table (multiple cards per player possible)
    cursor.execute("""
        CREATE TABLE forwards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skater_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            overall INTEGER NOT NULL,
            nationality TEXT NOT NULL,
            league TEXT NOT NULL,
            team TEXT NOT NULL,
            position TEXT NOT NULL DEFAULT 'FWD'
        )
    """)
    
    # Defense table (multiple cards per player possible)
    cursor.execute("""
        CREATE TABLE defense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skater_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            overall INTEGER NOT NULL,
            nationality TEXT NOT NULL,
            league TEXT NOT NULL,
            team TEXT NOT NULL,
            position TEXT NOT NULL DEFAULT 'DEF'
        )
    """)
    
    # Goalies table (multiple cards per player possible)
    cursor.execute("""
        CREATE TABLE goalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goalie_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            overall INTEGER NOT NULL,
            nationality TEXT NOT NULL,
            league TEXT NOT NULL,
            team TEXT NOT NULL,
            position TEXT NOT NULL DEFAULT 'G'
        )
    """)
    
    # Forward combos table
    cursor.execute("""
        CREATE TABLE forward_combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    cursor.execute("CREATE INDEX idx_forwards_skater_id ON forwards(skater_id)")
    cursor.execute("CREATE INDEX idx_forwards_overall ON forwards(overall)")
    cursor.execute("CREATE INDEX idx_forwards_team ON forwards(team)")
    cursor.execute("CREATE INDEX idx_forwards_nationality ON forwards(nationality)")
    cursor.execute("CREATE INDEX idx_forwards_event ON forwards(event)")
    
    cursor.execute("CREATE INDEX idx_defense_skater_id ON defense(skater_id)")
    cursor.execute("CREATE INDEX idx_defense_overall ON defense(overall)")
    cursor.execute("CREATE INDEX idx_defense_team ON defense(team)")
    cursor.execute("CREATE INDEX idx_defense_nationality ON defense(nationality)")
    cursor.execute("CREATE INDEX idx_defense_event ON defense(event)")
    
    cursor.execute("CREATE INDEX idx_goalies_goalie_id ON goalies(goalie_id)")
    cursor.execute("CREATE INDEX idx_goalies_overall ON goalies(overall)")
    cursor.execute("CREATE INDEX idx_goalies_team ON goalies(team)")
    cursor.execute("CREATE INDEX idx_goalies_nationality ON goalies(nationality)")
    cursor.execute("CREATE INDEX idx_goalies_event ON goalies(event)")
    
    # =========================================================================
    # LOAD DATA FROM CSV FILES
    # =========================================================================
    
    print("\nLoading data from CSV files...")
    
    # Load skater names
    print("  - Loading skater_id.csv...")
    df = pd.read_csv(data_dir / "skater_id.csv")
    df.rename(columns={"ID": "id", "First name": "first_name", "Second name": "last_name"}, inplace=True)
    df.to_sql("skater_names", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} skater names")
    
    # Load goalie names
    print("  - Loading g_id.csv...")
    df = pd.read_csv(data_dir / "g_id.csv")
    df.rename(columns={"ID": "id", "First name": "first_name", "Second name": "last_name"}, inplace=True)
    df.to_sql("goalie_names", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} goalie names")
    
    # Load forwards
    print("  - Loading fwd_filtered.csv...")
    df = pd.read_csv(data_dir / "fwd_filtered.csv")
    df.rename(columns={
        "Skater ID": "skater_id",
        "nationalitys": "nationality",
        "leagues": "league",
        "teams": "team",
        "POS": "position"
    }, inplace=True)
    df = df[["skater_id", "event", "overall", "nationality", "league", "team", "position"]]
    df.to_sql("forwards", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} forwards")
    
    # Load defense
    print("  - Loading def_filtered.csv...")
    df = pd.read_csv(data_dir / "def_filtered.csv")
    df.rename(columns={
        "Skater ID": "skater_id",
        "nationalitys": "nationality",
        "leagues": "league",
        "teams": "team",
        "POS": "position"
    }, inplace=True)
    df = df[["skater_id", "event", "overall", "nationality", "league", "team", "position"]]
    df.to_sql("defense", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} defense players")
    
    # Load goalies
    print("  - Loading g_filtered.csv...")
    df = pd.read_csv(data_dir / "g_filtered.csv")
    df.rename(columns={
        "Goalie ID": "goalie_id",
        "nationalitys": "nationality",
        "leagues": "league",
        "teams": "team"
    }, inplace=True)
    df = df[["goalie_id", "event", "overall", "nationality", "league", "team"]]
    # Position will use default value 'G' from table definition
    df.to_sql("goalies", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} goalies")
    
    # Load forward combos
    print("  - Loading fwd_line_combos.csv...")
    df = pd.read_csv(data_dir / "fwd_line_combos.csv")
    # Reset index to start from 0 for consistent IDs
    df.reset_index(drop=True, inplace=True)
    df.to_sql("forward_combos", conn, if_exists="append", index=False)
    print(f"    Loaded {len(df)} forward combos")
    
    # Load defense combos
    print("  - Loading def_line_combos.csv...")
    df = pd.read_csv(data_dir / "def_line_combos.csv")
    # Reset index to start from 0 for consistent IDs
    df.reset_index(drop=True, inplace=True)
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

