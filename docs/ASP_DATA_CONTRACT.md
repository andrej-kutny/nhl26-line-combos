# ASP data contract (backend ↔ solver)

This document describes a minimal, stable contract for exchanging data with the
ASP solver layer. The goal is to make integration testable and independent of
any particular dataset snapshot (CSV vs SQLite row IDs).

## 1) Facts (input to ASP)

### Players

Required:

```
player(CardID, OVR, Team, Nationality, Event).
```

Optional (but strongly recommended):

```
card_player(CardID, PlayerID).
```

Optional:

```
salary(CardID, Salary).
ap(CardID, AP).
```

Notes:
- `CardID` is the concrete selectable card identifier (string or int).
- `PlayerID` is the canonical “person” id (same for multiple cards of the same player).
- `Team`, `Nationality`, `Event` are compared as strings.

### Combos

Forwards (3 conditions):

```
fwd_combo(ComboID, RewardAmount, RewardType, T1, K1, T2, K2, T3, K3).
```

Defense (2 conditions):

```
def_combo(ComboID, RewardAmount, RewardType, T1, K1, T2, K2).
```

Where each `(Tn, Kn)` is one condition such as:
- `("team","chi")`
- `("nationality","canada")`
- `("event","fant")`

`RewardType` is one of: `ovr`, `sal`, `ap` (lowercase in ASP layer).

### Stage B requirements

Stage B enumeration enforces a required set of combo IDs:

```
required_combo(ComboID).
```

Stage B semantics:
- A single selected line/pair may activate `0..N` combos simultaneously.
- Each `required_combo/1` must be activated by the selected line/pair.

## 2) Solver outputs (atoms)

### Stage B (enumeration)

Stage B rules show:

```
select(CardID, Slot).
combo_active(ComboID).
total_base_ovr(N).
total_ovr_bonus(N).
total_salary(N).
total_salary_bonus(N).
total_ap(N).
total_ap_bonus(N).
```

Interpretation:
- `select/2` gives the chosen lineup (slots depend on program: 1..3 for forward line, 1..2 for defense pair).
- `combo_active/1` includes *all* activated combos for the chosen line/pair (not only required combos).
- “effective” caps are computed as:
  - `salary_eff = total_salary - total_salary_bonus`
  - `ap_eff = total_ap - total_ap_bonus`

## 3) JSON output (recommended for persistence)

Stage B tooling can export a self-contained JSON payload (see `docs/GOAL_1.md`).
This is recommended for persistence and API serving because it decouples the
frontend from ASP atoms.

## 4) ID stability note

Combo numeric IDs can differ across snapshots (e.g. SQLite row IDs vs CSV `combo_id`).
For cross-snapshot comparisons, prefer matching combos by their condition tuples
`(T1,K1,...)` rather than only by numeric id.

