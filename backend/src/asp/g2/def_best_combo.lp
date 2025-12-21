% Collect potential lines from all criteria
potential_def_line(A,B) :- best_defense_line_sal_combination(A,B).
potential_def_line(A,B) :- best_defense_line_ovr_combination(A,B).
potential_def_line(A,B) :- best_defense_line_ap_combination(A,B).

% Select best lines from the potential pool
{ def_best_combination(A,B) : potential_def_line(A,B) } <= 50.

#maximize{ TOTAL_OVERALL*w_ovr+AP*w_ap@0,A,B : def_best_combination(A,B), total_ovr_def(A,B,TOTAL_OVERALL), total_ap_def(A,B,AP) }.
