import clingo
import pytest

# Helper functions copied from test_asp_descriptions.py
def solve(files, extra_rules: str = "", consts=None, ctl_opts=None):
    opts = list(ctl_opts or [])
    if consts:
        for k, v in consts.items():
            opts.append(f"-c{k}={v}")
    ctl = clingo.Control(opts)
    for f in files:
        ctl.load(f)
    if extra_rules.strip():
        ctl.add("extra", [], extra_rules)
        ctl.ground([("base", []), ("extra", [])])
    else:
        ctl.ground([("base", [])])
    models = []
    def on_model(m: clingo.Model):
        models.append(m.symbols(shown=True))
    res = ctl.solve(on_model=on_model)
    return res, models

def shown(models, name):
    if not models:
        return []
    return [s for s in models[-1] if s.name == name]

def sym_to_str(sym: clingo.Symbol) -> str:
    return str(sym)

# Common data setup
COMMON_SETUP = r'''
    event("SPOT"; "ICON"; "BASE"; "NG"; "EVT").
    club("SJS"; "ABC"; "GHI"; "DEF"; "DET").
    country("ROU"; "HUN"; "MDA"; "USA"; "CAN").
'''

def test_duplicate_player_id_check_fwd():
    """
    Test that same player_id can't appear in the lineup more than once.
    """
    extra = COMMON_SETUP + r'''
        id("P_A"). type("P_A", "player"). nationality("P_A","USA").
        id("P_B"). type("P_B", "player"). nationality("P_B","USA").
        id("P_C"). type("P_C", "player"). nationality("P_C","USA").

        % Card 1: Player A, 93
        id("K1"). type("K1","card"). has_card("P_A","K1").
        position("K1", "C"). ovr("K1", 93). salary("K1", 10). team("K1","ABC"). card_type("K1","BASE").

        % Card 2: Player A, 92 (Different Card ID, Same Player ID)
        id("K2"). type("K2","card"). has_card("P_A","K2").
        position("K2", "LW"). ovr("K2", 92). salary("K2", 10). team("K2","ABC"). card_type("K2","BASE").

        % Card 3: Player B, 91
        id("K3"). type("K3","card"). has_card("P_B","K3").
        position("K3", "RW"). ovr("K3", 91). salary("K3", 10). team("K3","ABC"). card_type("K3","BASE").

        % Card 4: Player C, 60
        id("K4"). type("K4","card"). has_card("P_C","K4").
        position("K4", "LW"). ovr("K4", 60). salary("K4", 5). team("K4","ABC"). card_type("K4","BASE").

        #show fwd_best_combination/3.
        #show best_forward_line_sal_combination/3.
        #show best_forward_line_ap_combination/3.

    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_best_combo.lp", 
         "./src/asp/fwd_ovr_description.lp", "./src/asp/fwd_sal_description.lp", "./src/asp/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    ovr_results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "best_forward_line_ovr_combination")}
    sal_results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "best_forward_line_sal_combination")}
    ap_results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "best_forward_line_ap_combination")}
    
    print(f"\nDEBUG test_duplicate_player_id_check_fwd results: {results}")
    print(f"DEBUG best_forward_line_ovr_combination: {ovr_results}")
    print(f"DEBUG best_forward_line_sal_combination: {sal_results}")
    print(f"DEBUG best_forward_line_ap_combination: {ap_results}")

    # Expected: K1, K3, K4 or K2, K3, K4.
    expected_set_1 = tuple(sorted(['"K1"', '"K3"', '"K4"']))
    expected_set_2 = tuple(sorted(['"K2"', '"K3"', '"K4"']))
    
    assert any(r == expected_set_1 or r == expected_set_2 for r in results)
    assert not any(r == tuple(sorted(['"K1"', '"K2"', '"K3"'])) for r in results)


def test_ovr_boost_preference():
    extra = COMMON_SETUP + r'''
        % Synergy: 3 players from Team SJS gives +1 OVR
        forward_combo(100, 1, "OVR", club("SJS"), club("SJS"), club("SJS")).

        id("P1"). type("P1", "player"). nationality("P1","USA").
        id("P2"). type("P2", "player"). nationality("P2","USA").
        id("P3"). type("P3", "player"). nationality("P3","USA").
        id("P4"). type("P4", "player"). nationality("P4","USA").

        % K1: 88 OVR, SJS
        id("K1"). type("K1","card"). has_card("P1","K1").
        position("K1", "C"). ovr("K1", 88). salary("K1", 10). team("K1","SJS"). card_type("K1","BASE").

        % K2: 90 OVR, DET
        id("K2"). type("K2","card"). has_card("P2","K2").
        position("K2", "C"). ovr("K2", 90). salary("K2", 10). team("K2","DET"). card_type("K2","BASE").

        % K3: 90 OVR, SJS
        id("K3"). type("K3","card"). has_card("P3","K3").
        position("K3", "RW"). ovr("K3", 90). salary("K3", 10). team("K3","SJS"). card_type("K3","BASE").

        % K4: 90 OVR, SJS
        id("K4"). type("K4","card"). has_card("P4","K4").
        position("K4", "LW"). ovr("K4", 90). salary("K4", 10). team("K4","SJS"). card_type("K4","BASE").

        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_best_combo.lp", 
         "./src/asp/fwd_ovr_description.lp", "./src/asp/fwd_sal_description.lp", "./src/asp/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 3, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    print(f"\nDEBUG test_ovr_boost_preference results: {results}")
    
    expected = tuple(sorted(['"K1"', '"K3"', '"K4"']))
    assert expected in results
    assert tuple(sorted(['"K2"', '"K3"', '"K4"'])) not in results

