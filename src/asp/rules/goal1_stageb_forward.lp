% Goal 1 — Stage B (forward): enumerate all concrete forward lines that satisfy
% a required set of forward combos, and report *all* combos activated by the
% chosen line.
%
% Inputs (facts from Python/backend):
% - player(CardID, OVR, Team, Nationality, Event).
% - card_player(CardID, PlayerID).          % optional but recommended
% - salary(CardID, SalaryM). ap(CardID, AP).% optional
% - fwd_combo(ComboID, RewardAmt, RewardType, T1, K1, T2, K2, T3, K3).
% - required_combo(ComboID).               % the combo IDs to enforce
%
% Semantics:
% - We enumerate *all* distinct 3-player lines that satisfy ALL required combos.
% - A line may activate 0..N combos simultaneously.
% - Uniqueness is enforced via base.lp (no two cards with the same PlayerID).
% - Symmetry is broken by enforcing an ordering on selected CardIDs.

1 { select(P, 1) : player(P, _, _, _, _) } 1.
1 { select(P, 2) : player(P, _, _, _, _) } 1.
1 { select(P, 3) : player(P, _, _, _, _) } 1.

% No duplicate cards in different slots
:- select(P, S1), select(P, S2), S1 < S2.

% Symmetry breaking (treat {p1,p2,p3} as a set)
:- select(P1, 1), select(P2, 2), P1 > P2.
:- select(P2, 2), select(P3, 3), P2 > P3.

in_line(P) :- select(P, _).

% Combo activation (injective match conditions -> players) without grounding
% a full (P1,P2,P3) cross-product.
%
% For 3 conditions and 3 players, a perfect matching exists iff Hall's condition
% holds for all subsets of conditions.

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

cond_ok(C, I) :- fwd_combo(C, _, _, _, _, _, _, _, _), 1 <= #count { P : match_cond(C, I, P) }, I = 1..3.

pair_ok(C, 1, 2) :- fwd_combo(C, _, _, _, _, _, _, _, _), 2 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 2, P) }.
pair_ok(C, 1, 3) :- fwd_combo(C, _, _, _, _, _, _, _, _), 2 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 3, P) }.
pair_ok(C, 2, 3) :- fwd_combo(C, _, _, _, _, _, _, _, _), 2 <= #count { P : match_cond(C, 2, P); P : match_cond(C, 3, P) }.

triple_ok(C) :- fwd_combo(C, _, _, _, _, _, _, _, _), 3 <= #count { P : match_cond(C, 1, P); P : match_cond(C, 2, P); P : match_cond(C, 3, P) }.

combo_active(C) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    cond_ok(C, 1), cond_ok(C, 2), cond_ok(C, 3),
    pair_ok(C, 1, 2), pair_ok(C, 1, 3), pair_ok(C, 2, 3),
    triple_ok(C).

% Enforce that all required combos are active for the chosen line
:- required_combo(C), not combo_active(C).

total_base_ovr(Total) :-
    Total = #sum { OVR, P, S : select(P, S), ovr(P, OVR) }.

total_salary(Total) :-
    Total = #sum { S, P, Slt : select(P, Slt), salary_val(P, S) }.

total_ap(Total) :-
    Total = #sum { A, P, Slt : select(P, Slt), ap_val(P, A) }.

total_ovr_bonus(Bonus) :-
    Bonus = #sum { Amt, C : combo_active(C), fwd_combo(C, Amt, ovr, _, _, _, _, _, _) }.

total_salary_bonus(Bonus) :-
    Bonus = #sum { Amt, C : combo_active(C), fwd_combo(C, Amt, sal, _, _, _, _, _, _) }.

total_ap_bonus(Bonus) :-
    Bonus = #sum { Amt, C : combo_active(C), fwd_combo(C, Amt, ap, _, _, _, _, _, _) }.

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
