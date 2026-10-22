import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="NBA Injury Adjusted Wins",
    page_icon="🏀",
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "running_injury_adjusted_wins.csv"
REQUIRED_COLUMNS = [
    "GAME_DATE", "GAME_ID", "TEAM_ABBREVIATION", "ACTUAL_WIN",
    "OWN_INJURED_DPM_PCT", "OPP_INJURED_DPM_PCT", "ADJUSTED_WIN",
]

TEAM_NAMES = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
}

@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    data = pd.read_csv(file_path)
    missing = [col for col in REQUIRED_COLUMNS if col not in data.columns]
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing))
    data["GAME_DATE"] = pd.to_datetime(data["GAME_DATE"], errors="coerce")
    for col in ["ACTUAL_WIN", "OWN_INJURED_DPM_PCT", "OPP_INJURED_DPM_PCT", "ADJUSTED_WIN"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data["TEAM_ABBREVIATION"] = data["TEAM_ABBREVIATION"].astype(str).str.upper().str.strip()
    data = data.dropna(subset=["GAME_DATE", "TEAM_ABBREVIATION", "ADJUSTED_WIN"])
    data["TEAM"] = data["TEAM_ABBREVIATION"].map(TEAM_NAMES).fillna(data["TEAM_ABBREVIATION"])
    return data

st.title("🏀 NBA Injury Adjusted Wins")
st.caption("A team-by-team view of wins adjusted for player injuries.")

try:
    df = load_data(str(DATA_FILE))
except FileNotFoundError:
    st.error(f"Could not find `{DATA_FILE.name}`. Add the latest CSV beside `app.py`.")
    st.stop()
except Exception as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("The CSV has no usable rows.")
    st.stop()

min_date = df["GAME_DATE"].min().date()
max_date = df["GAME_DATE"].max().date()

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input(
        "Game date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    teams = sorted(df["TEAM"].unique().tolist())
    selected_teams = st.multiselect("Teams", teams, default=teams)
    st.caption("The dashboard uses the rows in the CSV. Replace the file with your latest export to update the data.")

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

filtered = df[
    df["GAME_DATE"].dt.date.between(start_date, end_date)
    & df["TEAM"].isin(selected_teams)
].copy()

if filtered.empty:
    st.info("No records match the selected filters.")
    st.stop()

# Each row is one team in one game. Season totals are sums over the selected date range.
leaderboard = (
    filtered.groupby(["TEAM", "TEAM_ABBREVIATION"], as_index=False)
    .agg(
        Injury_Adjusted_Wins=("ADJUSTED_WIN", "sum"),
        Actual_Wins=("ACTUAL_WIN", "sum"),
        Games=("GAME_ID", "nunique"),
        Own_Injury_DPM_Pct_Avg=("OWN_INJURED_DPM_PCT", "mean"),
        Opp_Injury_DPM_Pct_Avg=("OPP_INJURED_DPM_PCT", "mean"),
    )
)
leaderboard["Adjustment_vs_Actual"] = leaderboard["Injury_Adjusted_Wins"] - leaderboard["Actual_Wins"]
leaderboard = leaderboard.sort_values("Injury_Adjusted_Wins", ascending=False).reset_index(drop=True)
leaderboard.insert(0, "Rank", range(1, len(leaderboard) + 1))

total_adjusted = filtered["ADJUSTED_WIN"].sum()
total_actual = filtered["ACTUAL_WIN"].sum()
game_count = filtered["GAME_ID"].nunique()
latest_date = filtered["GAME_DATE"].max().strftime("%b %d, %Y")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Teams in view", f"{leaderboard['TEAM'].nunique()}")
c2.metric("Games in view", f"{game_count}")
c3.metric("Actual wins (team records)", f"{total_actual:.0f}")
c4.metric("Injury-adjusted wins", f"{total_adjusted:.2f}")
st.caption(f"Latest game date in filtered data: {latest_date}")

st.subheader("Team leaderboard")
display = leaderboard.rename(columns={
    "TEAM": "Team",
    "TEAM_ABBREVIATION": "Abbr.",
    "Injury_Adjusted_Wins": "Injury Adjusted Wins",
    "Actual_Wins": "Actual Wins",
    "Adjustment_vs_Actual": "Adjusted − Actual",
    "Own_Injury_DPM_Pct_Avg": "Avg. Own Injury DPM %",
    "Opp_Injury_DPM_Pct_Avg": "Avg. Opponent Injury DPM %",
})
st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Injury Adjusted Wins": st.column_config.NumberColumn(format="%.3f"),
        "Adjusted − Actual": st.column_config.NumberColumn(format="%+.3f"),
        "Avg. Own Injury DPM %": st.column_config.NumberColumn(format="%.2f%%"),
        "Avg. Opponent Injury DPM %": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

left, right = st.columns(2)
with left:
    st.subheader("Injury-adjusted wins by team")
    chart_data = leaderboard.sort_values("Injury_Adjusted_Wins", ascending=True)
    fig = px.bar(
        chart_data, x="Injury_Adjusted_Wins", y="TEAM", orientation="h",
        labels={"Injury_Adjusted_Wins": "Injury Adjusted Wins", "TEAM": ""},
        hover_data=["Actual_Wins", "Games"],
    )
    fig.update_layout(margin=dict(l=0, r=10, t=15, b=0), yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Adjusted wins vs. actual wins")
    fig2 = px.scatter(
        leaderboard, x="Actual_Wins", y="Injury_Adjusted_Wins",
        text="TEAM_ABBREVIATION", hover_name="TEAM",
        labels={"Actual_Wins": "Actual Wins", "Injury_Adjusted_Wins": "Injury Adjusted Wins"},
    )
    fig2.update_traces(textposition="top center")
    fig2.update_layout(margin=dict(l=0, r=10, t=15, b=0))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Game-level data")
game_view = filtered.sort_values(["GAME_DATE", "GAME_ID", "TEAM_ABBREVIATION"], ascending=[False, True, True]).copy()
game_view["GAME_DATE"] = game_view["GAME_DATE"].dt.strftime("%Y-%m-%d")
game_view = game_view.rename(columns={
    "GAME_DATE": "Date",
    "GAME_ID": "Game ID",
    "TEAM_ABBREVIATION": "Team",
    "ACTUAL_WIN": "Actual Win",
    "OWN_INJURED_DPM_PCT": "Own Injured DPM %",
    "OPP_INJURED_DPM_PCT": "Opponent Injured DPM %",
    "ADJUSTED_WIN": "Adjusted Win",
})
st.dataframe(
    game_view[["Date", "Game ID", "Team", "Actual Win", "Own Injured DPM %", "Opponent Injured DPM %", "Adjusted Win"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Own Injured DPM %": st.column_config.NumberColumn(format="%.4f"),
        "Opponent Injured DPM %": st.column_config.NumberColumn(format="%.4f"),
        "Adjusted Win": st.column_config.NumberColumn(format="%.4f"),
    },
)

csv_bytes = leaderboard.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download leaderboard CSV",
    data=csv_bytes,
    file_name="injury_adjusted_wins_leaderboard.csv",
    mime="text/csv",
)

with st.expander("About this dashboard"):
    st.write(
        "The leaderboard sums `ADJUSTED_WIN` across the selected date range for each team. "
        "It also shows actual wins and the difference between adjusted and actual wins. "
        "Confirm that this aggregation matches your intended definition of season-long Injury Adjusted Wins."
    )
    st.write(
        "This starter dashboard only displays records present in the CSV. To make daily updates automatic, "
        "the deployed app must receive the new CSV from your existing script or from a scheduled workflow."
    )
