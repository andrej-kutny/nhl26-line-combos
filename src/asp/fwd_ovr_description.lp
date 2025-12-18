ovr_boosted_fwd_line(A,B,C) :- ovr_boosted_fwd_line_1(A,B,C).
ovr_boosted_fwd_line(A,B,C) :- ovr_boosted_fwd_line_2(A,B,C).

ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,"SWEDEN"),card_type(_,"COM"),team(_,"NSH").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"LAK"),team(_,"SJS"),card_type(_,"COM").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"COM"),team(_,"SJS"),card_type(_,"NG").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(P1,"CHEL"),card_type(P2,"CHEL"),card_type(P3,"CHEL").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"SPOT"),team(_,"SJS"),card_type(_,"ICON").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"TBL"),team(_,"BUF"),team(_,"DET").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,"FINLAND"),card_type(_,"NG"),team(_,"NIA").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"STL"),card_type(_,"NG"),nationality(_,"CANADA").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"HH"),card_type(_,"ICON"),card_type(_,"FANT").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"NG"),team(_,"PHI"),team(_,"WSH").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"TOTW"),team(_,"FLA"),team(_,"NYI").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"DAL"),team(_,"WPG"),card_type(_,"NG").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,"SWEDEN"),card_type(_,"ROOK"),team(_,"TOR").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,"GERMANY"),card_type(_,"XP"),team(_,"EDM").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"EDM"),card_type(_,"ICON"),card_type(_,"ALUM").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"MTL"),team(_,"TOR"),team(_,"OTT").
ovr_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"NY"),team(_,"OTT"),team(_,"VAN").
ovr_boosted_fwd_line_2(A,B,C) :- forward_line(A,B,C), forward_card(A,P1), forward_card(B,P2), forward_card(C,P3), team(_,"TBL"), card_type(_,"COM"), team(_,"WSH").

total_ovr_fwd(A,B,C,TOTAL_OVERALL) :- ovr_boosted_fwd_line_1(A,B,C), ovr(A,O1), ovr(B,O2), ovr(C,O3), TOTAL_OVERALL = O1+O2+O3+overall_bonus_fwd_1.
total_ovr_fwd(A,B,C,TOTAL_OVERALL) :- ovr_boosted_fwd_line_2(A,B,C), ovr(A,O1), ovr(B,O2), ovr(C,O3), TOTAL_OVERALL = O1+O2+O3+overall_bonus_fwd_2.
forward_line_ovr_combination(A,B,C) :- forward_line(A,B,C), ovr_boosted_fwd_line(A,B,C).
{ best_forward_line_ovr_combination(A,B,C) : forward_line_ovr_combination(A,B,C) } <= 50.
#maximize{ TOTAL_OVERALL@0,A,B,C : best_forward_line_ovr_combination(A,B,C), total_ovr_fwd(A,B,C,TOTAL_OVERALL) }.

#show best_forward_line_ovr_combination/3.