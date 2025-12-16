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
:- not 1 { combo_active_def_in_pair(C, 3) }.

% Forward line mapping
fwd_line(L, S1, S2, S3) :- L=1, S1=1,  S2=2,  S3=3.
fwd_line(L, S1, S2, S3) :- L=2, S1=4,  S2=5,  S3=6.
fwd_line(L, S1, S2, S3) :- L=3, S1=7,  S2=8,  S3=9.
fwd_line(L, S1, S2, S3) :- L=4, S1=10, S2=11, S3=12.

% Defense pair mapping
def_line(L, S1, S2) :- L=1, S1=13, S2=14.
def_line(L, S1, S2) :- L=2, S1=15, S2=16.
def_line(L, S1, S2) :- L=3, S1=17, S2=18.

% -----------------------------
% Combo activation (team-level)
% -----------------------------
%
% Semantics:
% - A line/pair can activate 0..N combos simultaneously.
% - Every combo ID can contribute at most once globally to the team bonus.
%   (If multiple lines satisfy the same combo, it still counts once.)

in_fwd_line(L, P) :- fwd_line(L, S1, _, _), select(P, S1).
in_fwd_line(L, P) :- fwd_line(L, _, S2, _), select(P, S2).
in_fwd_line(L, P) :- fwd_line(L, _, _, S3), select(P, S3).

fwd_match(C, L, 1, P) :-
    in_fwd_line(L, P),
    fwd_combo(C, _, _, T1, K1, _, _, _, _),
    matches(P, T1, K1).
fwd_match(C, L, 2, P) :-
    in_fwd_line(L, P),
    fwd_combo(C, _, _, _, _, T2, K2, _, _),
    matches(P, T2, K2).
fwd_match(C, L, 3, P) :-
    in_fwd_line(L, P),
    fwd_combo(C, _, _, _, _, _, _, T3, K3),
    matches(P, T3, K3).

fwd_cond_ok(C, L, I) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    fwd_line(L, _, _, _),
    1 <= #count { P : fwd_match(C, L, I, P) },
    I = 1..3.
fwd_pair_ok(C, L, 1, 2) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    fwd_line(L, _, _, _),
    2 <= #count { P : fwd_match(C, L, 1, P); P : fwd_match(C, L, 2, P) }.
fwd_pair_ok(C, L, 1, 3) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    fwd_line(L, _, _, _),
    2 <= #count { P : fwd_match(C, L, 1, P); P : fwd_match(C, L, 3, P) }.
fwd_pair_ok(C, L, 2, 3) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    fwd_line(L, _, _, _),
    2 <= #count { P : fwd_match(C, L, 2, P); P : fwd_match(C, L, 3, P) }.
fwd_triple_ok(C, L) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    fwd_line(L, _, _, _),
    3 <= #count { P : fwd_match(C, L, 1, P); P : fwd_match(C, L, 2, P); P : fwd_match(C, L, 3, P) }.

combo_active_fwd_in_line(C, L) :-
    fwd_combo(C, _, _, _, _, _, _, _, _),
    fwd_cond_ok(C, L, 1), fwd_cond_ok(C, L, 2), fwd_cond_ok(C, L, 3),
    fwd_pair_ok(C, L, 1, 2), fwd_pair_ok(C, L, 1, 3), fwd_pair_ok(C, L, 2, 3),
    fwd_triple_ok(C, L).

combo_active_fwd(C) :- combo_active_fwd_in_line(C, L).

fwd_ovr_bonus(C, Amt) :- combo_active_fwd(C), fwd_combo(C, Amt, ovr, _, _, _, _, _, _).
fwd_sal_bonus(C, Amt) :- combo_active_fwd(C), fwd_combo(C, Amt, sal, _, _, _, _, _, _).
fwd_ap_bonus(C, Amt)  :- combo_active_fwd(C), fwd_combo(C, Amt, ap,  _, _, _, _, _, _).

% Require forward line 3 to activate at least one forward combo (bonus-oriented line)
:- not 1 { combo_active_fwd_in_line(C, 3) }.

in_def_pair(L, P) :- def_line(L, S1, _), select(P, S1).
in_def_pair(L, P) :- def_line(L, _, S2), select(P, S2).

def_match(C, L, 1, P) :-
    in_def_pair(L, P),
    def_combo(C, _, _, T1, K1, _, _),
    matches(P, T1, K1).
def_match(C, L, 2, P) :-
    in_def_pair(L, P),
    def_combo(C, _, _, _, _, T2, K2),
    matches(P, T2, K2).

def_cond_ok(C, L, I) :-
    def_combo(C, _, _, _, _, _, _),
    def_line(L, _, _),
    1 <= #count { P : def_match(C, L, I, P) },
    I = 1..2.
def_union_ok(C, L) :-
    def_combo(C, _, _, _, _, _, _),
    def_line(L, _, _),
    2 <= #count { P : def_match(C, L, 1, P); P : def_match(C, L, 2, P) }.

combo_active_def_in_pair(C, L) :-
    def_combo(C, _, _, _, _, _, _),
    def_cond_ok(C, L, 1), def_cond_ok(C, L, 2),
    def_union_ok(C, L).

combo_active_def(C) :- combo_active_def_in_pair(C, L).

def_ovr_bonus(C, Amt) :- combo_active_def(C), def_combo(C, Amt, ovr, _, _, _, _).
def_sal_bonus(C, Amt) :- combo_active_def(C), def_combo(C, Amt, sal, _, _, _, _).
def_ap_bonus(C, Amt)  :- combo_active_def(C), def_combo(C, Amt, ap,  _, _, _, _).

total_base_ovr(Total) :-
    Total = #sum { OVR, P, S : select(P, S), ovr(P, OVR) }.

total_ovr_bonus(Bonus) :-
    Bonus = #sum {
        Amt, C : fwd_ovr_bonus(C, Amt);
        Amt, C : def_ovr_bonus(C, Amt)
    }.

total_salary(Total) :-
    Total = #sum { S, P, Slt : select(P, Slt), salary_val(P, S) }.

total_ap(Total) :-
    Total = #sum { A, P, Slt : select(P, Slt), ap_val(P, A) }.

total_salary_bonus(Bonus) :-
    Bonus = #sum {
        Amt, C : fwd_sal_bonus(C, Amt);
        Amt, C : def_sal_bonus(C, Amt)
    }.

total_ap_bonus(Bonus) :-
    Bonus = #sum {
        Amt, C : fwd_ap_bonus(C, Amt);
        Amt, C : def_ap_bonus(C, Amt)
    }.

:- max_salary(Max), total_salary(S), total_salary_bonus(B), S - B > Max.
:- max_ap(Max), total_ap(A), total_ap_bonus(B), A - B > Max.

% Maximize base OVR + OVR combo bonus; SAL/AP bonuses as secondary preference
#maximize {
    OVR@3, P, S : select(P, S), ovr(P, OVR);
    Amt@3, C : fwd_ovr_bonus(C, Amt);
    Amt@3, C : def_ovr_bonus(C, Amt);
    Amt@2, C : fwd_sal_bonus(C, Amt);
    Amt@2, C : def_sal_bonus(C, Amt);
    Amt@2, C : fwd_ap_bonus(C, Amt);
    Amt@2, C : def_ap_bonus(C, Amt)
}.

#show select/2.
#show combo_active_fwd/1.
#show combo_active_def/1.
#show total_base_ovr/1.
#show total_ovr_bonus/1.
#show total_salary/1.
#show total_salary_bonus/1.
#show total_ap/1.
#show total_ap_bonus/1.
