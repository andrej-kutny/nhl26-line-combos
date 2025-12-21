/**
 * Line Combos API module
 */

import { apiGet } from './client';
import type { LineCombo, Player } from './types';

// Get all forward line combos
export function getForwardCombos(): Promise<LineCombo[]> {
  return apiGet<LineCombo[]>('/combos/forward');
}

// Get all defense line combos
export function getDefenseCombos(): Promise<LineCombo[]> {
  return apiGet<LineCombo[]>('/combos/defense');
}

// Get players matching a specific combo
export function getMatchingPlayers(comboId: number): Promise<Player[]> {
  return apiGet<Player[]>(`/combos/forward/${comboId}/matching-players`);
}
