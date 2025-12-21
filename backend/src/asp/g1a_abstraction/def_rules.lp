% We need exactly 2 players for one defense line.
player(1). player(2).

% Extract universe of values from combo definitions
is_team(T) :- defense_combo(_, _, _, team(T), _).
is_team(T) :- defense_combo(_, _, _, _, team(T)).

is_event(E) :- defense_combo(_, _, _, event(E), _).
is_event(E) :- defense_combo(_, _, _, _, event(E)).

is_nationality(N) :- defense_combo(_, _, _, nationality(N), _).
is_nationality(N) :- defense_combo(_, _, _, _, nationality(N)).

% Canonicalize combo requirements: Force Entry1 <= Entry2
defense_combo_sorted(ID, R, T, A, B) :- defense_combo(ID, R, T, A, B), A <= B.
defense_combo_sorted(ID, R, T, B, A) :- defense_combo(ID, R, T, A, B), B < A.

% A combo is active if Player 1 matches Entry A AND Player 2 matches Entry B (Sorted)
% This forces a specific assignment order, reducing redundancy.
% FORCED UPDATE TO ENSURE FILE IS WRITTEN
def_active_combo(ID, R, T) :- defense_combo_sorted(ID, R, T, Entry1, Entry2), match(1, Entry1), match(2, Entry2).

% Mark attributes as used if they contribute to an active combo (Canonical direction only)
used(1, Entry1) :- def_active_combo(ID, R, T), defense_combo_sorted(ID, R, T, Entry1, Entry2), match(1, Entry1), match(2, Entry2).
used(2, Entry2) :- def_active_combo(ID, R, T), defense_combo_sorted(ID, R, T, Entry1, Entry2), match(1, Entry1), match(2, Entry2).

% Calculate Total Reward
total_reward(Total) :- Total = #sum { R*M,ID : def_active_combo(ID, R, T), multiplier(T, M) }.

#show def_active_combo/3.
