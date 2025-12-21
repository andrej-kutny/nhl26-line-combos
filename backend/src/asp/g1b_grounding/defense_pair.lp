% Defense pair optimization (2 players).

% Combo facts:
%   def_combo(ComboID, RewardAmt, RewardType, T1, K1, T2, K2).
% RewardType is an atom: ovr | sal | ap

1 { select(P, 1) : player(P, _, _, _, _) } 1.
1 { select(P, 2) : player(P, _, _, _, _) } 1.

% No duplicate players in different slots
:- select(P, S1), select(P, S2), S1 < S2.

% Symmetry breaking: slot order is irrelevant for constraints/objective here.
:- select(P1, 1), select(P2, 2), P1 > P2.

in_pair(P) :- select(P, _).

% Combo activation without grounding a (P1,P2) cross-product.
%
% For |conditions|=|players|=2, a perfect matching exists iff:
% - each condition matches at least one selected player, and
% - the union of players matching either condition has size >= 2.

match_cond(C, 1, P) :-
    in_pair(P),
    def_combo(C, _, _, T1, K1, _, _),
    matches(P, T1, K1).
match_cond(C, 2, P) :-
    in_pair(P),
    def_combo(C, _, _, _, _, T2, K2),
    matches(P, T2, K2).

cond_ok(C, I) :-
    def_combo(C, _, _, _, _, _, _),
    1 <= #count { P : match_cond(C, I, P) },
    I = 1..2.
union_ok(C) :-
    def_combo(C, _, _, _, _, _, _),
    2 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 2, P) }.

combo_active(C) :- def_combo(C, _, _, _, _, _, _), cond_ok(C, 1), cond_ok(C, 2), union_ok(C).

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

% Optimization objectives (set by opt_target("ovr"|"salary"|"ap"|"balanced"))
% - ovr: maximize effective OVR; tie-break on bonuses
#maximize { OVR@3, P, S : opt_target("ovr"), select(P, S), ovr(P, OVR);
            Amt@3, C : opt_target("ovr"), ovr_bonus(C, Amt) }.

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
