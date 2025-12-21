% Common ASP rules for both Forward and Defense optimizations

% ------------------------------------------------------------------------------
% Player Extraction
% ------------------------------------------------------------------------------
% Input format: player(CardID, PlayerID, Nationality, Team, Event, Overall, Salary)
% Generate attributes
id(CardID) :- player(CardID, _, _, _, _, _, _).
player_obj(PlayerID) :- player(_, PlayerID, _, _, _, _, _).
has_card(PlayerID, CardID) :- player(CardID, PlayerID, _, _, _, _, _).
nationality(PlayerID, Nat) :- player(_, PlayerID, Nat, _, _, _, _).
team(CardID, Team) :- player(CardID, _, _, Team, _, _, _).
card_type(CardID, Event) :- player(CardID, _, _, _, Event, _, _).
ovr(CardID, Ovr) :- player(CardID, _, _, _, _, Ovr, _).
salary(CardID, Sal) :- player(CardID, _, _, _, _, _, Sal).

% Attribute Matching
% Matches a CardID against a Requirement (e.g., team("DET"))
player_match(CardID, team(T)) :- team(CardID, T).
player_match(CardID, event(E)) :- card_type(CardID, E).
player_match(CardID, nationality(N)) :- has_card(P, CardID), nationality(P, N).

% Aliases removed as per request
% Only team(), event(), and nationality() are supported.

% ------------------------------------------------------------------------------
% Dynamic Boost Types
% ------------------------------------------------------------------------------
% Extract boost types from combo definitions if present
boost_type(Type) :- forward_combo(_, _, Type, _, _, _).
boost_type(Type) :- defense_combo(_, _, Type, _, _).

