sal_boosted_fwd_line(A,B,C,BOOST_VALUE) :- boosted_fwd_line(A,B,C,"SAL",BOOST_VALUE,_,_,_).

forward_line_sal_combination(A,B,C) :- sal_boosted_fwd_line(A,B,C,BOOST_VALUE),  salary(A,S1), salary(B,S2), salary(C,S3), S1+S2+S3 <= salary_cap + BOOST_VALUE*w_sal.
{ best_forward_line_sal_combination(A,B,C) : forward_line_sal_combination(A,B,C) } <= 100.
#maximize{ O1+O2+O3@0,A,B,C : best_forward_line_sal_combination(A,B,C), ovr(A,O1), ovr(B,O2), ovr(C,O3) }.