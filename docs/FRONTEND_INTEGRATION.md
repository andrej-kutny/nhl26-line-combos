# Frontend Integration Guide

This guide explains how to connect frontend application to the API.

**Target frontend**: Angular v21

## API Base URL

```
Development: http://localhost:8000
```

## Quick Start

### 1. Start the API Server

```bash
cd nhl26-line-combos
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

### 2. Verify API is Running

```bash
curl http://localhost:8000/health
# {"status":"healthy","data":"loaded"}
```

### 3. Access API Documentation

Open http://localhost:8000/docs for interactive Swagger UI.

## CORS

The API allows requests from any origin during development. For production, update `src/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend URL
    ...
)
```

## API Endpoints Reference

### Get All Forwards

```javascript
// GET /players/forwards?min_ovr=80&limit=50
const response = await fetch('http://localhost:8000/players/forwards?min_ovr=80&limit=50');
const forwards = await response.json();

// Response: Array of players
[
  {
    "id": 2029,
    "first_name": "SERGEI",
    "last_name": "FEDOROV",
    "event": "ICON",
    "overall": 86,
    "nationality": "Russia",
    "league": "NHLAA",
    "team": "DET",
    "position": "FWD"
  },
  ...
]
```

### Search Players

```javascript
// GET /players/search?q=gretzky&min_ovr=80&event=ICON
const response = await fetch('http://localhost:8000/players/search?q=gretzky&min_ovr=80&event=ICON');
const results = await response.json();

// Response: Array of {player, position}
[
  {
    "player": { "id": 123, "first_name": "WAYNE", "last_name": "GRETZKY", ... },
    "position": "FWD"
  }
]
```

### Dropdown / Autocomplete (Recommended)

Use `/players/lookup` to build dynamic dropdowns that match UX requirement:
- card mode label: `"{First} {Last} {OVR} - {EVENT} - {Position}"`
- player mode label: `"{First} {Last} *"`

```javascript
// Card-level options (choose by card id)
// GET /players/lookup?q=gretzky&mode=card&position=FWD
const cards = await fetch('http://localhost:8000/players/lookup?q=gretzky&mode=card&position=FWD').then(r => r.json());

// Player-level options (choose by player_id for any card)
// GET /players/lookup?q=gretzky&mode=player
const players = await fetch('http://localhost:8000/players/lookup?q=gretzky&mode=player').then(r => r.json());
```

### Get Line Combinations

```javascript
// GET /combos/forward?reward_type=OVR&min_reward=2
const response = await fetch('http://localhost:8000/combos/forward?reward_type=OVR&min_reward=2');
const combos = await response.json();

// Response: Array of combos
[
  {
    "id": 0,
    "reward_amount": 2,
    "reward_type": "OVR",
    "condition1": { "type": "team", "key": "TBL" },
    "condition2": { "type": "event", "key": "COM" },
    "condition3": { "type": "team", "key": "WSH" }
  },
  ...
]
```

### Optimize Forward Line

```javascript
// POST /optimize/forward-line
const response = await fetch('http://localhost:8000/optimize/forward-line', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    constraints: {
      min_ovr: 80,
      max_salary: null,
      max_ap: null,
      require_center: false,
      excluded_player_ids: [],
      required_team: null,
      required_nationality: null,
      required_event: null
    },
    optimization_target: "ovr",  // "ovr" | "salary" | "ap" | "balanced"
    num_solutions: 5
  })
});

const result = await response.json();

// Response
{
  "success": true,
  "message": "Found 5 solution(s)",
  "solutions": [
    {
      "rank": 1,
      "players": [
        { "id": 2029, "first_name": "SERGEI", "last_name": "FEDOROV", "overall": 86, ... },
        { "id": 1063, "first_name": "PLAYER", "last_name": "TWO", "overall": 86, ... },
        { "id": 2128, "first_name": "PLAYER", "last_name": "THREE", "overall": 86, ... }
      ],
      "total_base_ovr": 258,
      "ovr_bonus": 2,
      "effective_ovr": 260,
      "total_salary": 0,
      "total_ap": 0,
      "active_combos": [
        { "id": 5, "reward_type": "OVR", "reward_amount": 2, "description": "team=DET + event=ICON + nationality=RUSSIA" }
      ]
    },
    ...
  ],
  "computation_time_ms": 145,
  "candidates_evaluated": 1766
}
```

### Validate User Line

```javascript
// POST /optimize/validate?position_type=forward
const response = await fetch('http://localhost:8000/optimize/validate?position_type=forward', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify([2029, 1437, 1221])  // Array of player IDs
});

