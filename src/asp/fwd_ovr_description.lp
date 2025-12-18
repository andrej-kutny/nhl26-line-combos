ovr_boosted_fwd_line(A,B,C,BOOST_VALUE) :- boosted_fwd_line(A,B,C,"OVR",BOOST_VALUE,_,_,_).

total_ovr_fwd(A,B,C,TOTAL_OVERALL) :- ovr_boosted_fwd_line(A,B,C,BOOST_VALUE), ovr(A,O1), ovr(B,O2), ovr(C,O3), TOTAL_OVERALL = O1+O2+O3+BOOST_VALUE*w_ovr.
forward_line_ovr_combination(A,B,C) :- forward_line(A,B,C), ovr_boosted_fwd_line(A,B,C,_).
{ best_forward_line_ovr_combination(A,B,C) : forward_line_ovr_combination(A,B,C) } <= 100.
#maximize{ TOTAL_OVERALL@0,A,B,C : best_forward_line_ovr_combination(A,B,C), total_ovr_fwd(A,B,C,TOTAL_OVERALL) }.