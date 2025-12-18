% Symmetry: order in combo definition doesn't matter
defense_combo(ID, R, T, B, A) :- defense_combo(ID, R, T, A, B).

% We need exactly 2 players for one defense line.
player(1..2).

% Extract universe of values from combo definitions
is_team(T) :- defense_combo(_, _, _, team(T), _).
is_team(T) :- defense_combo(_, _, _, _, team(T)).

is_event(E) :- defense_combo(_, _, _, event(E), _).
is_event(E) :- defense_combo(_, _, _, _, event(E)).

is_nationality(N) :- defense_combo(_, _, _, nationality(N), _).
is_nationality(N) :- defense_combo(_, _, _, _, nationality(N)).

% A combo is active if Player 1 matches Entry A AND Player 2 matches Entry B
% Since we have symmetry in defense_combo/5 and player symmetry breaking, checking (1,A) and (2,B) is sufficient
% provided defense_combo includes both (A,B) and (B,A).
def_active_combo(ID, R, T) :- defense_combo(ID, R, T, Entry1, Entry2), match(1, Entry1), match(2, Entry2).

% Mark attributes as used if they contribute to an active combo
used(1, Entry1) :- def_active_combo(ID, R, T), defense_combo(ID, R, T, Entry1, Entry2), match(1, Entry1), match(2, Entry2).
used(2, Entry2) :- def_active_combo(ID, R, T), defense_combo(ID, R, T, Entry1, Entry2), match(1, Entry1), match(2, Entry2).

% Calculate Total Reward
total_reward(Total) :- Total = #sum { R*M,ID : def_active_combo(ID, R, T), multiplier(T, M) }.

#show def_active_combo/3.