def test_salary_cap_fit():
    extra = COMMON_SETUP + r'''
        id("P1"). type("P1", "player"). nationality("P1","USA").
        id("P2"). type("P2", "player"). nationality("P2","USA").
        id("P3"). type("P3", "player"). nationality("P3","USA").
        id("P4"). type("P4", "player"). nationality("P4","USA").

        % K1: 40 Sal, 90 OVR (C)
        id("K1"). type("K1","card"). has_card("P1","K1").
        position("K1", "C"). ovr("K1", 90). salary("K1", 40). team("K1","SJS"). card_type("K1","BASE").

        % K2: 30 Sal, 80 OVR (LW)
        id("K2"). type("K2","card"). has_card("P2","K2").
        position("K2", "LW"). ovr("K2", 80). salary("K2", 30). team("K2","SJS"). card_type("K2","BASE").

        % K3: 20 Sal, 70 OVR (RW)
        id("K3"). type("K3","card"). has_card("P3","K3").
        position("K3", "RW"). ovr("K3", 70). salary("K3", 20). team("K3","SJS"). card_type("K3","BASE").

        % K4: 10 Sal, 60 OVR (RW)
        id("K4"). type("K4","card"). has_card("P4","K4").
        position("K4", "RW"). ovr("K4", 60). salary("K4", 10). team("K4","SJS"). card_type("K4","BASE").

        #show best_forward_line_sal_combination/3.
    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_sal_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 80, "w_sal": 1},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "best_forward_line_sal_combination")}
    print(f"\nDEBUG test_salary_cap_fit results: {results}")
    
    expected = tuple(sorted(['"K1"', '"K2"', '"K4"']))
    assert expected in results
    assert tuple(sorted(['"K1"', '"K2"', '"K3"'])) not in results

def test_salary_cap_boost_activation():
    extra = COMMON_SETUP + r'''
        % Synergy: 3 SJS players gives +15 SAL cap
        forward_combo(200, 15, "SAL", club("SJS"), club("SJS"), club("SJS")).

        id("P1"). type("P1", "player"). nationality("P1","USA").
        id("P2"). type("P2", "player"). nationality("P2","USA").
        id("P3"). type("P3", "player"). nationality("P3","USA").
        id("P4"). type("P4", "player"). nationality("P4","USA").

        % K1: 40 Sal, 90 OVR (C) - SJS
        id("K1"). type("K1","card"). has_card("P1","K1").
        position("K1", "C"). ovr("K1", 90). salary("K1", 40). team("K1","SJS"). card_type("K1","BASE").

        % K2: 30 Sal, 80 OVR (LW) - SJS
        id("K2"). type("K2","card"). has_card("P2","K2").
        position("K2", "LW"). ovr("K2", 80). salary("K2", 30). team("K2","SJS"). card_type("K2","BASE").

        % K3: 20 Sal, 70 OVR (RW) - SJS
        id("K3"). type("K3","card"). has_card("P3","K3").
        position("K3", "RW"). ovr("K3", 70). salary("K3", 20). team("K3","SJS"). card_type("K3","BASE").

        % K4: 10 Sal, 60 OVR (RW) - DET (No synergy)
        id("K4"). type("K4","card"). has_card("P4","K4").
        position("K4", "RW"). ovr("K4", 60). salary("K4", 10). team("K4","DET"). card_type("K4","BASE").

        #show best_forward_line_sal_combination/3.
    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_sal_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 80, "w_sal": 1},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "best_forward_line_sal_combination")}
    print(f"\nDEBUG test_salary_cap_boost_activation results: {results}")
    
    expected = tuple(sorted(['"K1"', '"K2"', '"K3"']))
    assert expected in results

