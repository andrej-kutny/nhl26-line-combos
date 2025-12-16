% Forward line optimization (3 players).

% Combo facts:
%   fwd_combo(ComboID, RewardAmt, RewardType, T1, K1, T2, K2, T3, K3).
% RewardType is an atom: ovr | sal | ap

1 { select(P, 1) : player(P, _, _, _, _) } 1.
1 { select(P, 2) : player(P, _, _, _, _) } 1.
1 { select(P, 3) : player(P, _, _, _, _) } 1.

% No duplicate players in different slots
:- select(P, S1), select(P, S2), S1 < S2.

combo_active(C) :-
    fwd_combo(C, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, 1), matches(P1, T1, K1),
    select(P2, 2), matches(P2, T2, K2),
    select(P3, 3), matches(P3, T3, K3).

% Allow condition order to be permuted across the 3 selected players
combo_active(C) :-
    fwd_combo(C, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, 1), matches(P1, T1, K1),
    select(P2, 2), matches(P2, T3, K3),
    select(P3, 3), matches(P3, T2, K2).

combo_active(C) :-
    fwd_combo(C, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, 1), matches(P1, T2, K2),
    select(P2, 2), matches(P2, T1, K1),
    select(P3, 3), matches(P3, T3, K3).

combo_active(C) :-
    fwd_combo(C, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, 1), matches(P1, T2, K2),
    select(P2, 2), matches(P2, T3, K3),
    select(P3, 3), matches(P3, T1, K1).

combo_active(C) :-
    fwd_combo(C, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, 1), matches(P1, T3, K3),
    select(P2, 2), matches(P2, T1, K1),
    select(P3, 3), matches(P3, T2, K2).

combo_active(C) :-
    fwd_combo(C, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, 1), matches(P1, T3, K3),
    select(P2, 2), matches(P2, T2, K2),
    select(P3, 3), matches(P3, T1, K1).

ovr_bonus(C, Amt) :- combo_active(C), fwd_combo(C, Amt, ovr, _, _, _, _, _, _).
sal_bonus(C, Amt) :- combo_active(C), fwd_combo(C, Amt, sal, _, _, _, _, _, _).
ap_bonus(C, Amt)  :- combo_active(C), fwd_combo(C, Amt, ap,  _, _, _, _, _, _).

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

% Optimization objectives (set by opt_target("ovr"|"salary"|"ap"|"balanced"))
% - ovr: maximize effective OVR; tie-break on bonuses
#maximize { OVR@3, P, S : opt_target("ovr"), select(P, S), ovr(P, OVR);
            Amt@3, C : opt_target("ovr"), ovr_bonus(C, Amt) }.
#maximize { Amt@2, C : opt_target("ovr"), sal_bonus(C, Amt);
            Amt@2, C : opt_target("ovr"), ap_bonus(C, Amt) }.

% - salary: maximize SAL bonus first, then effective OVR
#maximize { Amt@3, C : opt_target("salary"), sal_bonus(C, Amt) }.
#maximize { OVR@2, P, S : opt_target("salary"), select(P, S), ovr(P, OVR);
            Amt@2, C : opt_target("salary"), ovr_bonus(C, Amt) }.

% - ap: maximize AP bonus first, then effective OVR
#maximize { Amt@3, C : opt_target("ap"), ap_bonus(C, Amt) }.
#maximize { OVR@2, P, S : opt_target("ap"), select(P, S), ovr(P, OVR);
            Amt@2, C : opt_target("ap"), ovr_bonus(C, Amt) }.

% - balanced: maximize bonuses first, then OVR
#maximize { Amt@3, C : opt_target("balanced"), sal_bonus(C, Amt);
            Amt@3, C : opt_target("balanced"), ap_bonus(C, Amt);
            Amt@3, C : opt_target("balanced"), ovr_bonus(C, Amt) }.
#maximize { OVR@2, P, S : opt_target("balanced"), select(P, S), ovr(P, OVR) }.

#show select/2.
#show combo_active/1.
#show total_base_ovr/1.
#show total_ovr_bonus/1.
#show total_salary/1.
#show total_salary_bonus/1.
#show total_ap/1.
#show total_ap_bonus/1.
