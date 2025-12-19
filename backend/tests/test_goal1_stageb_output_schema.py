import pytest


def test_stageb_output_schema_version_and_required_keys():
    stageb = pytest.importorskip("scripts.goal1_stageb_enumerate")

    payload = stageb.build_stageb_payload(
        pos="fwd",
        combo_ids=[1, 2],
        constraints={"min_ovr": 80, "max_salary": 110, "max_ap": None, "require_center": False},
        solutions=[],
    )

    assert payload["schema_version"] == stageb.STAGEB_OUTPUT_SCHEMA_VERSION
    assert payload["pos"] == "fwd"
    assert payload["combo_ids"] == [1, 2]
    assert isinstance(payload["constraints"], dict)
    assert payload["count"] == 0
    assert payload["solutions"] == []

