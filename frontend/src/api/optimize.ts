/**
 * Optimization API module
 */

import { apiPost, apiGet } from './client';
import type { OptimizationRequest, OptimizationResponse } from './types';

// Optimize forward line
export function optimizeForwardLine(request: OptimizationRequest): Promise<OptimizationResponse> {
  return apiPost<OptimizationResponse>('/optimize/forward-line', request);
}

// Optimize defense pair
export function optimizeDefensePair(request: OptimizationRequest): Promise<OptimizationResponse> {
  return apiPost<OptimizationResponse>('/optimize/defense-pair', request);
}

// Optimize full team
export function optimizeFullTeam(request: OptimizationRequest): Promise<OptimizationResponse> {
  return apiPost<OptimizationResponse>('/optimize/full-team', request);
}

// Validate a user-selected line
export interface ValidateRequest {
  player_ids: number[];
  position_type: 'forward' | 'defense';
}

export interface ValidateResponse {
  valid: boolean;
  active_combos: Array<{
    id: number;
    reward_type: string;
    reward_amount: number;
    description: string;
  }>;
  total_bonus: {
    ovr: number;
    salary: number;
    ap: number;
  };
}

export function validateLine(request: ValidateRequest): Promise<ValidateResponse> {
  return apiPost<ValidateResponse>('/optimize/validate', request);
}

// Check if ASP solver is ready
export interface SolverStatus {
  asp_ready: boolean;
  message: string;
}

export function getSolverStatus(): Promise<SolverStatus> {
  return apiGet<SolverStatus>('/optimize/status');
}
