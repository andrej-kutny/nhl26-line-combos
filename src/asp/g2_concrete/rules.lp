#const salary_cap = 999999.
#const w_ovr = 1.
#const w_ap = 1.
#const w_sal = 1.

% Map weights
multiplier("OVR", w_ovr).
multiplier("AP", w_ap).
multiplier("SAL", w_sal).

% Match helper (interface to G1A combo logic)
match(P, Req) :- player_attr(P, Req).

% 1. Select players
{ selected(CardID) : player(CardID, _, _, _, _, _, _) } = num_players.

% 2. Assign positions 1..num_players to selected cards deterministically
% Rank cards by ID
sel_rank(C, R) :- selected(C), R = #count { C2 : selected(C2), C2 <= C }.
line_player(P, C) :- sel_rank(C, P).

% 3. Bridge to G1A: Generate player_attr/2 from selected players
player_attr(P, nationality(N)) :- line_player(P, C), player(C, _, N, _, _, _, _).
player_attr(P, event(E))       :- line_player(P, C), player(C, _, _, E, _, _, _).
player_attr(P, team(T))        :- line_player(P, C), player(C, _, _, _, T, _, _).

% 4. Constraint: Unique Player ID
:- selected(C1), selected(C2), C1 < C2,
   player(C1, PID, _, _, _, _, _), player(C2, PID, _, _, _, _, _).

% 5. Constraint: Salary Cap with Bonus Logic
base_salary(S) :- S = #sum { Sal,C : selected(C), player(C, _, _, _, _, _, Sal) }.
sal_bonus(B) :- B = #sum { R,ID : active_combo_any(ID, R, "SAL") }.
total_salary(S) :- base_salary(Base), sal_bonus(Bonus), S = Base - Bonus.

:- total_salary(S), S > salary_cap.

% 6. Objective
% Base OVR sum
total_ovr(O) :- O = #sum { Ovr,C : selected(C), player(C, _, _, _, _, Ovr, _) }.

% Final Objective: Maximize Base OVR + Combo Rewards
% Note: total_reward/1 comes from G1A rules.
final_score(S) :- total_ovr(O), total_reward(R), S = O + R.

#maximize { S : final_score(S) }.

#show selected/1.
#show final_score/1.
#show total_reward/1.
#show total_ovr/1.
#show total_salary/1.
#show sal_bonus/1.
