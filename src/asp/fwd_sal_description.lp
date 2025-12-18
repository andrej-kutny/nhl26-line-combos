sal_boosted_fwd_line(A,B,C) :- sal_boosted_fwd_line_5(A,B,C).
sal_boosted_fwd_line(A,B,C) :- sal_boosted_fwd_line_6(A,B,C).
sal_boosted_fwd_line(A,B,C) :- sal_boosted_fwd_line_7(A,B,C).
sal_boosted_fwd_line(A,B,C) :- sal_boosted_fwd_line_9(A,B,C).
sal_boosted_fwd_line(A,B,C) :- sal_boosted_fwd_line_20(A,B,C).

sal_boosted_fwd_line_5(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"VAN"),team(_,"SEA"),team(_,"SJS").
sal_boosted_fwd_line_6(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"ANA"),team(P2,"ANA"),team(P3,"ANA").
sal_boosted_fwd_line_6(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"BOS"),team(P2,"BOS"),team(P3,"BOS").
sal_boosted_fwd_line_6(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"TOR"),team(_,"OTT"),nationality(_,"SLOVAKIA").
sal_boosted_fwd_line_7(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(P1,"SWEDEN"),nationality(P2,"SWEDEN"),nationality(P3,"SWEDEN").
sal_boosted_fwd_line_7(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(P1,"USA"),nationality(P2,"USA"),nationality(P3,"USA").
sal_boosted_fwd_line_7(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"CAP"),team(_,"NJD"),team(_,"PIT").
sal_boosted_fwd_line_7(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"EDM"),team(_,"COL"),team(_,"MIN").
sal_boosted_fwd_line_7(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"NYR"),team(_,"DET"),team(_,"CHI").
sal_boosted_fwd_line_9(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"MTL"),team(_,"NY"),team(_,"MIN").
sal_boosted_fwd_line_9(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"BOS"),team(_,"MIN"),team(_,"OTT").
sal_boosted_fwd_line_9(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"TOR"),team(_,"VAN"),team(_,"MTL").
sal_boosted_fwd_line_9(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"CAP"),team(_,"TOR"),team(_,"SEA").
sal_boosted_fwd_line_20(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(P1,"FANT"),card_type(P2,"FANT"),card_type(P3,"FANT").

forward_line_sal_combination(A,B,C) :- sal_boosted_fwd_line_5(A,B,C),  salary(A,S1), salary(B,S2), salary(C,S3), S1+S2+S3 <= salary_cap + salary_cap_boost_5.
forward_line_sal_combination(A,B,C) :- sal_boosted_fwd_line_6(A,B,C),  salary(A,S1), salary(B,S2), salary(C,S3), S1+S2+S3 <= salary_cap + salary_cap_boost_6.
forward_line_sal_combination(A,B,C) :- sal_boosted_fwd_line_7(A,B,C),  salary(A,S1), salary(B,S2), salary(C,S3), S1+S2+S3 <= salary_cap + salary_cap_boost_7.
forward_line_sal_combination(A,B,C) :- sal_boosted_fwd_line_9(A,B,C),  salary(A,S1), salary(B,S2), salary(C,S3), S1+S2+S3 <= salary_cap + salary_cap_boost_9.
forward_line_sal_combination(A,B,C) :- sal_boosted_fwd_line_20(A,B,C), salary(A,S1), salary(B,S2), salary(C,S3), S1+S2+S3 <= salary_cap + salary_cap_boost_20.
{ best_forward_line_sal_combination(A,B,C) : forward_line_sal_combination(A,B,C) } <= 50.
#maximize{ O1+O2+O3@0,A,B,C : best_forward_line_sal_combination(A,B,C), ovr(A,O1), ovr(B,O2), ovr(C,O3) }.

#show best_forward_line_sal_combination/3.