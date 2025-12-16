"""
Export combo CSVs into small .lp fact files for standalone Clingo experiments.

Why this exists
---------------
For Goal 1, it's useful to run Clingo on "just the combo logic" without having to
boot the full backend/API. This script converts the project CSVs into 6 compact
fact files:

  out/fwd_ovr_combinations.lp
  out/fwd_sal_combinations.lp
  out/fwd_ap_combinations.lp
  out/def_ovr_combinations.lp
  out/def_sal_combinations.lp
  out/def_ap_combinations.lp

Fact format (matches our ASP rules)
----------------------------------
Forward combos:
  fwd_combo(ComboID, RewardAmount, RewardType, Type1, Key1, Type2, Key2, Type3, Key3).

Defense combos:
  def_combo(ComboID, RewardAmount, RewardType, Type1, Key1, Type2, Key2).

Where RewardType is one of: ovr | sal | ap
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _reward_atom(s: str) -> str:
    v = str(s).strip().upper()
    if v == "OVR":
        return "ovr"
    if v == "SAL":
        return "sal"
    if v == "AP":
        return "ap"
    raise ValueError(f"Unknown reward_type: {s!r}")


def _sanitize_atom(s: str) -> str:
    return str(s).strip().lower()


def _sanitize_key(s: str) -> str:
    return str(s).strip().upper()


def export(data_dir: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    fwd_df = pd.read_csv(data_dir / "fwd_line_combos.csv")
    def_df = pd.read_csv(data_dir / "def_line_combos.csv")

    outputs: list[Path] = []

    # Forward: 3-condition combos
    for reward in ("OVR", "SAL", "AP"):
        atom = _reward_atom(reward)
        path = out_dir / f"fwd_{atom}_combinations.lp"
        rows = fwd_df[fwd_df["reward_type"].astype(str).str.upper() == reward]
        lines = []
        for _, row in rows.iterrows():
            combo_id = int(row["combo_id"]) if "combo_id" in row else int(row.name)
            reward_amount = int(row["reward_amount"])
            t1, k1 = _sanitize_atom(row["type1"]), _sanitize_key(row["key1"])
            t2, k2 = _sanitize_atom(row["type2"]), _sanitize_key(row["key2"])
            t3, k3 = _sanitize_atom(row["type3"]), _sanitize_key(row["key3"])
            lines.append(
                f'fwd_combo({combo_id}, {reward_amount}, {atom}, "{t1}", "{k1}", "{t2}", "{k2}", "{t3}", "{k3}").'
            )
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        outputs.append(path)

    # Defense: 2-condition combos
    for reward in ("OVR", "SAL", "AP"):
        atom = _reward_atom(reward)
        path = out_dir / f"def_{atom}_combinations.lp"
        rows = def_df[def_df["reward_type"].astype(str).str.upper() == reward]
        lines = []
        for _, row in rows.iterrows():
            combo_id = int(row["combo_id"]) if "combo_id" in row else int(row.name)
            reward_amount = int(row["reward_amount"])
            t1, k1 = _sanitize_atom(row["type1"]), _sanitize_key(row["key1"])
            t2, k2 = _sanitize_atom(row["type2"]), _sanitize_key(row["key2"])
            lines.append(
                f'def_combo({combo_id}, {reward_amount}, {atom}, "{t1}", "{k1}", "{t2}", "{k2}").'
            )
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        outputs.append(path)

    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Export combo CSVs to .lp fact files.")
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--out-dir", type=str, default="out")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    data_dir = (repo_root / args.data_dir).resolve()
    out_dir = (repo_root / args.out_dir).resolve()

    written = export(data_dir=data_dir, out_dir=out_dir)
    for p in written:
        print(f"Wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

