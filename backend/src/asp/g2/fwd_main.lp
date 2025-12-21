% Forward specific rules

% ------------------------------------------------------------------------------
% Forward Cards
% ------------------------------------------------------------------------------
% Helper for forward positions removed as per request
% We assume the input player/7 facts are pre-filtered for forwards

forward_card(CardID, PlayerID) :- 
    player(CardID, PlayerID, _, _, _, _, _).

% ------------------------------------------------------------------------------
% Line Formation
% ------------------------------------------------------------------------------
% Forward Line: 3 different players (P1!=P2!=P3), sorted by OVR to reduce symmetry
forward_line(A,B,C) :- 
    forward_card(A,P1), forward_card(B,P2), forward_card(C,P3), 
    ovr(A, O1), ovr(B, O2), ovr(C, O3), 
    P1 != P2, P2 != P3, P1 != P3, 
    O1>=O2, O2>=O3.

% ------------------------------------------------------------------------------
% Combo Logic
% ------------------------------------------------------------------------------

% Normalize Forward Combos to sorted requirements
% This handles input permutations in combo definitions
fwd_combo_perm(ID,R,T,A,B,C) :- forward_combo(ID,R,T,A,B,C).
fwd_combo_perm(ID,R,T,A,C,B) :- forward_combo(ID,R,T,A,B,C).
fwd_combo_perm(ID,R,T,B,A,C) :- forward_combo(ID,R,T,A,B,C).
fwd_combo_perm(ID,R,T,B,C,A) :- forward_combo(ID,R,T,A,B,C).
fwd_combo_perm(ID,R,T,C,A,B) :- forward_combo(ID,R,T,A,B,C).
fwd_combo_perm(ID,R,T,C,B,A) :- forward_combo(ID,R,T,A,B,C).

% Select canonical (sorted) permutation of requirements
fwd_combo_sorted(ID,R,T,A,B,C) :- fwd_combo_perm(ID,R,T,A,B,C), A <= B, B <= C.

% Helper: Check if players match requirements in a specific order
fwd_match_perm(A,B,C, R1,R2,R3) :- 
    player_match(A, R1), player_match(B, R2), player_match(C, R3).

% ------------------------------------------------------------------------------
% Boosted Lines
% ------------------------------------------------------------------------------
% A line (A,B,C) is boosted by a combo (R1,R2,R3) if the players can be matched to requirements.
boosted_fwd_line(A, B, C, BoostType, BoostValue, R1, R2, R3) :-
    forward_line(A, B, C),
    fwd_combo_sorted(ID, BoostValue, BoostType, R1, R2, R3),
    1 <= {
        fwd_match_perm(A,B,C, R1,R2,R3);
        fwd_match_perm(A,C,B, R1,R2,R3);
        fwd_match_perm(B,A,C, R1,R2,R3);
        fwd_match_perm(B,C,A, R1,R2,R3);
        fwd_match_perm(C,A,B, R1,R2,R3);
        fwd_match_perm(C,B,A, R1,R2,R3)
    }.