def test_salary_cap_synergy_preference_unlimited():
    extra = COMMON_SETUP + r'''
        % Synergy: 3 SJS players gives +2 OVR
        forward_combo(300, 2, "OVR", club("SJS"), club("SJS"), club("SJS")).

        id("P1"). type("P1", "player"). nationality("P1","USA").
        id("P2"). type("P2", "player"). nationality("P2","USA").
        id("P3"). type("P3", "player"). nationality("P3","USA").
        id("P4"). type("P4", "player"). nationality("P4","USA").
        id("P5"). type("P5", "player"). nationality("P5","USA").
        id("P6"). type("P6", "player"). nationality("P6","USA").

        % Line A (Expensive, No Synergy) - DET
        id("KA1"). type("KA1","card"). has_card("P1","KA1"). position("KA1", "C"). ovr("KA1", 90). salary("KA1", 100). team("KA1","DET"). card_type("KA1","BASE").
        id("KA2"). type("KA2","card"). has_card("P2","KA2"). position("KA2", "LW"). ovr("KA2", 90). salary("KA2", 100). team("KA2","DET"). card_type("KA2","BASE").
        id("KA3"). type("KA3","card"). has_card("P3","KA3"). position("KA3", "RW"). ovr("KA3", 90). salary("KA3", 100). team("KA3","DET"). card_type("KA3","BASE").

        % Line B (Cheap, Synergy) - SJS
        id("KB1"). type("KB1","card"). has_card("P4","KB1"). position("KB1", "C"). ovr("KB1", 89). salary("KB1", 10). team("KB1","SJS"). card_type("KB1","BASE").
        id("KB2"). type("KB2","card"). has_card("P5","KB2"). position("KB2", "LW"). ovr("KB2", 89). salary("KB2", 10). team("KB2","SJS"). card_type("KB2","BASE").
        id("KB3"). type("KB3","card"). has_card("P6","KB3"). position("KB3", "RW"). ovr("KB3", 89). salary("KB3", 10). team("KB3","SJS"). card_type("KB3","BASE").

        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_best_combo.lp", 
         "./src/asp/fwd_ovr_description.lp", "./src/asp/fwd_sal_description.lp", "./src/asp/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 9999, "w_ovr": 3, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    print(f"\nDEBUG test_salary_cap_synergy_preference_unlimited results: {results}")
    
    expected = tuple(sorted(['"KB1"', '"KB2"', '"KB3"']))
    assert expected in results

# --- Playerset Limitation Tests ---

def test_playerset_limitation_1_set_fwd():
    extra = COMMON_SETUP + r'''
        id("P1"). type("P1", "player"). nationality("P1","USA").
        id("P2"). type("P2", "player"). nationality("P2","USA").
        id("P3"). type("P3", "player"). nationality("P3","USA").
        id("P4"). type("P4", "player"). nationality("P4","USA").

        % Pool: P4 must be in the line.
        required_player("P4").

        % K1, K2, K3 are 90 OVR.
        id("K1"). type("K1","card"). has_card("P1","K1"). position("K1", "C"). ovr("K1", 90). salary("K1", 10). team("K1","ABC"). card_type("K1","BASE").
        id("K2"). type("K2","card"). has_card("P2","K2"). position("K2", "LW"). ovr("K2", 90). salary("K2", 10). team("K2","ABC"). card_type("K2","BASE").
        id("K3"). type("K3","card"). has_card("P3","K3"). position("K3", "RW"). ovr("K3", 90). salary("K3", 10). team("K3","ABC"). card_type("K3","BASE").

        % K4 is 60 OVR, but required.
        id("K4"). type("K4","card"). has_card("P4","K4"). position("K4", "RW"). ovr("K4", 60). salary("K4", 10). team("K4","ABC"). card_type("K4","BASE").

        % Constraint: Line must include required_player
        :- required_player(P), not 1 { fwd_best_combination(A,B,C) : has_card(P,A); fwd_best_combination(A,B,C) : has_card(P,B); fwd_best_combination(A,B,C) : has_card(P,C) }.

        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_best_combo.lp", 
         "./src/asp/fwd_ovr_description.lp", "./src/asp/fwd_sal_description.lp", "./src/asp/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    print(f"\nDEBUG test_playerset_limitation_1_set_fwd results: {results}")
    
    # Must include P4 (K4).
    # K1, K2, K3 = 270 (Filtered out by constraint).
    # K1, K2, K4 = 240.
    
    assert any('"K4"' in r for r in results)
    assert not any(r == tuple(sorted(['"K1"', '"K2"', '"K3"'])) for r in results)

