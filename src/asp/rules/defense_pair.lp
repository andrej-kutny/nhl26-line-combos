% Defense pair optimization (2 players).

% Combo facts:
%   def_combo(ComboID, RewardAmt, RewardType, T1, K1, T2, K2).
% RewardType is an atom: ovr | sal | ap

1 { select(P, 1) : player(P, _, _, _, _) } 1.
1 { select(P, 2) : player(P, _, _, _, _) } 1.

% No duplicate players in different slots
:- select(P, S1), select(P, S2), S1 < S2.

combo_active(C) :-
    def_combo(C, _, _, T1, K1, T2, K2),
    select(P1, 1), matches(P1, T1, K1),
    select(P2, 2), matches(P2, T2, K2).

ovr_bonus(C, Amt) :- combo_active(C), def_combo(C, Amt, ovr, _, _, _, _).
sal_bonus(C, Amt) :- combo_active(C), def_combo(C, Amt, sal, _, _, _, _).
ap_bonus(C, Amt)  :- combo_active(C), def_combo(C, Amt, ap,  _, _, _, _).

total_base_ovr(Total) :-
    Total = #sum { OVR, P, S : select(P, S), ovr(P, OVR) }.

total_ovr_bonus(Bonus) :-
    Bonus = #sum { Amt, C : ovr_bonus(C, Amt) }.

total_salary(Total) :-
    Total = #sum { S, P, Slt : select(P, Slt), salary_val(P, S) }.

total_ap(Total) :-
    Total = #sum { A, P, Slt : select(P, Slt), ap_val(P, A) }.

total_salary_bonus(Bonus) :-
    Bonus = #sum { Amt, C : sal_bonus(C, Amt) }.

total_ap_bonus(Bonus) :-
    Bonus = #sum { Amt, C : ap_bonus(C, Amt) }.

:- max_salary(Max), total_salary(S), total_salary_bonus(B), S - B > Max.
:- max_ap(Max), total_ap(A), total_ap_bonus(B), A - B > Max.

% Maximize base OVR + OVR combo bonus (single priority)
#maximize { OVR@1, P, S : select(P, S), ovr(P, OVR); Amt@1, C : ovr_bonus(C, Amt) }.

#show select/2.
#show combo_active/1.
#show total_base_ovr/1.
#show total_ovr_bonus/1.
#show total_salary/1.
#show total_salary_bonus/1.
#show total_ap/1.
#show total_ap_bonus/1.