const result = await response.json();

// Response
{
  "valid": true,
  "players": [
    { "id": 2029, "name": "SERGEI FEDOROV", "overall": 86, "team": "DET", "nationality": "Russia" },
    ...
  ],
  "total_base_ovr": 254,
  "ovr_bonus": 2,
  "effective_ovr": 256,
  "active_combos": [
    { "id": 5, "reward_type": "OVR", "reward_amount": 2 }
  ]
}
```

### Get Statistics

```javascript
// GET /stats/
const response = await fetch('http://localhost:8000/stats/');
const stats = await response.json();

// Response
{
  "players": { "forwards": 1768, "defense": 890, "goalies": 305, "total": 2963 },
  "unique_players": { "forwards": 1125, "defense": 567, "goalies": 204 },
  "combos": { "forward_combos": 54, "defense_combos": 56, "total": 110 },
  "teams": ["ANA", "BOS", "BUF", ...],
  "nationalities": ["CANADA", "CZECHIA", "FINLAND", ...],
  "events": ["ALUM", "BA", "CAP", ...]
}
```

### Get Filter Options

```javascript
// For dropdown menus
const teams = await fetch('http://localhost:8000/stats/teams').then(r => r.json());
const nationalities = await fetch('http://localhost:8000/stats/nationalities').then(r => r.json());
const events = await fetch('http://localhost:8000/stats/events').then(r => r.json());
```

## TypeScript Types

If using TypeScript, here are the main types:

```typescript
interface Player {
  id: number;  // unique card ID (auto-increment)
  player_id: number;  // real player ID (shared across cards)
  first_name: string;
  last_name: string;
  img: string;
  position?: string;
  salary: number;
  event: string;
  overall: number;
  nationality: string;
  league: string;
  team: string;
  weight: number;
  height: number;
  position: 'FWD' | 'DEF' | 'G';
}

interface LookupOption {
  value: number;  // either card id or player_id
  value_type: 'card' | 'player';
  player_id: number;
  position: 'FWD' | 'DEF' | 'G';
  overall: number;
  event: string;
  position?: string;
  label: string;
}

interface ComboCondition {
  type: 'team' | 'nationality' | 'event';
  key: string;
}

interface LineCombo {
  id: number;
  reward_amount: number;
  reward_type: 'OVR' | 'SAL' | 'AP';
  condition1: ComboCondition;
  condition2: ComboCondition;
  condition3?: ComboCondition;  // Only for forward combos
}

interface OptimizationConstraints {
  min_ovr?: number;
  max_salary?: number | null;
  max_ap?: number | null;
  require_center?: boolean;
  excluded_player_ids?: number[];
  required_team?: string | null;
  required_nationality?: string | null;
  required_event?: string | null;
}

interface OptimizationRequest {
  constraints?: OptimizationConstraints;
  optimization_target?: 'ovr' | 'salary' | 'ap' | 'balanced';
  num_solutions?: number;
}

interface ActiveCombo {
  id: number;
  reward_type: 'OVR' | 'SAL' | 'AP';
  reward_amount: number;
  description: string;
}

interface LineSolution {
  rank: number;
  players: Player[];
  total_base_ovr: number;
  ovr_bonus: number;
  effective_ovr: number;
  total_salary: number;
  total_ap: number;
  active_combos: ActiveCombo[];
}

