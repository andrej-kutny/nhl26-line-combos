# Goal 1 — Data-driven line combination discovery

This document specifies **Goal 1** end-to-end: how the system discovers high-value line combinations, how ASP and the backend cooperate, and what artifacts (tasks, files, and storage) are produced.

## Problem statement

Goal 1 is triggered when:
- new players/cards are added to the database, or
- new line combinations are added to the database.

The goal is to generate and persist a **ranked set of candidate lines** (forward lines and defense pairs) for different optimization modes:
- OVR only
- SAL only
- AP only
- weighted mixes (OVR+SAL, OVR+SAL+AP)

### Key idea: 2-stage pipeline

1. **Stage A (abstract / combo-first)**: optimize over *line combination templates* (no real players yet).
2. **Stage B (grounding / player-aware)**: fetch a limited player pool that matches Stage A’s attributes, then enumerate **all concrete lines** that realize those combos.

This makes the expensive “concrete line enumeration” step run only on a small, high-signal candidate set.

---

## Data model inputs

### Line combination templates

Forward combination template (3 entries):
- `forward_combination(id, reward_amount, reward_type, entry1, entry2, entry3)`

Defense combination template (2 entries):
- `defense_combination(id, reward_amount, reward_type, entry1, entry2)`

Each entry is one of:
- `nationality(x)` or `team(x)` or `event(x)`

### Player/card facts

For Goal 1 grounding we use player cards from SQLite with at least:
- `id` (unique card ID), `player_id` (real player ID)
- `team`, `nationality`, `event`
- `overall`, `salary`, `ap` (if AP is modeled)

---

## Pipeline overview

```
SQLite              Backend                  ASP
  │                    │                      │ 
  │ Fetch line data    │                      │─ ─ ─ ─ 
  │<───────────────────│                      │ Stage │
  │───────────────────>│ get combo candidates │   A 
  │                    │─────────────────────>│       │
  │                    │<─────────────────────│─ ─ ─ ─  
  │                  ──│                      │─ ─ ─ ─ 
  │        For each │  │ get combo player     │       │
  │        candidate│  │ alternatives         │ Stage
  │                 │  │─────────────────────>│   B   │
  │  store result   │  │<─────────────────────│       
  │<────────────────+──│                      │       │
  │                 │  │                      │─ ─ ─ ─
  │                  ─>│                      │

```

---

## Stage A — Abstract optimization (combo-first)

### What Stage A optimizes

Backend creates reward-mode-specific ASP inputs (examples):
- `fwd_ovr_combinations.lp`
- `fwd_sal_combinations.lp`
- `fwd_ap_combinations.lp`
- `def_ovr_combinations.lp`
- `def_sal_combinations.lp`
- `def_ap_combinations.lp`

Clingo then returns the **top K abstract solutions** (e.g., `K=200`), where each solution contains:
- a set of combinations it uses,
- total gain broken down by reward types: `gain_ovr`, `gain_sal`, `gain_ap`
  - i.e. if optimizing SAL only, then `gain_ovr = 0` and `gain_ap = 0`.

---

## Stage B — Grounding (player-aware enumeration)

### Backend player candidate query

For each abstract solution from Stage A:
1. Extract unique keys appearing in its combos:
   - sets of size in range `0..3`, for each teams, nationalities and events
2. Query SQLite for candidate player cards:
   - Select players that match **at least one** key from any set
   - Compute `match_count` in range `0..3`:
     - +1 if player.team ∈ teams_set
     - +1 if player.nationality ∈ nationalities_set
     - +1 if player.event ∈ events_set
   - Sorting:
     - primary: `match_count DESC`
     - secondary: `overall DESC`
   - `LIMIT 100`

### Stage B solver requirements

Given:
- candidate players (with `player_id` and attributes)
- the specific combos for solution

Clingo enumerates **all concrete lines** that satisfy all combos, with rules:
- **Uniqueness**: do not use the same `player_id` more than once in a line.
- **Symmetry**
  - (forward lines): `{p1,p2,p3} == {p3,p1,p2}` should be treated as the same line.
  - (defense lines): `{p1,p2} == {p2,p1}` should be treated as the same line.

Stage B output should include:
- all results
- selected players per line

### Stage B output contract (JSON)

The Stage B enumerator should be able to write results as a self-contained JSON artifact that can be persisted in SQLite and served via API without requiring any additional context.

At minimum, the JSON file MUST follow this structure:

- `schema_version` (int): Output schema version for forward compatibility.
- `pos` (string): `"fwd"` or `"def"`.
- `combo_ids` (array[int]): The required combo IDs passed to Stage B.
- `constraints` (object): The constraints used for the run (same fields as `OptimizationConstraints`).
- `count` (int): Number of returned solutions.
- `solutions` (array[object]): List of solutions, where each solution contains:
  - `rank` (int)
  - `players` (array[object]): concrete card selection (must include card `id` and canonical `player_id`)
  - `total_base_ovr`, `ovr_bonus`, `effective_ovr`
  - `total_salary`, `total_ap`
  - `active_combos` (array[object]): all combos activated by this line/pair, including `reward_type`, `reward_amount` and a human-readable `description`

