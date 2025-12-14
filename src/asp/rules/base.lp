% Shared ASP rules for matching and constraints.

% Player facts:
%   player(CardID, OVR, Team, Nationality, Event).
%   card_player(CardID, PlayerID).
% Team/Nationality/Event are strings, normalized to lowercase.

ovr(P, OVR) :- player(P, OVR, _, _, _).

matches(P, "team", K) :- player(P, _, Team, _, _), K = Team.
matches(P, "nationality", K) :- player(P, _, _, Nat, _), K = Nat.
matches(P, "event", K) :- player(P, _, _, _, Ev), K = Ev.

salary_val(P, S) :- salary(P, S).
salary_val(P, 0) :- not salary(P, _), player(P, _, _, _, _).

ap_val(P, A) :- ap(P, A).
ap_val(P, 0) :- not ap(P, _), player(P, _, _, _, _).

% Generic constraints (provided as facts from Python)
:- excluded(P), select(P, _).

% Prevent selecting two different cards for the same underlying player
:- select(C1, _), select(C2, _), C1 != C2, card_player(C1, P), card_player(C2, P).

:- min_ovr(M), select(P, _), ovr(P, OVR), OVR < M.

:- required_team(T), select(P, _), player(P, _, Team, _, _), Team != T.
:- required_nationality(N), select(P, _), player(P, _, _, Nat, _), Nat != N.
:- required_event(E), select(P, _), player(P, _, _, _, Ev), Ev != E.

% Sub-position / center requirement (synthetic)
center(P) :- sub_pos(P, "c").
:- require_center, not 1 { select(P, _): center(P) }.
