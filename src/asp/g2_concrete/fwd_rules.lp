#const num_players = 3.
#include "../g1a_abstraction/fwd_rules.lp".

active_combo_any(ID, R, T) :- fwd_active_combo(ID, R, T).
