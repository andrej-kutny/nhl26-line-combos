ap_boosted_def_line(A,B) :- ap_boosted_def_line_2(A,B).
ap_boosted_def_line(A,B) :- ap_boosted_def_line_4(A,B).
ap_boosted_def_line(A,B) :- ap_boosted_def_line_8(A,B).

ap_boosted_def_line_2(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(P1,"COM"),card_type(P2,"COM").
ap_boosted_def_line_2(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"SEA"),team(_,"EDM").
ap_boosted_def_line_2(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"WPG"),team(_,"CHI").
ap_boosted_def_line_2(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"UTA"),team(_,"VGK").
ap_boosted_def_line_2(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"CBJ"),team(_,"FLA").
ap_boosted_def_line_2(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),card_type(_,"XP"),team(_,"DET").
ap_boosted_def_line_4(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"CAR"),team(_,"NJD").
ap_boosted_def_line_4(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"MTL"),team(_,"BOS").
ap_boosted_def_line_4(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"OTT"),team(_,"NY").
ap_boosted_def_line_4(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"SEA"),team(_,"TOR").
ap_boosted_def_line_4(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(_,"MTL"),team(_,"OTT").
ap_boosted_def_line_8(A,B) :- defense_line(A,B),defense_card(A,P1),defense_card(B,P2),team(P1,"CHI"),team(P2,"CHI").

total_ap_def(A,B,AP) :- ap_boosted_def_line_2(A,B),  AP = ability_points_bonus_def_2.
total_ap_def(A,B,AP) :- ap_boosted_def_line_4(A,B),  AP = ability_points_bonus_def_4.
total_ap_def(A,B,AP) :- ap_boosted_def_line_8(A,B),  AP = ability_points_bonus_def_8.
defense_line_ap_combination(A,B) :- defense_line(A,B), ap_boosted_def_line(A,B).
{ best_defense_line_ap_combination(A,B) : defense_line_ap_combination(A,B) } <= 50.
#maximize{ AP@0,A,B : best_defense_line_ap_combination(A,B), total_ap_def(A,B,AP) }.

#show best_defense_line_ap_combination/2.