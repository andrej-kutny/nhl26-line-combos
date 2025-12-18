ap_boosted_def_line(A,B,BOOST_VALUE) :- boosted_def_line(A,B,"AP",BOOST_VALUE,_,_).

total_ap_def(A,B,AP) :- ap_boosted_def_line(A,B,BOOST_VALUE), AP = BOOST_VALUE*w_ap.
defense_line_ap_combination(A,B) :- defense_line(A,B), ap_boosted_def_line(A,B,_).
{ best_defense_line_ap_combination(A,B) : defense_line_ap_combination(A,B) } <= 50.
#maximize{ AP@0,A,B : best_defense_line_ap_combination(A,B), total_ap_def(A,B,AP) }.