sal_boosted_def_line(A,B) :- sal_boosted_def_line_5(A,B).
sal_boosted_def_line(A,B) :- sal_boosted_def_line_6(A,B).
sal_boosted_def_line(A,B) :- sal_boosted_def_line_7(A,B).
sal_boosted_def_line(A,B) :- sal_boosted_def_line_10(A,B).
sal_boosted_def_line(A,B) :- sal_boosted_def_line_15(A,B).

sal_boosted_def_line_5(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"TBL"),team(_,"MTL").
sal_boosted_def_line_5(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),nationality(_,"CZECHIA"),team(_,"VAN").
sal_boosted_def_line_5(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"NSH"),team(_,"DAL").
sal_boosted_def_line_5(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"WSH"),team(_,"PHI").
sal_boosted_def_line_5(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"FANT"),team(_,"TOR").
sal_boosted_def_line_5(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"FANT"),team(_,"DET").
sal_boosted_def_line_5(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"NYR"),team(_,"NYI").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"CHI"),team(P2,"CHI").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"STL"),team(P2,"STL").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"CGY"),team(P2,"CGY").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"CAR"),team(P2,"CAR").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"LAK"),team(_,"ANA").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(P1,"TOTW"),card_type(P2,"TOTW").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"TBL"),card_type(_,"HH").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"NY"),team(_,"BOS").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"VAN"),team(_,"TOR").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"OTT"),team(_,"MIN").
sal_boosted_def_line_6(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"MTL"),team(P2,"MTL").
sal_boosted_def_line_7(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"STL"),card_type(_,"CAP").
sal_boosted_def_line_7(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"EVT"),card_type(_,"NG").
sal_boosted_def_line_10(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"NYR"),team(P2,"NYR").
sal_boosted_def_line_10(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),nationality(_,"CZECHIA"),team(_,"VAN").
sal_boosted_def_line_10(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"FANT"),team(_,"MTL").
sal_boosted_def_line_10(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),nationality(_,"USA"),nationality(_,"CANADA").
sal_boosted_def_line_15(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(P1,"FANT"),card_type(P2,"FANT").

defense_line_sal_combination(A,B) :- defense_line(A,B), sal_boosted_def_line_5(A,B),  salary(A,S1), salary(B,S2), S1+S2 <= salary_cap + salary_cap_boost_5.
defense_line_sal_combination(A,B) :- defense_line(A,B), sal_boosted_def_line_6(A,B),  salary(A,S1), salary(B,S2), S1+S2 <= salary_cap + salary_cap_boost_6.
defense_line_sal_combination(A,B) :- defense_line(A,B), sal_boosted_def_line_7(A,B),  salary(A,S1), salary(B,S2), S1+S2 <= salary_cap + salary_cap_boost_7.
defense_line_sal_combination(A,B) :- defense_line(A,B), sal_boosted_def_line_10(A,B), salary(A,S1), salary(B,S2), S1+S2 <= salary_cap + salary_cap_boost_10.
defense_line_sal_combination(A,B) :- defense_line(A,B), sal_boosted_def_line_15(A,B), salary(A,S1), salary(B,S2), S1+S2 <= salary_cap + salary_cap_boost_15.
{ best_defense_line_sal_combination(A,B) : defense_line_sal_combination(A,B) } <= 50.
#maximize{ O1+O2@0,A,B : best_defense_line_sal_combination(A,B), ovr(A,O1), ovr(B,O2) }.

#show best_defense_line_sal_combination/2.