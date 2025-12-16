Implementation Notes (concise, research-style)
==============================================

Data sources and placeholders
-----------------------------
- Player data (preferred when present): `data/nhlhutbuilder_players_api_dedup.csv` generated from nhlhutbuilder.
  - `card_api_id` is used as `card_id` (unique per card).
  - `player_group_id` is used as `player_id` (canonical, to forbid multiple cards of the same player).
  - Salary is parsed from `$X.YM` into an integer in “millions” (e.g., `$12.0M` → `12`).
- Fallback player data: original CSVs under `data/` (kept untouched).
- Legacy synthetic overrides: `data/player_attributes_override.csv` (kept as a fallback path; can be removed once the dataset is authoritative).
- Chemistry combos (v3) from nhlhutbuilder scrape:
  - `fwd_line_combos_v3.csv` (68 entries), `def_line_combos_v3.csv` (71 entries) with reward_type {OVR, AP, SAL}. Original combos remain for fallback.

Solver/runtime choices
----------------------
- Environment: Python 3.11 is recommended on macOS. Very new Python versions can break Clingo wheels; treat 3.11 as the “stable baseline” for the project.
- Symbol handling: collect `model.symbols(shown=True)` to avoid use-after-free.
- Full-team pruning (to keep the search tractable):
  - FWD candidates: ~24, DEF: ~14, G: ~4 (sorted by OVR).
  - Each combo ID can activate at most once globally (team-wide).
  - A single line/pair can activate 0..N different combos simultaneously (and all such bonuses apply).
- Response times: forward/defense are interactive with candidate pruning; full-team still depends heavily on caps.

Optimization targets and constraints
------------------------------------
- Core constraint interpretation (used consistently across endpoints):
  - Salary “cap” is treated as an effective cap: `total_salary - salary_bonus <= max_salary` (SAL bonuses increase budget).
  - AP cap is treated analogously: `total_ap - ap_bonus <= max_ap`.
- Targets:
  - `ovr`: maximize base OVR + total OVR bonus from all activated combos.
  - `salary`: maximize total SAL bonus first; then maximize effective OVR.
  - `ap`: maximize total AP bonus first; then maximize effective OVR.
  - `balanced`: maximize total bonuses (SAL/AP/OVR); then maximize base OVR.
- Effective salary/AP in responses: `total_salary - salary_bonus`, `total_ap - ap_bonus`. No SAL/AP objectives yet; they can be added when real values/requirements are set.

API quick-checks (venv311)
--------------------------
- Forward line: `POST /optimize/forward-line` with e.g. `{min_ovr:86, require_center:true, max_salary:110, max_ap:26}` → 1 solution in tests (use `card_id` strings for exclusions if needed).
- Defense pair: `POST /optimize/defense-pair` with e.g. `{min_ovr:84, max_salary:110, max_ap:26}` → 1 solution in tests.
- Full team: `POST /optimize/full-team` with e.g. `{min_ovr:82, max_salary:110, max_ap:26}` → 1 solution (20 players, effective OVR ~1764) with current pruning.

Combo activation sanity check
-----------------------------
- Script: `python scripts/check_combo_activation.py` prints how many forward/defense combos can currently activate with the loaded dataset.
- With the nhlhutbuilder-based player snapshot and v3 combos, we currently see ~55/68 forward and ~56/71 defense combos activatable (the loader normalizes `type=CARD` to `event` codes such as `GM`, `FANT`, etc.).

Fresh player data from nhlhutbuilder
------------------------------------
- Fetch: `python scripts/fetch_nhlhutbuilder_api.py` hits `php/player_stats.php` (server-side DataTables) and writes `data/nhlhutbuilder_players_api.csv`. All columns mirror the site (CARD, NAT, TEAM, DIV, SAL, POS, HAND, WGT, HGT, NAME, OVR, aOVR, …, FO, DIS, card_api_id). It iterates pages until the API returns empty, then sorts by name for easy visual validation.
- Group duplicates: `python scripts/add_player_group_id.py` reads the API CSV and writes `data/nhlhutbuilder_players_api_dedup.csv` with two extra fields:
  - `player_group_id`: G1, G2, … for all cards belonging to the same player (heuristic key: name + position + hand + height_in + weight_lb + nationality).
  - `other_card_ids`: comma-separated list of the other card_api_id values in the same group (helps humans see alternate cards immediately).
- These dedup ids can be fed into ASP/backend as the canonical `player_id`, while `card_api_id` stays the per-card key. Rules can then forbid multiple cards from the same player_group_id.

Known limitations / next swaps
------------------------------
- Salary and most attributes are pulled from nhlhutbuilder; `ability_points` is still not available in the player snapshot and remains unset.
- Event codes in combos are raw filenames from the scrape; can be mapped to human-readable names later.
- `require_center` relies on `sub_position` derived from the per-card position (C/LW/RW) in the player snapshot.

How to swap in real data
------------------------
1) Put real attributes in an override CSV: `id, sub_position, salary, ap` (id = Skater ID for FWD/DEF, Goalie ID for G).
2) Keep combo files in v3 format (type/key). Swap to official combos if you have them; otherwise continue with the scrape-v3.
3) Adjust event buckets/salary/AP generator or remove it when official values arrive; original CSVs stay untouched.
