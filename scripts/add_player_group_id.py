"""
Add a player_group_id to the nhlhutbuilder API CSV to tie multiple cards
for the same real player to one identifier (G001, G002, ...).

Heuristic key: name (upper), position, hand, height_in, weight_lb, nationality.
Adjust the key if you want stricter/looser grouping.
"""

from __future__ import annotations

import csv
from pathlib import Path

IN_PATH = Path(__file__).resolve().parents[1] / "data" / "nhlhutbuilder_players_api.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "nhlhutbuilder_players_api_dedup.csv"


def canonical_key(row: dict) -> tuple:
    return (
        row.get("name", "").strip().upper(),
        row.get("position", "").strip().upper(),
        row.get("hand", "").strip().upper(),
        row.get("height_in", "").strip(),
        row.get("weight_lb", "").strip(),
        row.get("nationality", "").strip().upper(),
    )


def main() -> None:
    with IN_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    groups: dict[tuple, str] = {}
    group_to_cards: dict[str, list[str]] = {}
    next_id = 1
    for r in rows:
        key = canonical_key(r)
        if key not in groups:
            groups[key] = f"G{next_id}"
            next_id += 1
        gid = groups[key]
        r["player_group_id"] = gid
        group_to_cards.setdefault(gid, []).append(str(r.get("card_api_id", "")).strip())

    # Build other_card_ids (other card_api_id in same group, excluding self)
    for r in rows:
        gid = r["player_group_id"]
        cards = [c for c in group_to_cards.get(gid, []) if c and c != str(r.get("card_api_id", "")).strip()]
        r["other_card_ids"] = ",".join(cards)

    fieldnames = list(rows[0].keys())
    if "player_group_id" not in fieldnames:
        fieldnames.append("player_group_id")
    if "other_card_ids" not in fieldnames:
        fieldnames.append("other_card_ids")

    # Sort by name for easier inspection
    rows.sort(key=lambda r: r.get("name", "").upper())

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows with group ids to {OUT_PATH}")


if __name__ == "__main__":
    main()
