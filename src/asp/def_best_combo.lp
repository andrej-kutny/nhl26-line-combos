{ def_best_combination(A,B) : best_defense_line_sal_combination(A,B), best_defense_line_ovr_combination(A,B), best_defense_line_ap_combination(A,B) } <= 50.
#maximize{ TOTAL_OVERALL*w_ovr+AP*w_ap@0,A,B : def_best_combination(A,B), total_ovr_def(A,B,TOTAL_OVERALL), total_ap_def(A,B,AP) }.
