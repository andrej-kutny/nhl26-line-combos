/**
 * Best Lines (Goal 1 Results) API module
 */

import { apiGet } from './client';
import type { Goal1Run, BestLinesResponse } from './types';

export interface RunListResponse {
  runs: Goal1Run[];
  total: number;
}

// List all Goal 1 runs
export function listRuns(
  position_type?: 'forward' | 'defense',
  optimization_mode?: string
): Promise<RunListResponse> {
  return apiGet<RunListResponse>('/best/runs', { position_type, optimization_mode });
}

// Get best lines for a position and optimization mode
export function getBestLines(
  position: 'forward' | 'defense',
  mode: 'ovr' | 'sal' | 'ap' | 'ovr_sal' | 'ovr_sal_ap',
  options?: {
    run_id?: number;
    limit?: number;
    offset?: number;
  }
): Promise<BestLinesResponse> {
  return apiGet<BestLinesResponse>(`/best/${position}/${mode}`, options);
}

// Get summary for best lines
export interface BestLinesSummary {
  success: boolean;
  run: Goal1Run | null;
  total_lines: number;
  top_scores: number[];
}

export function getBestLinesSummary(
  position: 'forward' | 'defense',
  mode: 'ovr' | 'sal' | 'ap' | 'ovr_sal' | 'ovr_sal_ap'
): Promise<BestLinesSummary> {
  return apiGet<BestLinesSummary>(`/best/${position}/${mode}/summary`);
}
