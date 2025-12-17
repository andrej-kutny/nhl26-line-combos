import pandas as pd


def test_dataloader_uses_combo_id_and_ceil_salary(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    pd.DataFrame(
        [
            {
                "card_id": "c1",
                "position": "C",
                "nationality": "Canada",
                "event": "FANT",
                "league": "NHL",
                "team": "TOR",
                "salary": 0.5,
                "overall": 80,
                "POS": "FWD",
                "player_id": 1,
            }
        ]
    ).to_csv(data_dir / "fwd_filtered.csv", index=False)

    pd.DataFrame(
        [
            {
                "card_id": "d1",
                "position": "LD",
                "nationality": "Canada",
                "event": "FANT",
                "league": "NHL",
                "team": "TOR",
                "salary": 1.0,
                "overall": 80,
                "POS": "DEF",
                "player_id": 2,
            }
        ]
    ).to_csv(data_dir / "def_filtered.csv", index=False)

    pd.DataFrame(
        [
            {
                "card_id": "g1",
                "nationality": "Canada",
                "event": "FANT",
                "league": "NHL",
                "team": "TOR",
                "salary": 0.5,
                "overall": 80,
                "player_id": 3,
            }
        ]
    ).to_csv(data_dir / "g_filtered.csv", index=False)

    pd.DataFrame(
        [
            {"player_id": 1, "First name": "A", "Second name": "B"},
            {"player_id": 2, "First name": "C", "Second name": "D"},
        ]
    ).to_csv(data_dir / "skater_id.csv", index=False)

    pd.DataFrame([{"player_id": 3, "First name": "E", "Second name": "F"}]).to_csv(
        data_dir / "g_id.csv", index=False
    )

    pd.DataFrame(
        [
            {
                "combo_id": 123,
                "reward_amount": 7,
                "reward_type": "SAL",
                "type1": "event",
                "key1": "FANT",
                "type2": "event",
                "key2": "FANT",
                "type3": "event",
                "key3": "FANT",
            }
        ]
    ).to_csv(data_dir / "fwd_line_combos.csv", index=False)

    pd.DataFrame(
        [
            {
                "combo_id": 456,
                "reward_amount": 6,
                "reward_type": "SAL",
                "type1": "event",
                "key1": "FANT",
                "type2": "event",
                "key2": "FANT",
            }
        ]
    ).to_csv(data_dir / "def_line_combos.csv", index=False)

    from src.core.data_loader import DataLoader

    loader = DataLoader(str(data_dir), use_hutbuilder_api=False)
    forwards = loader.get_forwards()
    assert forwards[0].salary == 1

    fwd_combos = loader.get_forward_combos()
    assert fwd_combos[0].id == 123

    def_combos = loader.get_defense_combos()
    assert def_combos[0].id == 456

