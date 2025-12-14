# Frontend Integration Guide

This guide explains how to connect your frontend application to the API.

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
    allow_origins=["http://localhost:5173"],  # Your frontend URL
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
// GET /players/search?q=gretzky
const response = await fetch('http://localhost:8000/players/search?q=gretzky');
const results = await response.json();

// Response: Array of {player, position}
[
  {
    "player": { "id": 123, "first_name": "WAYNE", "last_name": "GRETZKY", ... },
    "position": "FWD"
  }
]
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
  id: number;
  first_name: string;
  last_name: string;
  event: string;
  overall: number;
  nationality: string;
  league: string;
  team: string;
  position: 'FWD' | 'DEF' | 'G';
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
  excluded_player_ids?: string[];
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

## React Example

```jsx
import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

function LineOptimizer() {
  const [constraints, setConstraints] = useState({
    min_ovr: 80,
    excluded_player_ids: [],
  });
  const [solutions, setSolutions] = useState([]);
  const [loading, setLoading] = useState(false);

  const optimize = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/optimize/forward-line`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          constraints,
          optimization_target: 'ovr',
          num_solutions: 5,
        }),
      });
      const data = await response.json();
      setSolutions(data.solutions);
    } catch (error) {
      console.error('Optimization failed:', error);
    }
    setLoading(false);
  };

  return (
    <div>
      <h1>NHL 26 Line Optimizer</h1>
      
      <div>
        <label>
          Min OVR:
          <input
            type="range"
            min="70"
            max="95"
            value={constraints.min_ovr}
            onChange={(e) => setConstraints({ ...constraints, min_ovr: +e.target.value })}
          />
          {constraints.min_ovr}
        </label>
      </div>
      
      <button onClick={optimize} disabled={loading}>
        {loading ? 'Optimizing...' : 'Find Optimal Line'}
      </button>
      
      {solutions.map((sol) => (
        <div key={sol.rank} className="solution">
          <h3>Solution #{sol.rank}</h3>
          <p>Effective OVR: {sol.effective_ovr} (Base: {sol.total_base_ovr} + Bonus: {sol.ovr_bonus})</p>
          <ul>
            {sol.players.map((p) => (
              <li key={p.id}>
                {p.first_name} {p.last_name} - OVR {p.overall} ({p.team})
              </li>
            ))}
          </ul>
          {sol.active_combos.length > 0 && (
            <div>
              <strong>Active Combos:</strong>
              <ul>
                {sol.active_combos.map((c) => (
                  <li key={c.id}>+{c.reward_amount} {c.reward_type}: {c.description}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default LineOptimizer;
```

## Vue Example

```vue
<script setup>
import { ref } from 'vue';

const API_BASE = 'http://localhost:8000';

const minOvr = ref(80);
const solutions = ref([]);
const loading = ref(false);

async function optimize() {
  loading.value = true;
  try {
    const response = await fetch(`${API_BASE}/optimize/forward-line`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        constraints: { min_ovr: minOvr.value },
        optimization_target: 'ovr',
        num_solutions: 5,
      }),
    });
    const data = await response.json();
    solutions.value = data.solutions;
  } catch (error) {
    console.error('Optimization failed:', error);
  }
  loading.value = false;
}
</script>

<template>
  <div>
    <h1>NHL 26 Line Optimizer</h1>
    
    <div>
      <label>
        Min OVR: {{ minOvr }}
        <input type="range" v-model.number="minOvr" min="70" max="95" />
      </label>
    </div>
    
    <button @click="optimize" :disabled="loading">
      {{ loading ? 'Optimizing...' : 'Find Optimal Line' }}
    </button>
    
    <div v-for="sol in solutions" :key="sol.rank" class="solution">
      <h3>Solution #{{ sol.rank }}</h3>
      <p>Effective OVR: {{ sol.effective_ovr }}</p>
      <ul>
        <li v-for="p in sol.players" :key="p.id">
          {{ p.first_name }} {{ p.last_name }} - OVR {{ p.overall }}
        </li>
      </ul>
    </div>
  </div>
</template>
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

Handle errors in your frontend:

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

## Questions?

Contact the API team for:
- New endpoints
- Data format changes
- Authentication requirements
