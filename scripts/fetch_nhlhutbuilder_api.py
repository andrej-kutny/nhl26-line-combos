"""
Fetch player stats from nhlhutbuilder.com's DataTables API and save to a clean CSV.

Hits https://nhlhutbuilder.com/php/player_stats.php (server-side DataTables).
Defaults to 10 pages * 25 rows (250 rows) so we can validate against page 1
on the site. Increase PAGES if you want the full dataset.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


API_URL = "https://nhlhutbuilder.com/php/player_stats.php"

# Column order mirrors the table on player-stats.php (SAL kept as raw string).
# Extra column card_api_id is the anchor id (unique per card on the site).
COLUMNS = [
    "card",
    "nationality",
    "team",
    "division",
    "salary",
    "position",
    "hand",
    "weight_lb",
    "height_in",
    "name",
    "overall",
    "aOVR",
    "acceleration",
    "agility",
    "balance",
    "endurance",
    "speed",
    "slap_shot_accuracy",
    "slap_shot_power",
    "wrist_shot_accuracy",
    "wrist_shot_power",
    "deking",
    "offensive_awareness",
    "hand_eye",
    "passing",
    "puck_control",
    "body_checking",
    "strength",
    "aggression",
    "durability",
    "fighting_skill",
    "defensive_awareness",
    "shot_blocking",
    "stick_checking",
    "faceoffs",
    "discipline",
    "card_api_id",
]


def clean_html(text: str) -> str:
    # Remove HTML tags and decode common entities
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def parse_salary(s: str) -> float:
    # Input like "$12.0M" -> 12.0
    s = clean_html(s)
    s = s.replace("$", "").replace("M", "").strip()
    try:
        return float(s)
    except Exception:
        return 0.0


def parse_weight(s: str) -> float:
    # "200 lb" -> 200
    s = clean_html(s)
    m = re.search(r"([0-9]+(?:\\.[0-9]+)?)", s)
    return float(m.group(1)) if m else 0.0


def parse_height(s: str) -> float:
    # "6' 1\"" -> inches
    s = clean_html(s)
    m = re.match(r"(\d+)'\s*(\d+)", s)
    if not m:
        return 0.0
    feet = int(m.group(1))
    inches = int(m.group(2))
    return feet * 12 + inches


def parse_card_api_id(s: str) -> str:
    """Extract numeric id from the anchor in card_art/full_name (id="1001")."""

    m = re.search(r'id="(\d+)"', s)
    return m.group(1) if m else ""


def fetch_page(start: int, length: int = 25, draw: int = 1) -> List[Dict[str, Any]]:
    data = {
        "start": start,
        "length": length,
        "draw": draw,
    }
    payload = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
    parsed = json.loads(raw)
    return parsed.get("data", [])


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    out_path = project_root / "data" / "nhlhutbuilder_players_api.csv"

    length = 25
    all_rows: List[List[Any]] = []
    def format_row(r: Dict[str, Any]) -> List[Any]:
        return [
            clean_html(r.get("card", "")),
            clean_html(r.get("nationality", "")),
            clean_html(r.get("team", "")),
            clean_html(r.get("division", "")),
            clean_html(r.get("salary", "")),
            clean_html(r.get("position", "")),
            clean_html(r.get("hand", "")),
            parse_weight(r.get("weight", "")),
            parse_height(r.get("height", "")),
            clean_html(r.get("full_name", "")),
            r.get("overall", ""),
            r.get("aOVR", ""),
            r.get("acceleration", ""),
            r.get("agility", ""),
            r.get("balance", ""),
            r.get("endurance", ""),
            r.get("speed", ""),
            r.get("slap_shot_accuracy", ""),
            r.get("slap_shot_power", ""),
            r.get("wrist_shot_accuracy", ""),
            r.get("wrist_shot_power", ""),
            r.get("deking", ""),
            r.get("off_awareness", ""),
            r.get("hand_eye", ""),
            r.get("passing", ""),
            r.get("puck_control", ""),
            r.get("body_checking", ""),
            r.get("strength", ""),
            r.get("aggression", ""),
            r.get("durability", ""),
            r.get("fighting_skill", ""),
            r.get("def_awareness", ""),
            r.get("shot_blocking", ""),
            r.get("stick_checking", ""),
            r.get("faceoffs", ""),
            r.get("discipline", ""),
            parse_card_api_id(r.get("card_art", "") or r.get("full_name", "")),
        ]

    # Fetch pages until tomt svar; robust mot avsaknad av recordsTotal
    max_pages = 500  # skydd mot evig loop
    for i in range(max_pages):
        start = i * length
        rows = fetch_page(start=start, length=length, draw=i + 1)
        if not rows:
            break
        all_rows.extend(format_row(r) for r in rows)
        print(f"Fetched page {i+1} (rows: {len(rows)})")

    # Sort alphabetically by name for easier manual validation.
    all_rows = sorted(all_rows, key=lambda r: str(r[9]).upper())

    import csv

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(all_rows)

    print(f"Saved {len(all_rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
