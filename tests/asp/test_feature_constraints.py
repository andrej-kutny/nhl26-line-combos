import clingo
import pytest

import os

def solve(files, extra_rules: str = "", consts=None, ctl_opts=None):
    # Determine base path relative to this test file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    
    abs_files = []
    for f in files:
        if not os.path.isabs(f):
            abs_files.append(os.path.join(root_dir, f))
        else:
            abs_files.append(f)

    opts = list(ctl_opts or [])
    if consts:
        for k, v in consts.items():
            opts.append(f"-c{k}={v}")
    ctl = clingo.Control(opts)
    for f in abs_files:
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

def test_duplicate_player_id_check_fwd():
    """
    Test that same player_id can't appear in the lineup more than once.
    """
    extra = r'''
        player("K1", "P_A", "USA", "ABC", "BASE", 93, 10).
        player("K2", "P_A", "USA", "ABC", "BASE", 92, 10).
        player("K3", "P_B", "USA", "ABC", "BASE", 91, 10).
        player("K4", "P_C", "USA", "ABC", "BASE", 60, 5).
        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/fwd_main.lp", "backend/src/asp/g2/fwd_best_combo.lp",
         "backend/src/asp/g2/fwd_ovr_description.lp", "backend/src/asp/g2/fwd_sal_description.lp", "backend/src/asp/g2/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    
    expected_set_1 = tuple(sorted(['"K1"', '"K3"', '"K4"']))
    
    assert expected_set_1 in results
    assert not any('"K1"' in r and '"K2"' in r for r in results)

def test_ovr_boost_preference():
    extra = r'''
        % Synergy: 3 players from Team SJS gives +1 OVR
        forward_combo(100, 1, "OVR", team("SJS"), team("SJS"), team("SJS")).

        player("K1", "P1", "USA", "SJS", "BASE", 88, 10).
        player("K2", "P2", "USA", "DET", "BASE", 90, 10).
        player("K3", "P3", "USA", "SJS", "BASE", 90, 10).
        player("K4", "P4", "USA", "SJS", "BASE", 90, 10).
        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/fwd_main.lp", "backend/src/asp/g2/fwd_best_combo.lp",
         "backend/src/asp/g2/fwd_ovr_description.lp", "backend/src/asp/g2/fwd_sal_description.lp", "backend/src/asp/g2/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 3, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    
    expected = tuple(sorted(['"K1"', '"K3"', '"K4"']))
    assert expected in results

def test_salary_cap_fit():
    extra = r'''
        player("K1", "P1", "USA", "SJS", "BASE", 90, 40).        player("K2", "P2", "USA", "SJS", "BASE", 80, 30).        player("K3", "P3", "USA", "SJS", "BASE", 70, 20).        player("K4", "P4", "USA", "SJS", "BASE", 60, 10).        #show best_forward_line_sal_combination/3.
    '''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/fwd_main.lp", "backend/src/asp/g2/fwd_sal_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 80, "w_sal": 1},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "best_forward_line_sal_combination")}
    
    expected = tuple(sorted(['"K1"', '"K2"', '"K4"']))
    assert expected in results
    assert tuple(sorted(['"K1"', '"K2"', '"K3"'])) not in results

def test_salary_cap_boost_activation():
    extra = r'''
        % Synergy: 3 SJS players gives +15 SAL cap
        forward_combo(200, 15, "SAL", team("SJS"), team("SJS"), team("SJS")).

        player("K1", "P1", "USA", "SJS", "BASE", 90, 40).        player("K2", "P2", "USA", "SJS", "BASE", 80, 30).        player("K3", "P3", "USA", "SJS", "BASE", 70, 20).        player("K4", "P4", "USA", "DET", "BASE", 60, 10).        #show best_forward_line_sal_combination/3.
    '''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/fwd_main.lp", "backend/src/asp/g2/fwd_sal_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 80, "w_sal": 1},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "best_forward_line_sal_combination")}
    
    expected = tuple(sorted(['"K1"', '"K2"', '"K3"']))
    assert expected in results

# --- Playerset Limitation Tests ---

