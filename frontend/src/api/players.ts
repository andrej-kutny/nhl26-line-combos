/**
 * Players API module
 */

import { apiGet } from './client';
import type { Player, LookupOption, DatasetStats } from './types';

export interface PlayerFilters {
  min_ovr?: number;
  max_ovr?: number;
  team?: string;
  nationality?: string;
  event?: string;
  limit?: number;
  offset?: number;
  [key: string]: string | number | boolean | undefined;
}

// Get forwards with optional filters
export function getForwards(filters?: PlayerFilters): Promise<Player[]> {
  return apiGet<Player[]>('/players/forwards', filters);
}

// Get defense players with optional filters
export function getDefense(filters?: PlayerFilters): Promise<Player[]> {
  return apiGet<Player[]>('/players/defense', filters);
}

// Get goalies with optional filters
export function getGoalies(filters?: PlayerFilters): Promise<Player[]> {
  return apiGet<Player[]>('/players/goalies', filters);
}

// Search forwards by name
export function searchForwards(q: string, filters?: PlayerFilters): Promise<Player[]> {
  return apiGet<Player[]>('/players/forwards/search', { q, ...filters });
}

// Search defense by name
export function searchDefense(q: string, filters?: PlayerFilters): Promise<Player[]> {
  return apiGet<Player[]>('/players/defense/search', { q, ...filters });
}

// Search goalies by name
export function searchGoalies(q: string, filters?: PlayerFilters): Promise<Player[]> {
  return apiGet<Player[]>('/players/goalies/search', { q, ...filters });
}

// Lookup players for autocomplete
export function lookupPlayers(
  q: string, 
  mode: 'card' | 'player' = 'card',
  position?: 'FWD' | 'DEF' | 'G'
): Promise<LookupOption[]> {
  return apiGet<LookupOption[]>('/players/lookup', { q, mode, position });
}

// Get all cards for a specific player
export function getForwardCards(playerId: number): Promise<Player[]> {
  return apiGet<Player[]>(`/players/forwards/cards/${playerId}`);
}

export function getDefenseCards(playerId: number): Promise<Player[]> {
  return apiGet<Player[]>(`/players/defense/cards/${playerId}`);
}

export function getGoalieCards(playerId: number): Promise<Player[]> {
  return apiGet<Player[]>(`/players/goalies/cards/${playerId}`);
}

// Get dataset statistics
export function getStats(): Promise<DatasetStats> {
  return apiGet<DatasetStats>('/stats/');
}

// Get available teams
export async function getTeams(): Promise<string[]> {
  const response = await apiGet<{ teams: string[] }>('/stats/teams');
  return response.teams;
}

// Get available nationalities
export async function getNationalities(): Promise<string[]> {
  const response = await apiGet<{ nationalities: string[] }>('/stats/nationalities');
  return response.nationalities;
}

// Get available events
export async function getEvents(): Promise<string[]> {
  const response = await apiGet<{ events: string[] }>('/stats/events');
  return response.events;
}