interface OptimizationResponse {
  success: boolean;
  message: string;
  solutions: LineSolution[];
  computation_time_ms: number;
  candidates_evaluated: number;
}
```

## Angular example (HttpClient)

```typescript
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class NhlApi {
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private readonly http: HttpClient) {}

  lookupPlayers(q: string, mode: 'card' | 'player' = 'card') {
    const params = new HttpParams().set('q', q).set('mode', mode);
    return this.http.get(`${this.baseUrl}/players/lookup`, { params });
  }

  optimizeForwardLine(body: unknown) {
    return this.http.post(`${this.baseUrl}/optimize/forward-line`, body);
  }
}
```

## Error Handling

The API returns standard HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 500 | Server error |
| 501 | Not implemented (ASP solver pending) |

Handle errors in frontend:

```javascript
async function apiCall(url, options = {}) {
  const response = await fetch(url, options);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API request failed');
  }
  
  return response.json();
}
```

## Checking ASP Solver Status

Before using optimization endpoints, check if the ASP solver is ready:

```javascript
const status = await fetch('http://localhost:8000/optimize/status').then(r => r.json());

if (status.solver_type === 'placeholder') {
  console.warn('ASP solver not yet implemented - using placeholder');
}

// Check which features are available
if (status.features.full_team) {
  // Full team optimization is available
}
```

## Best Lines Endpoints (Goal 1 Results)

These endpoints expose pre-computed optimal line combinations from the Goal 1 pipeline.

### List Available Runs

```javascript
// GET /best/runs?position_type=forward&optimization_mode=ovr
const response = await fetch('http://localhost:8000/best/runs?position_type=forward');
const { runs, total } = await response.json();

// Response
{
  "runs": [
    {
      "id": 1,
      "run_timestamp": "2025-12-18T10:30:00Z",
      "position_type": "forward",
      "optimization_mode": "ovr",
      "parameters": { "k": 200 }
    }
  ],
  "total": 1
}
```

### Get Best Lines

```javascript
// GET /best/{pos}/{mode}?limit=10
const response = await fetch('http://localhost:8000/best/forward/ovr?limit=10');
const result = await response.json();

// Response
{
  "success": true,
  "run": {
    "id": 1,
    "run_timestamp": "2025-12-18T10:30:00Z",
    "position_type": "forward",
    "optimization_mode": "ovr"
  },
  "position_type": "forward",
  "optimization_mode": "ovr",
  "total_lines": 150,
  "lines": [
    {
      "id": 1,
      "players": [
        {
          "id": 123,
          "player_id": 456,
          "first_name": "Connor",
          "last_name": "McDavid",
          "overall": 99,
          "team": "EDM",
          "nationality": "CANADA",
          "event": "TOTY",
          "position": "FWD",
          "salary": 5000000
        }
        // ... more players
      ],
      "activated_combo_ids": [1, 5, 12],
      "total_ovr": 292,
      "total_salary": 15000000,
      "total_ap": 6,
      "ranking_score": 298.0
    }
    // ... more lines
  ]
}
```

### Get Summary (Lighter Response)

```javascript
// GET /best/{pos}/{mode}/summary
const response = await fetch('http://localhost:8000/best/forward/ovr/summary');
const summary = await response.json();

// Response
{
  "has_results": true,
  "position_type": "forward",
  "optimization_mode": "ovr",
  "run": {
    "id": 1,
    "timestamp": "2025-12-18T10:30:00Z",
    "parameters": { "k": 200 }
  },
  "total_lines": 150,
  "top_scores": [298.0, 295.5, 294.0]
}
```

### Best Lines TypeScript Types

```typescript
interface Goal1Run {
  id: number;
  run_timestamp: string;
  position_type: 'forward' | 'defense';
  optimization_mode: 'ovr' | 'sal' | 'ap' | 'ovr_sal' | 'ovr_sal_ap';
  parameters: Record<string, unknown>;
  dataset_hash?: string;
}

interface PlayerInfo {
  id: number;
  player_id: number;
  first_name: string;
  last_name: string;
  overall: number;
  team: string;
  nationality: string;
  event: string;
  position: string;
  salary: number;
}

interface ConcreteLineResponse {
  id: number;
  players: PlayerInfo[];
  activated_combo_ids: number[];
  total_ovr: number;
  total_salary: number;
  total_ap: number;
  ranking_score: number;
}

interface BestLinesResponse {
  success: boolean;
  run: Goal1Run | null;
  position_type: string;
  optimization_mode: string;
  total_lines: number;
  lines: ConcreteLineResponse[];
}
```

## Questions?

Contact the API team for:
- New endpoints
- Data format changes
- Authentication requirements

