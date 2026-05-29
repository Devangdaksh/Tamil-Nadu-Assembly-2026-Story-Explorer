"""
Streamlit dashboard — TN 2026 Assembly election (RPC #26).
Run: streamlit run dashboard/app.py
"""

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.load_data import (  # noqa: E402
    constituency_margins,
    constituency_winners,
    load_master,
    load_results,
    year_comparison,
)

st.set_page_config(
    page_title="TN Election 2026 | AtliQ Story Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Tamil Nadu Assembly 2026 — Story Explorer")
st.caption(
    "Neutral, ECI-based view for AtliQ Media planning. "
    "Compare 2021 vs 2026; filter by region and reservation."
)

r21 = load_results(2021)
r26 = load_results(2026)
master = load_master()
w21 = constituency_winners(r21)
w26 = constituency_winners(r26)
margins = constituency_margins(r26)
comparison = year_comparison()

with st.sidebar:
    st.header("Filters")
    regions = sorted(w26["region"].dropna().unique())
    region_sel = st.multiselect("Region", regions, default=regions)
    reserved_sel = st.multiselect("Reservation", ["GEN", "SC", "ST"], default=["GEN", "SC", "ST"])
    parties = sorted(w26["party"].unique())
    party_sel = st.multiselect("2026 winning party", parties, default=["TVK", "DMK", "AIADMK"])

filtered = w26[
    w26["region"].isin(region_sel)
    & w26["reserved"].isin(reserved_sel)
    & w26["party"].isin(party_sel)
]

tab1, tab2, tab3, tab4 = st.tabs(
    ["Seat map (table)", "Margins", "2021 → 2026", "Constituency lookup"]
)

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Seats in view", len(filtered), help="After sidebar filters")
    c2.metric("TVK seats (filtered)", int((filtered.party == "TVK").sum()))
    c3.metric("Changed vs 2021", int(comparison[comparison.ac_number.isin(filtered.ac_number) & comparison.changed].shape[0]))

    seat_counts = filtered["party"].value_counts().reset_index()
    seat_counts.columns = ["party", "seats"]
    fig = px.bar(
        seat_counts,
        x="party",
        y="seats",
        title="Winning party — seat count (filtered)",
        color_discrete_sequence=["#3B82F6"],
    )
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Seats")
    st.plotly_chart(fig, use_container_width=True)

    region_party = (
        filtered.groupby(["region", "party"], as_index=False)
        .size()
        .rename(columns={"size": "seats"})
    )
    if not region_party.empty:
        pivot = region_party.pivot(index="region", columns="party", values="seats").fillna(0)
        fig2 = px.imshow(
            pivot,
            labels=dict(x="Party", y="Region", color="Seats"),
            title="Seats by region × party",
            color_continuous_scale="Blues",
            aspect="auto",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(
        filtered[
            ["ac_number", "constituency", "party", "votes", "region", "reserved"]
        ].sort_values("ac_number"),
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    m_filt = margins[margins.ac_number.isin(filtered.ac_number)]
    st.metric("Races under 1% margin (filtered)", int((m_filt.margin_pct < 1).sum()))
    st.metric("Races under 5% margin (filtered)", int((m_filt.margin_pct < 5).sum()))

    fig3 = px.histogram(
        m_filt,
        x="margin_pct",
        nbins=25,
        title="Distribution of winning margins (%)",
        labels={"margin_pct": "Margin %"},
        color_discrete_sequence=["#6366F1"],
    )
    st.plotly_chart(fig3, use_container_width=True)

    closest = m_filt.nsmallest(15, "margin_pct")[
        [
            "constituency",
            "party",
            "runner_up_party",
            "margin_votes",
            "margin_pct",
            "region",
        ]
    ]
    st.subheader("Closest races")
    st.dataframe(closest, use_container_width=True, hide_index=True)

with tab3:
    cmp_f = comparison[comparison.ac_number.isin(filtered.ac_number)]
    flip_matrix = (
        cmp_f[cmp_f.changed]
        .groupby(["party_2021", "party_2026"])
        .size()
        .reset_index(name="constituencies")
        .sort_values("constituencies", ascending=False)
    )
    st.subheader("Largest party switches (2021 winner → 2026 winner)")
    st.dataframe(flip_matrix.head(20), use_container_width=True, hide_index=True)

    st.subheader("Constituencies that flipped")
    st.dataframe(
        cmp_f[cmp_f.changed][
            ["ac_number", "constituency", "region", "party_2021", "party_2026"]
        ].sort_values("region"),
        use_container_width=True,
        hide_index=True,
    )

with tab4:
    ac = st.number_input("AC number (1–234)", min_value=1, max_value=234, value=1)
    detail = r26[r26.ac_number == ac].sort_values("votes", ascending=False)
    meta = master[master.ac_number == ac].iloc[0]
    st.write(f"**{meta.constituency}** — {meta.district} · {meta.region} · {meta.reserved}")
    st.dataframe(
        detail[["candidate", "party", "votes"]],
        use_container_width=True,
        hide_index=True,
    )
    if detail["turnout"].notna().any() and detail["turnout"].iloc[0] == detail["turnout"].iloc[0]:
        st.info(f"Turnout (2026 row): {detail['turnout'].iloc[0]}%")
    else:
        st.warning("Turnout % not present in 2026 file for this release.")

st.divider()
st.markdown(
    "**Limitations:** 2026 turnout is blank in supplied data; use 2021 turnout only where noted. "
    "Do not infer causation (alliance effects, leadership, etc.) from vote totals alone."
)
