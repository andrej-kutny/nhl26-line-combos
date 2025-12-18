ap_boosted_fwd_line(A,B,C) :- ap_boosted_fwd_line_1(A,B,C).
ap_boosted_fwd_line(A,B,C) :- ap_boosted_fwd_line_3(A,B,C).
ap_boosted_fwd_line(A,B,C) :- ap_boosted_fwd_line_5(A,B,C).
ap_boosted_fwd_line(A,B,C) :- ap_boosted_fwd_line_6(A,B,C).
ap_boosted_fwd_line(A,B,C) :- ap_boosted_fwd_line_12(A,B,C).

ap_boosted_fwd_line_1(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"HUTC"),team(_,"MTL"),card_type(_,"GB").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"PHI"),team(P2,"PHI"),team(P3,"PHI").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"WPG"),team(P2,"WPG"),team(P3,"WPG").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"COL"),team(P2,"COL"),team(P3,"COL").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"ANA"),team(P2,"ANA"),team(P3,"ANA").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"BOS"),team(P2,"BOS"),team(P3,"BOS").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(P1,"COM"),card_type(P2,"COM"),card_type(P3,"COM").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"CAP"),team(_,"UTA"),team(_,"STL").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"CAP"),team(_,"TOR"),team(_,"CGY").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"UTA"),card_type(_,"FANT"),team(_,"CHI").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"TOTW"),card_type(_,"SOTM"),card_type(_,"TOTW").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"CAP"),team(_,"OTT"),team(_,"CBJ").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"ANA"),card_type(_,"SOTM"),team(_,"LAK").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"GB"),team(_,"PIT"),team(_,"CAR").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"COM"),team(_,"SJS"),nationality(_,"CZECHIA").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"DET"),team(_,"MTL"),nationality(_,"DENMARK").
ap_boosted_fwd_line_3(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"TBL"),team(_,"BUF"),card_type(_,"CAP").
ap_boosted_fwd_line_5(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),nationality(_,"USA"),card_type(_,"NG"),team(_,"PIT").
ap_boosted_fwd_line_6(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"NY"),team(_,"MTL"),team(_,"BOS").
ap_boosted_fwd_line_6(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(_,"MIN"),team(_,"SEA"),team(_,"VAN").
ap_boosted_fwd_line_6(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),card_type(_,"HH"),team(_,"DET"),team(_,"SEA").
ap_boosted_fwd_line_12(A,B,C) :- forward_line(A,B,C),forward_card(A,P1),forward_card(B,P2),forward_card(C,P3),team(P1,"DET"),team(P2,"DET"),team(P3,"DET").

total_ap_fwd(A,B,C,AP) :- ap_boosted_fwd_line_1(A,B,C),  AP = ability_points_bonus_fwd_1.
total_ap_fwd(A,B,C,AP) :- ap_boosted_fwd_line_3(A,B,C),  AP = ability_points_bonus_fwd_3.
total_ap_fwd(A,B,C,AP) :- ap_boosted_fwd_line_5(A,B,C),  AP = ability_points_bonus_fwd_5.
total_ap_fwd(A,B,C,AP) :- ap_boosted_fwd_line_6(A,B,C),  AP = ability_points_bonus_fwd_6.
total_ap_fwd(A,B,C,AP) :- ap_boosted_fwd_line_12(A,B,C), AP = ability_points_bonus_fwd_12.
forward_line_ap_combination(A,B,C) :- forward_line(A,B,C), ap_boosted_fwd_line(A,B,C).
{ best_forward_line_ap_combination(A,B,C) : forward_line_ap_combination(A,B,C) } <= 50.
#maximize{ AP@0,A,B,C : best_forward_line_ap_combination(A,B,C), total_ap_fwd(A,B,C,AP) }.

#show best_forward_line_ap_combination/3.