Notes:
- IDs may differ between CSV and SQLite snapshots (e.g. SQLite row IDs vs CSV `combo_id`). For cross-snapshot comparisons, match combos by their `(type,key)` conditions, which are also exposed in `active_combos[].description`.
- Combo activation semantics are: any single line/pair may activate `0..N` combos simultaneously, while each combo can be activated at most once globally in the team context.

---

## Storage (SQLite) — what Goal 1 persists

Recommended persisted artifacts:
- **Goal 1 run metadata**
  - timestamp, dataset version/hash, parameters (K, LIMIT, weights, mode)
- **Abstract solutions (Stage A)**
  - selected combo IDs + gains per reward type
- **Concrete lines (Stage B)**
  - line type, player_ids, activated combos, gains, and ranking score

---

## Task list (Goal 1)

Task naming: `${'A' | 'B' | 'F'}G1 ${subject}`

### Backend (B)

- **BG1 Create SQLite database with data from the dataset**
  - **Goal**: Create the SQLite schema and ingestion pipeline for players/cards and combo templates.
  - **Deliverables**:
    - tables for player cards (forwards/defense/goalies) and for combo templates
    - ingestion job: CSV → SQLite (idempotent)
  - **Acceptance**:
    - a fresh DB can be built from `backend/data/*.csv`
    - combo templates are queryable by line type and reward type

- **BG1 Fetch SQLite data and send them in correct format to ASP (Stage A input builder)**
  - **Goal**: Build mode-specific ASP files (or an in-memory program) for Stage A.
  - **Deliverables**:
    - file(s): `<pos>_<type>_combinations.lp` where `<type>` is `ap` or `sal` or `ovr`, `<pos>` is `fwd` or `def`
    - consistent output contract requested from Stage A
  - **Acceptance**:
    - changing combos in SQLite changes the generated ASP input without code changes

- **BG1 Process results from AG1 Line combinations optimisation and prepare Stage B inputs**
  - **Goal**: Parse Stage A top-K solutions and build the per-solution player candidate pool.
  - **Deliverables**:
    - extractor: combos → `{teams,nats,events}`
    - SQLite query: ranked player candidates (`match_count`, `overall`) with `LIMIT 100`
    - Stage B input builder per solution
  - **Acceptance**:
    - candidate query ranking matches spec (match_count primary, overall secondary)

- **BG1 Process results from AG1 Find all line combinations… and store in database**
  - **Goal**: Persist Stage B concrete lines and their metadata.
  - **Deliverables**:
    - DB tables for Goal 1 results
    - deduping rules (avoid duplicates across runs, or store run_id)
  - **Acceptance**:
    - results can be reproduced and queried by mode/run/line type

- **BG1 Create endpoint to show results of Goal 1**
  - **Goal**: Expose persisted results to frontend.
  - **Deliverables**:
    - `GET /best/{pos}/{type}`
      - `{pos}`: `forward` or `defense`
      - `{type}`: `sal` or `ovr` or `ap` or `sal_ovr` or `sal_ovr_ap`
  - **Acceptance**:
    - endpoint returns stable ordering and is UI-ready

### ASP (A)

- **AG1 Line combinations optimisation (abstract from players db)**
  - **Goal**: Stage A solver that selects top-K abstract combo solutions for a requested optimization mode.
  - **Deliverables**:
    - ASP rules for each mode (or a shared rule file parameterized by mode/weights)
    - outputs: used combos + gain breakdown
  - **Acceptance**:
    - returns top-K (e.g., 200) solutions with deterministic tie-breaking

- **AG1 Find all line combinations that could be used based on players data**
  - **Goal**: Stage B solver that enumerates all concrete lines using the candidate player pool and Stage A combos.
  - **Deliverables**:
    - forward line enumeration with symmetry breaking (`p1<p2<p3`)
    - defense pair enumeration with symmetry breaking (`p1<p2`)
    - uniqueness of `player_id` enforced
  - **Acceptance**:
    - all returned lines are unique up to permutation
    - no player_id repeated within a line

### Frontend (F)

Low priority.

- **FG1 Goal 1 results page**
  - **Goal**: UI to explore persisted Goal 1 results.
  - **Deliverables**:
    - filters: line type (forward/defense), mode (ovr/sal/ap/weighted), top-N
    - table/list rendering of lines and their gains
  - **Acceptance**:
    - user can quickly identify what players to target to activate high-value combos

---

## Notes / open decisions

- **Weights**:
  - forward: `ovr_weight=3`, `sal_weight=1`
  - defense: `ovr_weight=2`, `sal_weight=1`
  - `ap_weight=1` when included
- **“Feasibility filter”**:
  - implemented implicitly by Stage B (only lines that exist in candidate players are returned)
  - Stage A is allowed to be “combo-only” and over-generate, because Stage B will ground it.

