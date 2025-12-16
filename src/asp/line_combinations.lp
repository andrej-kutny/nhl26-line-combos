comp(X) :- id(X), type(X, "comp").

player(X) :- id(X), first_name(X, _), family_name(X, _), type(X, "player"), nationality(X, _).

attack_card(A,B,C) :- id(A), comp(B), player(C), plays_in(C, B), type(A, "card"), has_card(C, A), position(A, "attack"), ovr(A, _).

defense_card(A,B,C) :- id(A), comp(B), player(C), plays_in(C, B), type(A, "card"), has_card(C, A), position(A, "defense"), ovr(A, _).

{ attack_team(A, B, C) : attack_card(A,_,P1), attack_card(B,_,P2), attack_card(C,_,P3), P1 != P2, P2 != P3, P1 != P3 } = 1.
{ defense_team(A, B) : defense_card(A,_,P1), defense_card(B,_,P2), P1 != P2 } = 1.

#show player/1.
#show comp/1.
#show attack_team/3.
#show defense_team/2.