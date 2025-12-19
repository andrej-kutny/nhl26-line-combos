% Forward line optimization (3 players).
%
% Semantics (aligned with gameplay notes):
% - A line can activate 0..N different combos at the same time.
% - A combo activates iff its conditions can be matched injectively to the
%   selected players (i.e., 3 distinct players cover 3 conditions).
%
% Combo facts:
%   fwd_combo(ComboID, RewardAmt, RewardType, T1, K1, T2, K2, T3, K3).
% RewardType is an atom: ovr | sal | ap

1 { select(P, 1) : player(P, _, _, _, _) } 1.
1 { select(P, 2) : player(P, _, _, _, _) } 1.
1 { select(P, 3) : player(P, _, _, _, _) } 1.

% No duplicate players in different slots
:- select(P, S1), select(P, S2), S1 < S2.

% Symmetry breaking: slot order is irrelevant for constraints/objective here.
% This reduces 3! equivalent permutations of the same selected set.
:- select(P1, 1), select(P2, 2), P1 > P2.
:- select(P2, 2), select(P3, 3), P2 > P3.

in_line(P) :- select(P, _).

% Combo activation without grounding a (P1,P2,P3) cross-product.
%
% For |conditions|=|players|=3 we can use Hall's marriage theorem:
% a perfect matching exists iff every subset of conditions is covered by at
% least that many distinct players.

match_cond(C, 1, P) :-
    in_line(P),
    fwd_combo(C, _, _, T1, K1, _, _, _, _),
    matches(P, T1, K1).
match_cond(C, 2, P) :-
    in_line(P),
    fwd_combo(C, _, _, _, _, T2, K2, _, _),
    matches(P, T2, K2).
match_cond(C, 3, P) :-
    in_line(P),
    fwd_combo(C, _, _, _, _, _, _, T3, K3),
    matches(P, T3, K3).

cond_ok(C, I) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    1 <= #count { P : match_cond(C, I, P) },
    I = 1..3.

pair_ok(C, 1, 2) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    2 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 2, P) }.
pair_ok(C, 1, 3) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    2 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 3, P) }.
pair_ok(C, 2, 3) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    2 <= #count { P : match_cond(C, 2, P); P : match_cond(C, 3, P) }.

triple_ok(C) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    3 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 2, P); P : match_cond(C, 3, P) }.

combo_active(C) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    cond_ok(C, 1), cond_ok(C, 2), cond_ok(C, 3),
    pair_ok(C, 1, 2), pair_ok(C, 1, 3), pair_ok(C, 2, 3),
    triple_ok(C).

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
