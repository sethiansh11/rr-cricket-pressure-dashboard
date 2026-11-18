"""Dash dashboard for the existing cricket player-wise analytics.

Input file expected beside this script:
    agg_data_playerwise_dashboard.csv

Create it at the END of the existing notebook, after all merges:
    agg_data_playerwise.to_csv('agg_data_playerwise_dashboard.csv', index=False)

The dashboard only reads the already-computed player-wise table. It does not
recalculate pressure scores, player statistics, or rankings from ball-by-ball data.
"""

from pathlib import Path
import os
import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

DATA_PATH = Path(__file__).with_name("agg_data_playerwise_dashboard.csv")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Could not find {DATA_PATH.name}. In your existing notebook, run:\n\n"
        "agg_data_playerwise.to_csv('agg_data_playerwise_dashboard.csv', index=False)\n\n"
        "Save the CSV in the same folder as pressure_dashboard.py."
    )

# Reuse the final player-wise table produced by the user's existing notebook.
df = pd.read_csv(DATA_PATH)

if "player_id" not in df.columns:
    raise ValueError("The exported table must contain a 'player_id' column.")

if "player_name" not in df.columns:
    df["player_name"] = df["player_id"].astype(str)
else:
    df["player_name"] = df["player_name"].fillna(df["player_id"].astype(str)).astype(str)

