export type Pos = 'fwd' | 'def';

export type OptimizationTarget = 'ovr' | 'salary' | 'ap' | 'balanced';

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
  constraints: OptimizationConstraints;
  optimization_target: OptimizationTarget;
  num_solutions: number;
}

export interface Player {
  id: number;
  player_id?: number;
  first_name?: string;
  last_name?: string;
  team?: string;
  nationality?: string;
  event?: string;
  overall?: number;
  salary?: number;
  position?: string;
}

export interface ActiveCombo {
  id: number;
  reward_type: string;
  reward_amount: number;
  description?: string;
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

export interface StageBDemoPayload {
  schema_version: number;
  pos: Pos;
  combo_ids: number[];
  constraints?: Record<string, unknown>;
  count: number;
  solutions: LineSolution[];
}