def test_playerset_limitation_1_set_fwd():
    extra = r'''
        % Pool: P4 must be in the line.
        required_player("P4").

        player("K1", "P1", "USA", "ABC", "BASE", 90, 10).        player("K2", "P2", "USA", "ABC", "BASE", 90, 10).        player("K3", "P3", "USA", "ABC", "BASE", 90, 10).        player("K4", "P4", "USA", "ABC", "BASE", 60, 10).        % Constraint: ALL generated lines must include required_player
        :- fwd_best_combination(A,B,C), required_player(P), not has_card(P,A), not has_card(P,B), not has_card(P,C).

        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/fwd_main.lp", "backend/src/asp/g2/fwd_best_combo.lp", 
         "backend/src/asp/g2/fwd_ovr_description.lp", "backend/src/asp/g2/fwd_sal_description.lp", "backend/src/asp/g2/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    
    assert any('"K4"' in r for r in results)
    assert not any(r == tuple(sorted(['"K1"', '"K2"', '"K3"'])) for r in results)

def test_playerset_limitation_2_sets_def():
    extra = r'''
        pool("A", "P1").
        pool("B", "P2").

        player("K1", "P1", "USA", "ABC", "BASE", 60, 10).        player("K2", "P2", "USA", "ABC", "BASE", 60, 10).        player("K3", "P3", "USA", "ABC", "BASE", 90, 10).        player("K4", "P4", "USA", "ABC", "BASE", 90, 10).        % Helper: Line has player from Pool
        line_has_pool(PoolID, A, B) :- def_best_combination(A,B), pool(PoolID, P), has_card(P, A).
        line_has_pool(PoolID, A, B) :- def_best_combination(A,B), pool(PoolID, P), has_card(P, B).

        % Constraint: Must satisfy both pools for EVERY line
        :- def_best_combination(A,B), pool(PoolID, _), not line_has_pool(PoolID, A, B).
        
        % Force at least one result
        :- not 1 { def_best_combination(A,B) }.

        #show def_best_combination/2.
    '''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/def_main.lp", "backend/src/asp/g2/def_best_combo.lp", 
         "backend/src/asp/g2/def_ovr_description.lp", "backend/src/asp/g2/def_sal_description.lp", "backend/src/asp/g2/def_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "def_best_combination")}
    
    expected = tuple(sorted(['"K1"', '"K2"']))
    assert expected in results
    assert not any(r == tuple(sorted(['"K3"', '"K4"'])) for r in results)

def test_playerset_limitation_3_sets_fwd():
    extra = r'''
        pool("A", "P1").
        pool("B", "P2").
        pool("C", "P3").

        player("K1", "P1", "USA", "ABC", "BASE", 60, 10).        player("K2", "P2", "USA", "ABC", "BASE", 60, 10).        player("K3", "P3", "USA", "ABC", "BASE", 60, 10).        player("K4", "P4", "USA", "ABC", "BASE", 90, 10).        player("K5", "P5", "USA", "ABC", "BASE", 90, 10).        player("K6", "P6", "USA", "ABC", "BASE", 90, 10).        % Helper
        line_has_pool(PoolID, A, B, C) :- fwd_best_combination(A,B,C), pool(PoolID, P), has_card(P, A).
        line_has_pool(PoolID, A, B, C) :- fwd_best_combination(A,B,C), pool(PoolID, P), has_card(P, B).
        line_has_pool(PoolID, A, B, C) :- fwd_best_combination(A,B,C), pool(PoolID, P), has_card(P, C).

        % Constraint
        :- fwd_best_combination(A,B,C), pool(PoolID, _), not line_has_pool(PoolID, A, B, C).

        #show fwd_best_combination/3.
    '''
    
    res, models = solve(
        ["backend/src/asp/g2/common.lp", "backend/src/asp/g2/fwd_main.lp", "backend/src/asp/g2/fwd_best_combo.lp", 
         "backend/src/asp/g2/fwd_ovr_description.lp", "backend/src/asp/g2/fwd_sal_description.lp", "backend/src/asp/g2/fwd_ap_description.lp"],
        extra_rules=extra,
        consts={"salary_cap": 999, "w_ovr": 1, "w_ap": 0, "w_sal": 0},
        ctl_opts=[]
    )
    
    assert res.satisfiable
    results = {tuple(sorted(map(sym_to_str, s.arguments))) for s in shown(models, "fwd_best_combination")}
    
    expected = tuple(sorted(['"K1"', '"K2"', '"K3"']))
    assert expected in results
    assert not any(r == tuple(sorted(['"K4"', '"K5"', '"K6"'])) for r in results)
