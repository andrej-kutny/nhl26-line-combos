% Full team optimization
% Slots:
%   1..12   = forwards (4 lines, each 3 players)
%   13..18  = defense (3 pairs, each 2 players)
%   19..20  = goalies (2 spots)

fwd_slot(1..12).
def_slot(13..18).
g_slot(19..20).

% Require strong first forward line (slots 1-3)
:- select(P, S), S=1..3, ovr(P, OVR), OVR < 87.

% Require solid second forward line (slots 4-6)
:- select(P, S), S=4..6, ovr(P, OVR), OVR < 85.

% Exactly one player per slot
1 { select(P, S) : player(P, _, _, _, _) } 1 :- fwd_slot(S).
1 { select(P, S) : player(P, _, _, _, _) } 1 :- def_slot(S).
1 { select(P, S) : player(P, _, _, _, _) } 1 :- g_slot(S).

% No duplicate players across any slots
:- select(P, S1), select(P, S2), S1 < S2.

% Goalie 1 (slot 19) must meet a higher OVR threshold
:- select(P, S), S=19, ovr(P, OVR), OVR < 87.

% Defense lines 1-2 should be solid
:- select(P, S), S=13..16, ovr(P, OVR), OVR < 85.

% Defense pair 3 (bonus-oriented) must activate at least one defense combo
:- not 1 { combo_active_def(C, 3) }.

% Forward line mapping
fwd_line(L, S1, S2, S3) :- L=1, S1=1,  S2=2,  S3=3.
fwd_line(L, S1, S2, S3) :- L=2, S1=4,  S2=5,  S3=6.
fwd_line(L, S1, S2, S3) :- L=3, S1=7,  S2=8,  S3=9.
fwd_line(L, S1, S2, S3) :- L=4, S1=10, S2=11, S3=12.

% Defense pair mapping
def_line(L, S1, S2) :- L=1, S1=13, S2=14.
def_line(L, S1, S2) :- L=2, S1=15, S2=16.
def_line(L, S1, S2) :- L=3, S1=17, S2=18.

% Activate forward combos per line; each combo can be used at most once globally
combo_active_fwd(C, L) :-
    fwd_line(L, S1, S2, S3),
    fwd_combo(C, _, _, T1, K1, T2, K2, T3, K3),
    select(P1, S1), matches(P1, T1, K1),
    select(P2, S2), matches(P2, T2, K2),
    select(P3, S3), matches(P3, T3, K3).

% At most one active forward combo per line.
:- combo_active_fwd(C1, L), combo_active_fwd(C2, L), C1 < C2.

:- combo_active_fwd(C, L1), combo_active_fwd(C, L2), L1 != L2.

ovr_bonus(C, Amt) :- combo_active_fwd(C, _), fwd_combo(C, Amt, ovr, _, _, _, _, _, _).
sal_bonus(C, Amt) :- combo_active_fwd(C, _), fwd_combo(C, Amt, sal, _, _, _, _, _, _).
ap_bonus(C, Amt)  :- combo_active_fwd(C, _), fwd_combo(C, Amt, ap,  _, _, _, _, _, _).

% Require line 3 to activate at least one forward combo (bonus-oriented line)
:- not 1 { combo_active_fwd(C, 3) }.

% Activate defense combos per pair; each combo can be used at most once globally
combo_active_def(C, L) :-
    def_line(L, S1, S2),
    def_combo(C, _, _, T1, K1, T2, K2),
    select(P1, S1), matches(P1, T1, K1),
    select(P2, S2), matches(P2, T2, K2).

% At most one active defense combo per pair.
:- combo_active_def(C1, L), combo_active_def(C2, L), C1 < C2.

:- combo_active_def(C, L1), combo_active_def(C, L2), L1 != L2.

ovr_bonus(C, Amt) :- combo_active_def(C, _), def_combo(C, Amt, ovr, _, _, _, _).
sal_bonus(C, Amt) :- combo_active_def(C, _), def_combo(C, Amt, sal, _, _, _, _).
ap_bonus(C, Amt)  :- combo_active_def(C, _), def_combo(C, Amt, ap,  _, _, _, _).

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

% Maximize base OVR + OVR combo bonus; SAL/AP bonuses as secondary preference
#maximize {
    OVR@3, P, S : select(P, S), ovr(P, OVR);
    Amt@3, C : ovr_bonus(C, Amt);
    Amt@2, C : sal_bonus(C, Amt);
    Amt@2, C : ap_bonus(C, Amt)
}.

#show select/2.
#show combo_active_fwd/2.
#show combo_active_def/2.
#show total_base_ovr/1.
#show total_ovr_bonus/1.
#show total_salary/1.
#show total_salary_bonus/1.
#show total_ap/1.
#show total_ap_bonus/1.