# Definitions refer only to columns already created in the user's notebook.
# direction: 'high' means larger is better; 'low' means smaller is better.
ANALYSES = {
    "Overall batting": {
        "description": "Overall batting output using the player-wise statistics already calculated.",
        "metrics": {
            "batting_runs": {"label": "Total batting runs", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "batting_runs_mean": {"label": "Average runs per recorded batting delivery-group row", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "runs_per_ball": {"label": "Runs per recorded striker delivery", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "boundary_runs": {"label": "Boundary runs", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "total_boundaries": {"label": "Total fours and sixes", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "boundary_contribution": {"label": "Boundary contribution (%)", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "runs_on_foot": {"label": "Runs on foot", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "runs_on_foot_contribution": {"label": "Running contribution (%)", "direction": "high", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30},
            "batting_consistency": {"label": "Existing batting consistency CV (lower is better)", "direction": "low", "matches": "matches_batted", "min_matches": 5, "exposure": "batting_deliveries", "min_exposure": 30, "guard": ("batting_runs_mean", "high")},
        },
        "default": "batting_runs",
    },
    "Overall bowling": {
        "description": "Overall bowling output using the player-wise statistics already calculated. Economy and discipline metrics are ranked in their appropriate direction.",
        "metrics": {
            "Economy_rate": {"label": "Economy rate (lower is better)", "direction": "low", "matches": "matches_bowled", "min_matches": 5, "exposure": "legal_deliveries", "min_exposure": 120},
            "dot_ball_precentage": {"label": "Dot-ball percentage", "direction": "high", "matches": "matches_bowled", "min_matches": 5, "exposure": "legal_deliveries", "min_exposure": 120},
            "boundary_runs_conceeded": {"label": "Boundary runs conceded (lower is better)", "direction": "low", "matches": "matches_bowled", "min_matches": 5, "exposure": "legal_deliveries", "min_exposure": 120},
            "wide_frequency": {"label": "Wide frequency (lower is better)", "direction": "low", "matches": "matches_bowled", "min_matches": 5, "exposure": "legal_deliveries", "min_exposure": 120},
            "no_ball_frequency": {"label": "No-ball frequency (lower is better)", "direction": "low", "matches": "matches_bowled", "min_matches": 5, "exposure": "legal_deliveries", "min_exposure": 120},
            "bowling_consistency": {"label": "Existing bowling consistency CV (lower is better)", "direction": "low", "matches": "matches_bowled", "min_matches": 5, "exposure": "legal_deliveries", "min_exposure": 120, "guard": ("Economy_rate", "low")},
        },
        "default": "Economy_rate",
    },
    "Batting under pressure": {
        "description": "Performance on deliveries categorized High or Very High by your existing batting-pressure category. T20 and T20I are combined, as requested.",
        "metrics": {
            "batting_pressure_strike_rate": {"label": "Pressure strike rate", "direction": "high", "matches": "batting_pressure_matches", "min_matches": 5, "exposure": "batting_pressure_balls", "min_exposure": 30},
            "batting_pressure_runs": {"label": "Runs scored under pressure", "direction": "high", "matches": "batting_pressure_matches", "min_matches": 5, "exposure": "batting_pressure_balls", "min_exposure": 30},
            "batting_pressure_sr_cv": {"label": "Pressure strike-rate CV (lower is better)", "direction": "low", "matches": "batting_pressure_matches", "min_matches": 5, "exposure": "batting_pressure_balls", "min_exposure": 30, "guard": ("batting_pressure_strike_rate", "high")},
        },
        "default": "batting_pressure_strike_rate",
    },
    "Bowling under pressure": {
        "description": "Bowling performance on deliveries categorized High or Very High by your existing bowling-team pressure category. T20 and T20I are combined, as requested.",
        "metrics": {
            "bowling_pressure_economy": {"label": "Pressure economy (lower is better)", "direction": "low", "matches": "bowling_pressure_matches", "min_matches": 5, "exposure": "bowling_pressure_legal_balls", "min_exposure": 60},
            "bowling_pressure_dot_pct": {"label": "Pressure dot-ball percentage", "direction": "high", "matches": "bowling_pressure_matches", "min_matches": 5, "exposure": "bowling_pressure_legal_balls", "min_exposure": 60},
            "bowling_pressure_economy_cv": {"label": "Pressure economy CV (lower is better)", "direction": "low", "matches": "bowling_pressure_matches", "min_matches": 5, "exposure": "bowling_pressure_legal_balls", "min_exposure": 60, "guard": ("bowling_pressure_economy", "low")},
        },
        "default": "bowling_pressure_economy",
    },
}

# Keep only metrics that really exist in the exported player-wise table.
for analysis_name, config in ANALYSES.items():
    config["metrics"] = {
        col: spec for col, spec in config["metrics"].items()
        if col in df.columns
    }
    if config["default"] not in config["metrics"] and config["metrics"]:
        config["default"] = next(iter(config["metrics"]))


def card_style():
    return {
        "background": "white", "border": "1px solid #e5e7eb",
        "borderRadius": "12px", "padding": "14px 16px",
        "boxShadow": "0 2px 8px rgba(15, 23, 42, 0.04)",
    }


def build_table(records, metric_label):
    if not records:
        return html.Div("No eligible players for this selection.", style={"padding": "18px", "color": "#64748b"})

    headers = ["Rank", "Player", metric_label, "Matches", "Exposure"]
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    rows = []
    for row in records:
        value = row.get("selected_value")
        rows.append(html.Tr([
            html.Td(row.get("rank")),
            html.Td(row.get("player_name")),
            html.Td("—" if pd.isna(value) else f"{value:,.2f}"),
            html.Td(row.get("matches", "—")),
            html.Td(row.get("exposure", "—")),
        ]))
    return html.Table([header, html.Tbody(rows)], style={
        "width": "100%", "borderCollapse": "collapse", "fontSize": "14px"
    })


app = Dash(__name__)
app.title = "Cricket Pressure & Player Analytics"

analysis_options = [
    {"label": name, "value": name}
    for name, cfg in ANALYSES.items() if cfg["metrics"]
]
initial_analysis = analysis_options[0]["value"] if analysis_options else None
initial_metrics = ANALYSES[initial_analysis]["metrics"] if initial_analysis else {}
initial_metric = ANALYSES[initial_analysis]["default"] if initial_analysis else None

app.layout = html.Div([
    html.Div([
        html.H1("Cricket Player Performance Dashboard", style={"marginBottom": "4px", "color": "#0f172a"}),
        html.Div("Overall statistics, pressure performance and consistency rankings", style={"color": "#64748b", "fontSize": "15px"}),
    ], style={"marginBottom": "22px"}),

    html.Div([
        html.Div([
            html.Label("Analysis area", style={"fontWeight": "600"}),
            dcc.Dropdown(
                id="analysis-select", options=analysis_options,
                value=initial_analysis, clearable=False
            ),
        ], style={"flex": "2", "minWidth": "230px"}),
        html.Div([
            html.Label("Choose statistic", style={"fontWeight": "600"}),
            dcc.Dropdown(
                id="metric-select",
                options=[{"label": spec["label"], "value": col} for col, spec in initial_metrics.items()],
                value=initial_metric, clearable=False
            ),
        ], style={"flex": "3", "minWidth": "260px"}),
        html.Div([
            html.Label("Number of players", style={"fontWeight": "600"}),
            dcc.Dropdown(
                id="topn-select",
                options=[{"label": str(n), "value": n} for n in [5, 10, 15, 20]],
                value=10, clearable=False
            ),
        ], style={"flex": "1", "minWidth": "130px"}),
    ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap", **card_style(), "marginBottom": "18px"}),

    html.Div(id="analysis-description", style={"color": "#475569", "marginBottom": "14px"}),

    html.Div([
        html.Div(id="summary-card", style={**card_style(), "flex": "1"}),
        html.Div(id="ranking-rule-card", style={**card_style(), "flex": "2"}),
    ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginBottom": "18px"}),

    html.Div([
        dcc.Graph(id="leaderboard-graph", config={"displaylogo": False}),
    ], style={**card_style(), "marginBottom": "18px"}),

    html.Div([
        html.H3("Ranked players", style={"marginTop": "0"}),
        html.Div(id="leaderboard-table", style={"overflowX": "auto"}),
    ], style=card_style()),

    html.Div(
        "Consistency CV is lower-is-better. Exposure counts are shown alongside each ranking; rankings use the minimum appearance and delivery thresholds stated in the analysis definition.",
        style={"fontSize": "12px", "color": "#64748b", "marginTop": "14px"}
    ),
], style={
    "maxWidth": "1450px", "margin": "0 auto", "padding": "26px",
    "fontFamily": "Arial, sans-serif", "background": "#f8fafc", "minHeight": "100vh"
})


@app.callback(
    Output("metric-select", "options"),
    Output("metric-select", "value"),
    Output("analysis-description", "children"),
    Input("analysis-select", "value"),
)
def update_metric_options(analysis_name):
    config = ANALYSES.get(analysis_name, {})
    metrics = config.get("metrics", {})
    options = [{"label": spec["label"], "value": col} for col, spec in metrics.items()]
    default = config.get("default") if metrics else None
    return options, default, config.get("description", "")


@app.callback(
    Output("leaderboard-graph", "figure"),
    Output("leaderboard-table", "children"),
    Output("summary-card", "children"),
    Output("ranking-rule-card", "children"),
    Input("analysis-select", "value"),
    Input("metric-select", "value"),
    Input("topn-select", "value"),
)
def update_dashboard(analysis_name, metric, top_n):
    config = ANALYSES.get(analysis_name, {})
    spec = config.get("metrics", {}).get(metric)

    if not spec:
        empty_fig = px.bar(title="Selected statistic is not available in this table")
        return empty_fig, html.Div("No metric available."), "No data", "Check the exported player-wise table."

    work = df.copy()
    required_cols = [metric]
    for key in ["matches", "exposure"]:
        if spec.get(key):
            required_cols.append(spec[key])

    for col in required_cols:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    work = work.dropna(subset=[metric]).copy()

    # Apply role-specific exposure thresholds.
    if spec.get("matches") in work.columns:
        work = work[work[spec["matches"]] >= spec["min_matches"]]
    if spec.get("exposure") in work.columns:
        work = work[work[spec["exposure"]] >= spec["min_exposure"]]

    # For consistency rankings, exclude players whose performance level is
    # below the median among eligible players. This avoids rewarding poor but
    # repeatable performance as "best under pressure".
    guard_text = ""
    if spec.get("guard"):
        guard_col, guard_direction = spec["guard"]
        if guard_col in work.columns:
            work[guard_col] = pd.to_numeric(work[guard_col], errors="coerce")
            guard_median = work[guard_col].median()
            if pd.notna(guard_median):
                if guard_direction == "high":
                    work = work[work[guard_col] >= guard_median]
                    guard_text = f" Consistency candidates also meet or exceed the eligible-player median for {guard_col}."
                else:
                    work = work[work[guard_col] <= guard_median]
                    guard_text = f" Consistency candidates also meet or beat the eligible-player median for {guard_col}."

    ascending = spec["direction"] == "low"
    tie_cols = [metric]
    tie_ascending = [ascending]

    # Sensible secondary ordering for common performance metrics.
    tie_break = {
        "batting_pressure_strike_rate": ("batting_pressure_sr_cv", True),
        "batting_runs": ("batting_runs_mean", False),
        "Economy_rate": ("dot_ball_precentage", False),
        "bowling_pressure_economy": ("bowling_pressure_dot_pct", False),
    }.get(metric)
    if tie_break and tie_break[0] in work.columns:
        tie_cols.append(tie_break[0])
        tie_ascending.append(tie_break[1])

    work = work.sort_values(tie_cols, ascending=tie_ascending, na_position="last").head(int(top_n or 10)).copy()
    work["rank"] = np.arange(1, len(work) + 1)

    label = spec["label"]
    x_label = "Lower is better" if ascending else "Higher is better"

    if work.empty:
        fig = px.bar(title=f"No eligible players for {label}")
        fig.update_layout(template="plotly_white", height=480)
        return fig, html.Div("No players meet the exposure requirements for this selection."), "0 eligible players", "Try a different statistic or top-N selection."

    fig = px.bar(
        work.sort_values(metric, ascending=True),
        x=metric, y="player_name", orientation="h",
        text=metric, hover_data=[c for c in ["player_id", spec.get("matches"), spec.get("exposure")] if c and c in work.columns],
        title=f"{analysis_name}: {label}"
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        template="plotly_white", height=max(440, 38 * len(work) + 150),
        xaxis_title=label, yaxis_title="Player", showlegend=False,
        margin={"l": 150, "r": 45, "t": 65, "b": 55}
    )
    fig.update_xaxes(title=f"{label} — {x_label}")

    match_col = spec.get("matches")
    exposure_col = spec.get("exposure")
    records = []
    for _, row in work.iterrows():
        val = row[metric]
        records.append({
            "rank": int(row["rank"]),
            "player_name": row["player_name"],
            "selected_value": float(val) if pd.notna(val) else np.nan,
            "matches": int(row[match_col]) if match_col and pd.notna(row.get(match_col)) else "—",
            "exposure": int(row[exposure_col]) if exposure_col and pd.notna(row.get(exposure_col)) else "—",
        })

    table = build_table(records, label)
    summary = html.Div([
        html.Div("Players shown", style={"color": "#64748b", "fontSize": "12px"}),
        html.Div(str(len(work)), style={"fontSize": "27px", "fontWeight": "700", "color": "#0f172a"}),
        html.Div(f"of {len(df):,} players in the master table", style={"color": "#64748b", "fontSize": "12px"}),
    ])
    match_rule = f"Minimum {spec['min_matches']} qualifying matches" if match_col else "No match filter"
    exposure_rule = f"Minimum {spec['min_exposure']} {exposure_col}" if exposure_col else "No exposure filter"
    direction_rule = "Lower values rank first" if ascending else "Higher values rank first"
    rule = html.Div([
        html.Div("Ranking and eligibility", style={"fontWeight": "700", "marginBottom": "5px"}),
        html.Div(f"Statistic: {label}"),
        html.Div(f"{match_rule}; {exposure_rule}; {direction_rule}."),
        html.Div(guard_text, style={"color": "#475569", "marginTop": "4px"}),
    ])
    return fig, table, summary, rule


# WSGI entry point for production hosting (Render/Gunicorn).
server = app.server

if __name__ == "__main__":
    # Local development; Render uses the Gunicorn command in render.yaml.
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8050"))
    )
