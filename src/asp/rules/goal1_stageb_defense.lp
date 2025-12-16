% Goal 1 — Stage B (defense): enumerate all concrete defense pairs that satisfy
% a required set of defense combos.
%
% Inputs (facts from Python/backend):
% - player(CardID, OVR, Team, Nationality, Event).
% - card_player(CardID, PlayerID).          % optional but recommended
% - salary(CardID, SalaryM). ap(CardID, AP).% optional
% - def_combo(ComboID, RewardAmt, RewardType, T1, K1, T2, K2).
% - required_combo(ComboID).               % the combo IDs to enforce
%
% Semantics:
% - We enumerate *all* distinct 2-player pairs that satisfy ALL required combos.
% - Uniqueness is enforced via base.lp (no two cards with the same PlayerID).
% - Symmetry is broken by enforcing an ordering on selected CardIDs.

1 { select(P, 1) : player(P, _, _, _, _) } 1.
1 { select(P, 2) : player(P, _, _, _, _) } 1.

% No duplicate cards in different slots
:- select(P, S1), select(P, S2), S1 < S2.

% Symmetry breaking (treat {p1,p2} as a set)
:- select(P1, 1), select(P2, 2), P1 > P2.

in_pair(P) :- select(P, _).

% For 2 conditions and 2 players, a perfect matching exists iff:
% - each condition matches at least one selected player, and
% - the union of players matching either condition has size >= 2.

match_cond(C, 1, P) :-
    required_combo(C),
    in_pair(P),
    def_combo(C, _, _, T1, K1, _, _),
    matches(P, T1, K1).
match_cond(C, 2, P) :-
    required_combo(C),
    in_pair(P),
    def_combo(C, _, _, _, _, T2, K2),
    matches(P, T2, K2).

cond_ok(C, I) :- required_combo(C), 1 <= #count { P : match_cond(C, I, P) }, I = 1..2.
union_ok(C) :- required_combo(C), 2 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 2, P) }.

combo_active(C) :- required_combo(C), cond_ok(C, 1), cond_ok(C, 2), union_ok(C).

% Enforce that all required combos are active for the chosen pair
:- required_combo(C), not combo_active(C).

total_base_ovr(Total) :-
    Total = #sum { OVR, P, S : select(P, S), ovr(P, OVR) }.

total_salary(Total) :-
    Total = #sum { S, P, Slt : select(P, Slt), salary_val(P, S) }.

total_ap(Total) :-
    Total = #sum { A, P, Slt : select(P, Slt), ap_val(P, A) }.

total_ovr_bonus(Bonus) :-
    Bonus = #sum { Amt, C : combo_active(C), def_combo(C, Amt, ovr, _, _, _, _) }.

total_salary_bonus(Bonus) :-
    Bonus = #sum { Amt, C : combo_active(C), def_combo(C, Amt, sal, _, _, _, _) }.

total_ap_bonus(Bonus) :-
    Bonus = #sum { Amt, C : combo_active(C), def_combo(C, Amt, ap, _, _, _, _) }.

% Optional caps (same convention as the API: effective cap is total - bonus)
:- max_salary(Max), total_salary(S), total_salary_bonus(B), S - B > Max.
:- max_ap(Max), total_ap(A), total_ap_bonus(B), A - B > Max.

#show select/2.
#show combo_active/1.
#show total_base_ovr/1.
#show total_ovr_bonus/1.
#show total_salary/1.
#show total_salary_bonus/1.
#show total_ap/1.
#show total_ap_bonus/1.

