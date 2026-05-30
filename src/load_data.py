"""Load and aggregate Tamil Nadu assembly election CSVs."""

from pathlib import Path

import plotly.express as px
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

MAJOR_PARTIES = [
    "DMK",
    "AIADMK",
    "TVK",
    "INC",
    "BJP",
    "PMK",
    "VCK",
    "NTK",
    "CPI",
    "CPI(M)",
    "NOTA",
]


def load_results(year: int) -> pd.DataFrame:
    path = DATA_DIR / f"tn_{year}_results.csv"
    df = pd.read_csv(path)
    df["ac_number"] = df["ac_number"].astype(int)
    return df


def load_master() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "constituency_master.csv")


def constituency_winners(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values(["ac_number", "votes"], ascending=[True, False])
        .groupby("ac_number", as_index=False)
        .first()
    )


def constituency_margins(df: pd.DataFrame) -> pd.DataFrame:
    ranked = df.sort_values(["ac_number", "votes"], ascending=[True, False])
    top = ranked.groupby("ac_number", as_index=False).nth(0)
    second = ranked.groupby("ac_number", as_index=False).nth(1)
    totals = df.groupby("ac_number")["votes"].sum()

    out = top.copy()
    out["runner_up_party"] = second["party"].values
    out["runner_up_votes"] = second["votes"].values
    out["margin_votes"] = out["votes"] - out["runner_up_votes"]
    out["total_votes"] = out["ac_number"].map(totals)
    out["margin_pct"] = out["margin_votes"] / out["total_votes"] * 100
    return out


def party_vote_share(df: pd.DataFrame, party: str) -> pd.Series:
    totals = df.groupby("ac_number")["votes"].sum()
    party_votes = df[df["party"] == party].groupby("ac_number")["votes"].sum()
    return (party_votes / totals * 100).reindex(totals.index)


def year_comparison() -> pd.DataFrame:
    w21 = constituency_winners(load_results(2021))
    w26 = constituency_winners(load_results(2026))
    merged = w21[["ac_number", "constituency", "party", "region"]].merge(
        w26[["ac_number", "party"]],
        on="ac_number",
        suffixes=("_2021", "_2026"),
    )
    merged["changed"] = merged["party_2021"] != merged["party_2026"]
    return merged