def test_playerset_limitation_2_sets_def():
    extra = COMMON_SETUP + r'''
        id("P1"). type("P1", "player"). nationality("P1","USA").
        id("P2"). type("P2", "player"). nationality("P2","USA").
        id("P3"). type("P3", "player"). nationality("P3","USA").
        id("P4"). type("P4", "player"). nationality("P4","USA").

        pool("A", "P1").
        pool("B", "P2").

        % K1 (P1), K2 (P2) are low rated (60).
        % K3 (P3), K4 (P4) are high rated (90).
        
        id("K1"). type("K1","card"). has_card("P1","K1"). position("K1", "LD"). ovr("K1", 60). salary("K1", 10). team("K1","ABC"). card_type("K1","BASE").
        id("K2"). type("K2","card"). has_card("P2","K2"). position("K2", "RD"). ovr("K2", 60). salary("K2", 10). team("K2","ABC"). card_type("K2","BASE").
        id("K3"). type("K3","card"). has_card("P3","K3"). position("K3", "LD"). ovr("K3", 90). salary("K3", 10). team("K3","ABC"). card_type("K3","BASE").
        id("K4"). type("K4","card"). has_card("P4","K4"). position("K4", "RD"). ovr("K4", 90). salary("K4", 10). team("K4","ABC"). card_type("K4","BASE").

        % Constraint: Must satisfy both pools
        :- pool(PoolID, _), not 1 { def_best_combination(A,B) : has_card(P,A), pool(PoolID, P); def_best_combination(A,B) : has_card(P,B), pool(PoolID, P) }.

        #show def_best_combination/2.
    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/def_best_combo.lp", 
         "./src/asp/def_ovr_description.lp", "./src/asp/def_sal_description.lp", "./src/asp/def_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "def_best_combination")}
    print(f"\nDEBUG test_playerset_limitation_2_sets_def results: {results}")
    
    expected = tuple(sorted(['"K1"', '"K2"']))
    assert expected in results

def test_playerset_limitation_3_sets_fwd():
    extra = COMMON_SETUP + r'''
        id("P1"). type("P1", "player"). nationality("P1","USA").
        id("P2"). type("P2", "player"). nationality("P2","USA").
        id("P3"). type("P3", "player"). nationality("P3","USA").
        id("P4"). type("P4", "player"). nationality("P4","USA").
        id("P5"). type("P5", "player"). nationality("P5","USA").

        pool("A", "P1").
        pool("B", "P2").
        pool("C", "P3").

        % K1(P1), K2(P2), K3(P3) are low (60).
        % K4, K5, K6 are high (90).
        
        id("K1"). type("K1","card"). has_card("P1","K1"). position("K1", "C"). ovr("K1", 60). salary("K1", 10). team("K1","ABC"). card_type("K1","BASE").
        id("K2"). type("K2","card"). has_card("P2","K2"). position("K2", "LW"). ovr("K2", 60). salary("K2", 10). team("K2","ABC"). card_type("K2","BASE").
        id("K3"). type("K3","card"). has_card("P3","K3"). position("K3", "RW"). ovr("K3", 60). salary("K3", 10). team("K3","ABC"). card_type("K3","BASE").
        
        id("K4"). type("K4","card"). has_card("P4","K4"). position("K4", "C"). ovr("K4", 90). salary("K4", 10). team("K4","ABC"). card_type("K4","BASE").
        id("K5"). type("K5","card"). has_card("P4","K5"). position("K5", "LW"). ovr("K5", 90). salary("K5", 10). team("K5","ABC"). card_type("K5","BASE").
        id("K6"). type("K6","card"). has_card("P4","K6"). position("K6", "RW"). ovr("K6", 90). salary("K6", 10). team("K6","ABC"). card_type("K6","BASE").

        % Constraint
        :- pool(PoolID, _), not 1 { fwd_best_combination(A,B,C) : has_card(P,A), pool(PoolID, P); fwd_best_combination(A,B,C) : has_card(P,B), pool(PoolID, P); fwd_best_combination(A,B,C) : has_card(P,C), pool(PoolID, P) }.

        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["./src/asp/main_description.lp", "./src/asp/fwd_best_combo.lp", 
         "./src/asp/fwd_ovr_description.lp", "./src/asp/fwd_sal_description.lp", "./src/asp/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    print(f"\nDEBUG test_playerset_limitation_3_sets_fwd results: {results}")
    
    expected = tuple(sorted(['"K1"', '"K2"', '"K3"']))
    assert expected in results
