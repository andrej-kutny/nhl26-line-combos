// Player types
export interface Player {
  id: number;  // unique card ID (auto-increment)
  player_id: number;  // real player ID (shared across cards)
  first_name: string;
  last_name: string;
  img: string;
  position: 'FWD' | 'DEF' | 'G';
  salary: number;
  event: string;
  overall: number;
  nationality: string;
  league: string;
  team: string;
  weight: number;
  height: number;
}

export interface LookupOption {
  value: number;  // either card id or player_id
  value_type: 'card' | 'player';
  player_id: number;
  position: 'FWD' | 'DEF' | 'G';
  overall: number;
  event: string;
  label: string;
}

// Combo types
export interface ComboCondition {
  type: 'team' | 'nationality' | 'event';
  key: string;
}

export interface LineCombo {
  id: number;
  reward_amount: number;
  reward_type: 'OVR' | 'SAL' | 'AP';
  condition1: ComboCondition;
  condition2: ComboCondition;
  condition3?: ComboCondition;  // Only for forward combos
}

// Optimization types
export interface OptimizationConstraints {
  min_ovr?: number;
  max_salary?: number | null;
  max_ap?: number | null;
  require_center?: boolean;
  excluded_player_ids?: number[];
  required_team?: string | null;
  required_nationality?: string | null;
  required_event?: string | null;
}

export interface OptimizationRequest {
  constraints?: OptimizationConstraints;
  optimization_target?: 'ovr' | 'salary' | 'ap' | 'balanced';
  num_solutions?: number;
}

export interface ActiveCombo {
  id: number;
  reward_type: 'OVR' | 'SAL' | 'AP';
  reward_amount: number;
  description: string;
}

export interface LineSolution {
  rank: number;
  players: Player[];
  total_base_ovr: number;
  ovr_bonus: number;
  effective_ovr: number;
  total_salary: number;
  total_ap: number;
  active_combos: ActiveCombo[];
}

export interface OptimizationResponse {
  success: boolean;
  message: string;
  solutions: LineSolution[];
  computation_time_ms: number;
  candidates_evaluated: number;
}

// Goal 1 / Best Lines types
export interface Goal1Run {
  id: number;
  run_timestamp: string;
  position_type: 'forward' | 'defense';
  optimization_mode: 'ovr' | 'sal' | 'ap' | 'ovr_sal' | 'ovr_sal_ap';
  parameters: Record<string, unknown>;
  dataset_hash?: string;
}

export interface PlayerInfo {
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

export interface ConcreteLineResponse {
  id: number;
  players: PlayerInfo[];
  activated_combo_ids: number[];
  total_ovr: number;
  total_salary: number;
  total_ap: number;
  ranking_score: number;
}

export interface BestLinesResponse {
  success: boolean;
  run: Goal1Run | null;
  position_type: string;
  optimization_mode: string;
  total_lines: number;
  lines: ConcreteLineResponse[];
}

// Stats types
export interface DatasetStats {
  players: {
    forwards: number;
    defense: number;
    goalies: number;
    total: number;
  };
  combos: {
    forward_combos: number;
    defense_combos: number;
    total: number;
  };
  teams: string[];
  nationalities: string[];
}

// API response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}
