Implementation Notes (concise, research-style)
==============================================

Data sources and placeholders
-----------------------------
- Player base data: original CSVs under `data/` (kept untouched).
- Synthetic attributes in `data/player_attributes_override.csv`:
  - Sub-position (C/LW/RW) synthesized per team: sort FWD by OVR, every 3rd → C, remaining alternate LW/RW.
  - Salary (placeholder): `round((50_000 + 5_000*(OVR-80)) * event_mult)`; multipliers base={XP,ROOK,FANT,default}:1.0, promo={HH,NHL24,WCUP,ICON-LITE}:1.2, high-end={ICON,MSP,HH-MASTER}:1.5.
  - AP (placeholder): `max(0, floor((OVR-80)/2)) + event_bonus`; bonus base=0, promo=1, high-end=2.
- Chemistry combos (v3) from nhlhutbuilder scrape:
  - `fwd_line_combos_v3.csv` (68 entries), `def_line_combos_v3.csv` (71 entries) with reward_type {OVR, AP, SAL}. Original combos remain for fallback.

Solver/runtime choices
----------------------
- Environment: Python 3.11 with `clingo==5.7.1` (5.8.0 + 3.13 segfaulted). Use `venv311`.
- Symbol handling: collect `model.symbols(shown=True)` to avoid use-after-free.
- Full-team pruning (to keep the search tractable):
  - FWD candidates: ~24, DEF: ~14, G: ~4 (sorted by OVR).
  - Each combo ID can activate at most once globally.
- Response times: forward/defense are fast; full-team ~60–120 s with current caps (can be tightened or given a timeout).

Optimization targets and constraints
------------------------------------
- Primary objective: maximize OVR + OVR bonuses.
- SAL/AP facts and bonuses are in the rules; cap-checks fire if `max_salary`/`max_ap` are provided in constraints.
- Effective salary/AP in responses: `total_salary - salary_bonus`, `total_ap - ap_bonus`. No SAL/AP objectives yet; they can be added when real values/requirements are set.

API quick-checks (venv311)
--------------------------
- Forward line: `POST /optimize/forward-line` with e.g. `{min_ovr:86, require_center:true, max_salary:110, max_ap:26}` → 1 solution in tests.
- Defense pair: `POST /optimize/defense-pair` with e.g. `{min_ovr:84, max_salary:110, max_ap:26}` → 1 solution in tests.
- Full team: `POST /optimize/full-team` with e.g. `{min_ovr:82, max_salary:110, max_ap:26}` → 1 solution (20 players, effective OVR ~1764) with current pruning.

Known limitations / next swaps
------------------------------
- Sub-positions, salary, AP are synthetic; replace the override file when real data is available.
- Event codes in combos are raw filenames from the scrape; can be mapped to human-readable names later.
- SAL/AP are included as constraints/bonuses, but not in the objective yet.
- `require_center` relies on synthetic sub-positions; real C/LW/RW are needed for accuracy.

How to swap in real data
------------------------
1) Put real attributes in an override CSV: `id, sub_position, salary, ap` (id = Skater ID for FWD/DEF, Goalie ID for G).
2) Keep combo files in v3 format (type/key). Swap to official combos if you have them; otherwise continue with the scrape-v3.
3) Adjust event buckets/salary/AP generator or remove it when official values arrive; original CSVs stay untouched.
