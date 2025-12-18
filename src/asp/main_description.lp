player(X) :- id(X), type(X, "player"), nationality(X, _).

forward_card(A,C) :- id(A), player(C), type(A, "card"), has_card(C, A), position(A, "C"), ovr(A, _), salary(A,_), team(A,_).
forward_card(A,C) :- id(A), player(C), type(A, "card"), has_card(C, A), position(A, "LW"), ovr(A, _), salary(A,_), team(A,_).
forward_card(A,C) :- id(A), player(C), type(A, "card"), has_card(C, A), position(A, "RW"), ovr(A, _), salary(A,_), team(A,_).
defense_card(A,C) :- id(A), player(C), type(A, "card"), has_card(C, A), position(A, "G"), ovr(A, _), salary(A,_), team(A,_).
defense_card(A,C) :- id(A), player(C), type(A, "card"), has_card(C, A), position(A, "LD"), ovr(A, _), salary(A,_), team(A,_).
defense_card(A,C) :- id(A), player(C), type(A, "card"), has_card(C, A), position(A, "RD"), ovr(A, _), salary(A,_), team(A,_).

forward_line(A,B,C) :- forward_card(A,P1), forward_card(B,P2), forward_card(C,P3), ovr(A, O1), ovr(B, O2), ovr(C, O3), P1 != P2, P2 != P3, P1 != P3, O1>=O2, O2>=O3.
defense_line(A,B) :- defense_card(A,P1), defense_card(B,P2), ovr(A, O1), ovr(B, O2), P1 != P2, O1>=O2.
goalie_line(A,B) :- defense_line(A,B), position(A,"G"), position(B,"G"). 

#const salary_cap = 1100. % times 100k
#const salary_cap_boost_5 = 50. % times 100k
#const salary_cap_boost_6 = 60. % times 100k
#const salary_cap_boost_7 = 70. % times 100k
#const salary_cap_boost_9 = 90. % times 100k
#const salary_cap_boost_20 = 200. % times 100k

#const overall_bonus_fwd_1 = 1.
#const overall_bonus_fwd_2 = 2.
#const overall_bonus_def_1 = 1.
#const overall_bonus_def_2 = 2.

#const ability_points_bonus_fwd_1 = 1.
#const ability_points_bonus_fwd_3 = 3.
#const ability_points_bonus_fwd_5 = 5.
#const ability_points_bonus_fwd_6 = 6.
#const ability_points_bonus_fwd_12 = 12.
#const ability_points_bonus_def_2 = 2.
#const ability_points_bonus_def_4 = 4.
#const ability_points_bonus_def_5 = 5.
#const ability_points_bonus_def_8 = 8.