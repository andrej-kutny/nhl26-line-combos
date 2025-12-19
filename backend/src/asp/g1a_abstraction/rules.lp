#const w_ovr = 1.
#const w_ap = 1.
#const w_sal = 1.
multiplier("OVR", w_ovr).
multiplier("AP", w_ap).
multiplier("SAL", w_sal).

% Generate attributes for each player
% Allow 0 or 1 attribute per type.
{ player_attr(P, team(T)) : is_team(T) } <= 1 :- player(P).
{ player_attr(P, event(E)) : is_event(E) } <= 1 :- player(P).
{ player_attr(P, nationality(N)) : is_nationality(N) } <= 1 :- player(P).

% Match helper
match(P, Req) :- player_attr(P, Req).

% Constraint: An attribute cannot be assigned if it is not used in ANY active combo.
:- player_attr(P, Req), not used(P, Req).

% Symmetry Breaking: Force P < P+1 lexicographically for any adjacent players
has_team(P) :- player_attr(P, team(_)).
has_event(P) :- player_attr(P, event(_)).
has_nationality(P) :- player_attr(P, nationality(_)).

% Order: No Team < Team(A) < Team(B)
:- player(P), player(P+1), has_team(P), not has_team(P+1).
:- player(P), player(P+1), player_attr(P, team(T1)), player_attr(P+1, team(T2)), T1 > T2.

% If Teams equal, compare Events
same_team(P, P1) :- player(P), player(P1), P1=P+1, player_attr(P, team(T)), player_attr(P1, team(T)).
same_team(P, P1) :- player(P), player(P1), P1=P+1, not has_team(P), not has_team(P1).

:- player(P), player(P+1), same_team(P, P+1), has_event(P), not has_event(P+1).
:- player(P), player(P+1), same_team(P, P+1), player_attr(P, event(E1)), player_attr(P+1, event(E2)), E1 > E2.

% If Teams and Events equal, compare Nationalities
same_event(P, P1) :- player(P), player(P1), P1=P+1, player_attr(P, event(E)), player_attr(P1, event(E)).
same_event(P, P1) :- player(P), player(P1), P1=P+1, not has_event(P), not has_event(P1).

:- player(P), player(P+1), same_team(P, P+1), same_event(P, P+1), has_nationality(P), not has_nationality(P+1).
:- player(P), player(P+1), same_team(P, P+1), same_event(P, P+1), player_attr(P, nationality(N1)), player_attr(P+1, nationality(N2)), N1 > N2.

#show player_attr/2.
#show total_reward/1.
