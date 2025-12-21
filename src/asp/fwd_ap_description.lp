ap_boosted_fwd_line(A,B,C,BOOST_VALUE) :- boosted_fwd_line(A,B,C,"AP",BOOST_VALUE,_,_,_).

total_ap_fwd(A,B,C,AP) :- forward_line(A,B,C), not ap_boosted_fwd_line(A,B,C,_), AP = 0.
total_ap_fwd(A,B,C,AP) :- ap_boosted_fwd_line(A,B,C,BOOST_VALUE), AP = BOOST_VALUE * w_ap.
forward_line_ap_combination(A,B,C) :- forward_line(A,B,C).
{ best_forward_line_ap_combination(A,B,C) : forward_line_ap_combination(A,B,C) } <= 100.
#maximize{ AP@0,A,B,C : best_forward_line_ap_combination(A,B,C), total_ap_fwd(A,B,C,AP) }.