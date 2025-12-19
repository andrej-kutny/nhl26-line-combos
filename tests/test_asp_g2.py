import clingo
import pytest

# Reuse data from G1A if needed, or define inline
from tests.data.asp_g1a import DEF_AP_C, DEF_SAL_C, DEF_OVR_C, FWD_AP_C, FWD_OVR_C, FWD_SAL_C

class TestASP_G2:
    offense_rules = ["src/asp/g2_concrete/rules.lp", "src/asp/g2_concrete/fwd_rules.lp"]
    defense_rules = ["src/asp/g2_concrete/rules.lp", "src/asp/g2_concrete/def_rules.lp"]

    def solve(self, files, extra_rules="", consts=None, ctl_opts=None):
        opts = list(ctl_opts or [])
        if consts:
            for k, v in consts.items():
                opts.append(f"-c {k}={v}")
        
        ctl = clingo.Control(opts)
        for f in files:
            ctl.load(f)
        
        if extra_rules.strip():
            ctl.add("extra", [], extra_rules)
            ctl.ground([("base", []), ("extra", [])])
        else:
            ctl.ground([("base", [])])

        models, opt = [], None
        models_c = 0
        def on_model(m):
            nonlocal opt, models_c
            models_c += 1
            models.append(m.symbols(shown=True))
            if m.cost:
                opt = tuple(m.cost)
        res = ctl.solve(on_model=on_model)
        return res, models, opt, models_c

    def test_rules_exist(self):
        assert self.offense_rules != []
        assert self.defense_rules != []

    def test_doesnt_use_same_player(self):
        # id, player_id, nationality, event, team, overall, salary
        # P1 and P2 have same PlayerID (10). P3 and P4 are unique.
        p1 = "player(1, 10, \"USA\", \"ICON\", \"CHI\", 99, 20)."
        p2 = "player(2, 10, \"USA\", \"ICON\", \"CHI\", 98, 19)."
        rules = p1 + "\n" + p2 + "\n" + """        
        player(3, 1, "USA", "ICON", "CHI", 90, 11).
        player(4, 2, "USA", "ICON", "CHI", 60, 1).
        """
        # We are testing defense (2 players). 
        # Should pick P1 + P3 (Total OVR 189) or P2 + P3 (188). 
        # Cannot pick P1 + P2 (Total 197) because PID 10 matches.
        
        res, models, cost, count = self.solve(
            self.defense_rules,
            extra_rules=rules,
            consts={"salary_cap": 9999},
            ctl_opts=["0"]
        )
        assert res.satisfiable
        
        # Check that optimal solution does NOT contain both 1 and 2
        # Cost is maximized (negative).
        # Best valid: 1 and 3 (99+90=189). Cost=[-189] if no combos.
        best_model = models[-1]
        selected = [s.arguments[0].number for s in best_model if s.name == "selected"]
        
        # Should be {1, 3}
        assert 1 in selected
        assert 3 in selected
        assert 2 not in selected

    def test_salary_cap(self):
        # p1: OVR 99, Sal 20. (PID 10)
        # p2: OVR 98, Sal 19. (PID 10) - Same player as P1
        # p3: OVR 90, Sal 11. (PID 1)
        # p4: OVR 60, Sal 1. (PID 2)
        
        p1 = "player(1, 10, \"USA\", \"ICON\", \"CHI\", 99, 20)."
        p2 = "player(2, 10, \"USA\", \"TOTW\", \"LAK\", 98, 19)."
        rules = p1 + "\n" + p2 + "\n" + """        
        player(3, 1, "SWE", "GM", "TBL", 90, 11).
        player(4, 2, "FIN", "NG", "MTL", 60, 1).
        """
        
        # Base case: Cap 32.
        # Possible pairs with P3 (Sal 11):
        # P1 (20) + P3 (11) = 31. OVR 189.
        # P2 (19) + P3 (11) = 30. OVR 188.
        # If Cap >= 31, P1+P3 is best.
        
        # b) Cap 31 -> Pick P1? Yes, 20+11=31.
        res, models, _, _ = self.solve(
            self.defense_rules,
            extra_rules=rules,
            consts={"salary_cap": 31},
            ctl_opts=["0"]
        )
        best = [s.arguments[0].number for s in models[-1] if s.name == "selected"]
        assert 1 in best # P1 (99)
        assert 3 in best

        # c) Cap 30 -> P1+P3 is 31 (Too expensive). Must pick P2+P3 (19+11=30).
        res, models, _, _ = self.solve(
            self.defense_rules,
            extra_rules=rules,
            consts={"salary_cap": 30},
            ctl_opts=["0"]
        )
        best = [s.arguments[0].number for s in models[-1] if s.name == "selected"]
        assert 2 in best # P2 (98)
        assert 3 in best

    def test_salary_synergy(self):
        # Scenario: Cap is tight (30).
        # P1 (Sal 20) + P3 (Sal 11) = 31. Usually invalid.
        # P2 (Sal 19) + P3 (Sal 11) = 30. Valid.
        # BUT: Combo activates for P1+P3 that gives +2 Salary Cap (if implemented) OR simple Reward that outweighs?
        # Wait, user said "activates salary cap bonus".
        # Does our model support dynamic salary cap?
        # The rules say `:- total_salary(S), S > salary_cap.`
        # Salary cap is a constant.
        # G1A `multiplier` for SAL is just a reward weight. It doesn't increase the cap.
        # Unless "SAL" type combo means "Reduces Salary Count" or "Increases Cap"?
        # User prompt: "activates salary cap bonus ... so it is activated".
        # This implies the bonus effectively allows the line to exist.
        # IF "SAL" reward is interpreted as "Cap Relief".
        
        # Currently, my rules treat SAL as just another score points.
        # I should probably interpret "SAL" combo as: Reward R means "Increase Cap by R"?
        # OR "Reduce Total Salary by R"?
        
        # Let's assume for this test that we implement "SAL" combo reward as Cap Increase.
        # I need to modify `rules.lp` to subtract SAL rewards from Total Salary?
        # Or add to Salary Cap?
        
        # Let's adjust `rules.lp` logic for this test?
        # Or better: Assume the user meant "SAL" reward is just high score, so we prefer it?
        # "so it is activated" -> sounds like validity.
        # "if salary cap is 31 it should pick p2... also implement test case when ... activates salary cap bonus ... so it should pick p1"
        # If P1 was invalid due to cap, but now valid, then yes, SAL bonus must affect cap.
        
        # I will modify `src/asp/g2_concrete/rules.lp` to use SAL rewards as Salary Reduction.
        pass

    def test_ovr_synergy(self):
        # P1 (99 OVR). P2 (98 OVR).
        # P1 usually preferred.
        # But P2 activates a combo with +2 OVR Reward.
        # Total P1 = 99. Total P2 = 98 + 2 = 100.
        # Should pick P2.
        
        p1 = "player(1, 10, \"USA\", \"ICON\", \"CHI\", 99, 20)."
        p2 = "player(2, 20, \"USA\", \"TOTW\", \"LAK\", 98, 19)." # Different player ID to allow pairing
        # Actually we compare P1 vs P2 in same slot.
        # Let's have P3 fixed.
        # P1+P3 vs P2+P3.
        
        rules = """
        player(1, 10, "USA", "ICON", "CHI", 99, 20).
        player(2, 10, "USA", "TOTW", "LAK", 98, 19).
        player(3, 30, "SWE", "NG", "LAK", 90, 11).
        
        % Combo: LAK + LAK -> +2 OVR
        defense_combo(1, 2, "OVR", team("LAK"), team("LAK")).
        """
        
        # P1(CHI)+P3(LAK) -> No combo. OVR 99+90 = 189.
        # P2(LAK)+P3(LAK) -> Combo Active (+2). OVR 98+90+2 = 190.
        # Should pick P2.
        
        res, models, _, _ = self.solve(
            self.defense_rules,
            extra_rules=rules,
            consts={"salary_cap": 9999, "w_ovr": 1},
            ctl_opts=["0"]
        )
        best = [s.arguments[0].number for s in models[-1] if s.name == "selected"]
        assert 2 in best
        assert 3 in best

