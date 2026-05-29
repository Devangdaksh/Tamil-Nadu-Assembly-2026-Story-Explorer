"""
Reproducible analysis for RPC #26 — Tamil Nadu 2026 Assembly election.
Run from project root: python analysis/generate_outputs.py
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.load_data import (  # noqa: E402
    constituency_margins,
    constituency_winners,
    load_results,
    party_vote_share,
    year_comparison,
)

OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

# Neutral palette — not party-branded colors
COLORS = {
    "TVK": "#4B5563",
    "DMK": "#6B7280",
    "AIADMK": "#9CA3AF",
    "INC": "#D1D5DB",
    "other": "#E5E7EB",
}


def save_seat_chart(winners: pd.DataFrame, title: str, filename: str) -> None:
    counts = winners["party"].value_counts()
    top = counts.head(8)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(top.index[::-1], top.values[::-1], color="#3B82F6", alpha=0.85)
    ax.set_xlabel("Assembly seats (234 total)")
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left")
    for bar in bars:
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{int(bar.get_width())}", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_region_heatmap(winners: pd.DataFrame, filename: str) -> None:
    focus = ["TVK", "DMK", "AIADMK"]
    ct = pd.crosstab(winners["region"], winners["party"])[focus]
    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(ct.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(focus)), focus)
    ax.set_yticks(range(len(ct.index)), ct.index)
    for i in range(len(ct.index)):
        for j in range(len(focus)):
            ax.text(j, i, int(ct.iloc[i, j]), ha="center", va="center", fontsize=10)
    ax.set_title("2026 seats by editorial region (top three parties)", loc="left", fontweight="bold")
    fig.colorbar(im, ax=ax, label="Seats")
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_margin_histogram(margins: pd.DataFrame, filename: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(margins["margin_pct"], bins=30, color="#6366F1", edgecolor="white", alpha=0.9)
    ax.axvline(1, color="#DC2626", linestyle="--", linewidth=1, label="1% margin")
    ax.axvline(5, color="#F59E0B", linestyle="--", linewidth=1, label="5% margin")
    ax.set_xlabel("Winning margin (% of valid votes in constituency)")
    ax.set_ylabel("Number of constituencies")
    ax.set_title("2026: How close were the races?", loc="left", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_story_metrics() -> None:
    r21, r26 = load_results(2021), load_results(2026)
    w21, w26 = constituency_winners(r21), constituency_winners(r26)
    margins = constituency_margins(r26)
    cmp = year_comparison()

    closest = margins.nsmallest(1, "margin_votes").iloc[0]
    flips = cmp[cmp["changed"]]
    dmk_to_tvk = flips[(flips.party_2021 == "DMK") & (flips.party_2026 == "TVK")]

    chennai = w26[w26.region == "Chennai Metro"]["party"].value_counts()
    tvk_metro = int(chennai.get("TVK", 0))
    metro_total = len(w26[w26.region == "Chennai Metro"])

    lines = [
        "# Story metrics (generated — verify in notebook before filming)",
        "",
        "## Headline-ready numbers",
        f"- **TVK** won **{(w26.party == 'TVK').sum()}** of 234 seats in 2026 (no seats in 2021 dataset).",
        f"- **DMK** seats: **{(w21.party == 'DMK').sum()}** (2021) → **{(w26.party == 'DMK').sum()}** (2026).",
        f"- **AIADMK** seats: **{(w21.party == 'AIADMK').sum()}** (2021) → **{(w26.party == 'AIADMK').sum()}** (2026).",
        f"- **{len(flips)}** constituencies changed winning party vs 2021.",
        f"- **{len(dmk_to_tvk)}** former DMK seats were won by TVK in 2026 (largest single flip path).",
        f"- **{(margins.margin_pct < 1).sum()}** races decided by under **1%** margin; **{(margins.margin_pct < 5).sum()}** under **5%**.",
        f"- Narrowest result: **{closest.constituency}** — **{int(closest.margin_votes)}** vote margin ({closest.party} over {closest.runner_up_party}).",
        f"- **Chennai Metro**: TVK won **{tvk_metro}/{metro_total}** seats.",
        f"- TVK was 1st or 2nd in **{(w26.party == 'TVK').sum() + (margins.runner_up_party == 'TVK').sum()}** constituencies.",
        "",
        "## Data limitations (state on air)",
        "- 2026 file has **no turnout %** in this release; 2021 turnout is available for comparison only.",
        "- 2026 data is from ECI live portal; Form-20 audited totals may differ slightly.",
        "- Candidate/party names are as recorded by ECI; small spelling variants exist across years (e.g. Gummidipundi vs Gummidipoondi).",
        "",
        "## Suggested 3-story show arc",
        "1. **Urban reset** — Chennai Metro seat map + what changed from 2021 winners.",
        "2. **The super-tight state** — margin distribution + Tiruppattur one-vote segment.",
        "3. **Who lost what** — DMK→TVK flip count and regional table (Metro vs Kongu vs Delta).",
    ]
    (OUT / "story_metrics.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    r21, r26 = load_results(2021), load_results(2026)
    w21, w26 = constituency_winners(r21), constituency_winners(r26)
    margins = constituency_margins(r26)

    save_seat_chart(w21, "2021 Tamil Nadu Assembly — seats by winning party", "seats_2021.png")
    save_seat_chart(w26, "2026 Tamil Nadu Assembly — seats by winning party", "seats_2026.png")
    save_region_heatmap(w26, "seats_by_region_2026.png")
    save_margin_histogram(margins, "margin_distribution_2026.png")

    # Vote share comparison for major parties
    rows = []
    for party in ["DMK", "AIADMK", "TVK", "NTK", "NOTA"]:
        s21 = party_vote_share(r21, party)
        s26 = party_vote_share(r26, party)
        rows.append({
            "party": party,
            "mean_share_2021": round(s21.mean(), 2),
            "mean_share_2026": round(s26.mean(), 2),
        })
    pd.DataFrame(rows).to_csv(OUT / "vote_share_comparison.csv", index=False)

    write_story_metrics()
    print(f"Wrote charts and metrics to {OUT}")


if __name__ == "__main__":
    main()
