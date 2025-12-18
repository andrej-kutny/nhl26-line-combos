ovr_boosted_def_line(A,B,BOOST_VALUE) :- boosted_def_line(A,B,"OVR",BOOST_VALUE,_,_).

total_ovr_def(A,B,TOTAL_OVERALL) :- ovr_boosted_def_line(A,B,BOOST_VALUE), ovr(A,O1), ovr(B,O2), TOTAL_OVERALL = O1+O2+BOOST_VALUE*w_ovr.
defense_line_ovr_combination(A,B) :- defense_line(A,B), ovr_boosted_def_line(A,B,_).
{ best_defense_line_ovr_combination(A,B) : defense_line_ovr_combination(A,B) } <= 50.
#maximize{ TOTAL_OVERALL@0,A,B : best_defense_line_ovr_combination(A,B), total_ovr_def(A,B,TOTAL_OVERALL) }.