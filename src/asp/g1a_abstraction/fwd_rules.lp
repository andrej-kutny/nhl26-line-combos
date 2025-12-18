% We need exactly 3 players for one forward line.
player(1..3).

% Symmetry: order in combo definition doesn't matter. Generate all 6 permutations.
forward_combo_perm(ID, R, T, A, B, C) :- forward_combo(ID, R, T, A, B, C).
forward_combo_perm(ID, R, T, A, C, B) :- forward_combo(ID, R, T, A, B, C).
forward_combo_perm(ID, R, T, B, A, C) :- forward_combo(ID, R, T, A, B, C).
forward_combo_perm(ID, R, T, B, C, A) :- forward_combo(ID, R, T, A, B, C).
forward_combo_perm(ID, R, T, C, A, B) :- forward_combo(ID, R, T, A, B, C).
forward_combo_perm(ID, R, T, C, B, A) :- forward_combo(ID, R, T, A, B, C).

% Extract universe of values from combo definitions
is_team(T) :- forward_combo(_, _, _, team(T), _, _).
is_team(T) :- forward_combo(_, _, _, _, team(T), _).
is_team(T) :- forward_combo(_, _, _, _, _, team(T)).

is_event(E) :- forward_combo(_, _, _, event(E), _, _).
is_event(E) :- forward_combo(_, _, _, _, event(E), _).
is_event(E) :- forward_combo(_, _, _, _, _, event(E)).

is_nationality(N) :- forward_combo(_, _, _, nationality(N), _, _).
is_nationality(N) :- forward_combo(_, _, _, _, nationality(N), _).
is_nationality(N) :- forward_combo(_, _, _, _, _, nationality(N)).

% A combo is active if Player 1 matches Entry A, Player 2 matches Entry B, Player 3 matches Entry C
% Since we expanded all permutations of the requirements, checking 1-A, 2-B, 3-C covers all cases.
fwd_active_combo(ID, R, T) :- forward_combo_perm(ID, R, T, A, B, C), match(1, A), match(2, B), match(3, C).

% Mark attributes as used if they contribute to an active combo
used(1, A) :- fwd_active_combo(ID, R, T), forward_combo_perm(ID, R, T, A, B, C), match(1, A), match(2, B), match(3, C).
used(2, B) :- fwd_active_combo(ID, R, T), forward_combo_perm(ID, R, T, A, B, C), match(1, A), match(2, B), match(3, C).
used(3, C) :- fwd_active_combo(ID, R, T), forward_combo_perm(ID, R, T, A, B, C), match(1, A), match(2, B), match(3, C).

% Calculate Total Reward
total_reward(Total) :- Total = #sum { R*M,ID : fwd_active_combo(ID, R, T), multiplier(T, M) }.

#show fwd_active_combo/3.
