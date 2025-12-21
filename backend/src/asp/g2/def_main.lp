% Defense specific rules

% ------------------------------------------------------------------------------
% Defense Cards
% ------------------------------------------------------------------------------
% Helper for defense positions removed as per request
% We assume the input player/7 facts are pre-filtered for defense

defense_card(CardID, PlayerID) :- 
    player(CardID, PlayerID, _, _, _, _, _).

% ------------------------------------------------------------------------------
% Line Formation
% ------------------------------------------------------------------------------
% Defense Line: 2 different players
defense_line(A,B) :- 
    defense_card(A,P1), defense_card(B,P2), 
    ovr(A, O1), ovr(B, O2), 
    P1 != P2, 
    O1>=O2.

goalie_line(A,B) :- defense_line(A,B), position(A,"G"), position(B,"G"). 

% ------------------------------------------------------------------------------
% Combo Logic
% ------------------------------------------------------------------------------

% Normalize Defense Combos
def_combo_perm(ID,R,T,A,B) :- defense_combo(ID,R,T,A,B).
def_combo_perm(ID,R,T,B,A) :- defense_combo(ID,R,T,A,B).

def_combo_sorted(ID,R,T,A,B) :- def_combo_perm(ID,R,T,A,B), A <= B.

% Helper: Check if players match requirements
def_match_perm(A,B, R1,R2) :-
    player_match(A, R1), player_match(B, R2).

% ------------------------------------------------------------------------------
% Boosted Lines
% ------------------------------------------------------------------------------
boosted_def_line(A, B, BoostType, BoostValue, R1, R2) :-
    defense_line(A, B),
    def_combo_sorted(ID, BoostValue, BoostType, R1, R2),
    1 <= {
        def_match_perm(A,B, R1,R2);
        def_match_perm(B,A, R1,R2)
    }.
