% Collect potential lines from all criteria
potential_fwd_line(A,B,C) :- best_forward_line_sal_combination(A,B,C).
potential_fwd_line(A,B,C) :- best_forward_line_ovr_combination(A,B,C).
potential_fwd_line(A,B,C) :- best_forward_line_ap_combination(A,B,C).

% Select best lines from the potential pool
{ fwd_best_combination(A,B,C) : potential_fwd_line(A,B,C) } <= 50.

#maximize{ TOTAL_OVERALL*w_ovr+AP*w_ap@0,A,B,C : fwd_best_combination(A,B,C), total_ovr_fwd(A,B,C,TOTAL_OVERALL), total_ap_fwd(A,B,C,AP) }.
