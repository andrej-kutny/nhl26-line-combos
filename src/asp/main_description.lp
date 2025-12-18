boost_type("OVR";"SAL";"AP").

player(X) :- id(X), type(X, "player"), nationality(X, _).

forward_card(X,Y) :- id(X), player(Y), type(X, "card"), has_card(Y, X), position(X, "C"), ovr(X, _), salary(X,_), team(X,_).
forward_card(X,Y) :- id(X), player(Y), type(X, "card"), has_card(Y, X), position(X, "LW"), ovr(X, _), salary(X,_), team(X,_).
forward_card(X,Y) :- id(X), player(Y), type(X, "card"), has_card(Y, X), position(X, "RW"), ovr(X, _), salary(X,_), team(X,_).
defense_card(X,Y) :- id(X), player(Y), type(X, "card"), has_card(Y, X), position(X, "G"), ovr(X, _), salary(X,_), team(X,_).
defense_card(X,Y) :- id(X), player(Y), type(X, "card"), has_card(Y, X), position(X, "LD"), ovr(X, _), salary(X,_), team(X,_).
defense_card(X,Y) :- id(X), player(Y), type(X, "card"), has_card(Y, X), position(X, "RD"), ovr(X, _), salary(X,_), team(X,_).

forward_line(A,B,C) :- forward_card(A,P1), forward_card(B,P2), forward_card(C,P3), ovr(A, O1), ovr(B, O2), ovr(C, O3), P1 != P2, P2 != P3, P1 != P3, O1>=O2, O2>=O3.
defense_line(A,B) :- defense_card(A,P1), defense_card(B,P2), ovr(A, O1), ovr(B, O2), P1 != P2, O1>=O2.
goalie_line(A,B) :- defense_line(A,B), position(A,"G"), position(B,"G"). 

boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,club(X1),event(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,X1),card_type(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,club(X1),country(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,X1),nationality(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,club(X1),club(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,X1),team(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,event(X1),event(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,X1),card_type(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,event(X1),country(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,X1),nationality(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,event(X1),club(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,X1),team(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,country(X1),event(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),nationality(_,X1),card_type(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,country(X1),country(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),nationality(_,X1),nationality(_,X2).
boosted_def_line(A,B,BOOST_TYPE,BOOST_VALUE,X1,X2) :- boost_type(BOOST_TYPE),defense_combo(_,BOOST_VALUE,BOOST_TYPE,country(X1),club(X2)),defense_line(A,B),defense_card(A,P1),defense_card(B,P2),nationality(_,X1),team(_,X2).

boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,club(X1),club(X2),club(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,X1),team(_,X2),team(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,club(X1),club(X2),event(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,X1),team(_,X2),card_type(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,club(X1),club(X2),country(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,X1),team(_,X2),nationality(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,event(X1),event(X2),club(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,X1),card_type(_,X2),team(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,event(X1),event(X2),country(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,X1),card_type(_,X2),nationality(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,event(X1),event(X2),event(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,X1),card_type(_,X2),card_type(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,country(X1),country(X2),club(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,X1),nationality(_,X2),team(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,country(X1),country(X2),country(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,X1),nationality(_,X2),nationality(_,X3).
boosted_fwd_line(A,B,C,BOOST_TYPE,BOOST_VALUE,X1,X2,X3) :- boost_type(BOOST_TYPE),forward_combo(_,BOOST_VALUE,BOOST_TYPE,country(X1),country(X2),event(X3)),forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,X1),nationality(_,X2),card_type(_,X3).

#const salary_cap = 1100.
#const w_ovr = 1.
#const w_ap = 1.
#const w_sal = 1.