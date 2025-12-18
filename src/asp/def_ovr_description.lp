ovr_boosted_def_line(A,B) :- ovr_boosted_def_line_1(A,B).
ovr_boosted_def_line(A,B) :- ovr_boosted_def_line_2(A,B).

ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"VAN"),card_type(_,"COM").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"NG"),nationality(_,"CZECHIA").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"CAR"),team(_,"PIT").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"TOTW"),card_type(_,"SOTM").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"MIN"),team(_,"CGY").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"OTT"),team(_,"BUF").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"BOS"),card_type(_,"NG").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"VAN"),nationality(_,"FINLAND").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"ROOK"),card_type(_,"HH").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"COL"),card_type(_,"ICON").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"CAP"),team(_,"SJS").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"MIN"),team(_,"VAN").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"SEA"),team(_,"MTL").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"STL"),team(P2,"STL").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"CGY"),team(P2,"CGY").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"MTL"),team(P2,"MTL").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"NG"),team(_,"EVT").
ovr_boosted_def_line_1(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"CAR"),card_type(_,"NG").
ovr_boosted_def_line_2(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"MIN"),card_type(_,"COM").

total_ovr_def(A,B,TOTAL_OVERALL) :- ovr_boosted_def_line_1(A,B), ovr(A,O1), ovr(B,O2), TOTAL_OVERALL = O1+O2+overall_bonus_def_1.
total_ovr_def(A,B,TOTAL_OVERALL) :- ovr_boosted_def_line_2(A,B), ovr(A,O1), ovr(B,O2), TOTAL_OVERALL = O1+O2+overall_bonus_def_2.
defense_line_ovr_combination(A,B) :- defense_line(A,B), ovr_boosted_def_line(A,B).
{ best_defense_line_ovr_combination(A,B) : defense_line_ovr_combination(A,B) } <= 50.
#maximize{ TOTAL_OVERALL@0,A,B : best_defense_line_ovr_combination(A,B), total_ovr_def(A,B,TOTAL_OVERALL) }.

#show best_defense_line_ovr_combination/2.