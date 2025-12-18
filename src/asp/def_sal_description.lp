sal_boosted_def_line(A,B,BOOST_VALUE) :- boosted_def_line(A,B,"SAL",BOOST_VALUE,_,_).

defense_line_sal_combination(A,B) :- defense_line(A,B), sal_boosted_def_line(A,B,BOOST_VALUE),  salary(A,S1), salary(B,S2), S1+S2 <= salary_cap + BOOST_VALUE * w_sal.
{ best_defense_line_sal_combination(A,B) : defense_line_sal_combination(A,B) } <= 50.
#maximize{ O1+O2@0,A,B : best_defense_line_sal_combination(A,B), ovr(A,O1), ovr(B,O2) }.