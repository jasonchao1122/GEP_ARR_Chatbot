from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def time_series_totals_chart(totals_table: pd.DataFrame) -> go.Figure:
    """Line chart of Plan vs Actual totals over time."""
    df = totals_table.copy()
    melted = df.melt(id_vars=["date"], value_vars=[c for c in ["Plan", "Actual"] if c in df.columns], var_name="Series", value_name="Total")
    fig = px.line(
        melted,
        x="date",
        y="Total",
        color="Series",
        markers=True,
        title="Totals Over Time: Plan vs Actual",
    )
    fig.update_layout(legend_title_text="Series")
    return fig


def variance_bar_by_metric(var_by_metric: pd.DataFrame, period: pd.Timestamp) -> go.Figure:
    df = var_by_metric.copy()
    fig = px.bar(
        df,
        x="metric",
        y="Variance",
        color=df["Variance"].apply(lambda v: "Positive" if v >= 0 else "Negative"),
        color_discrete_map={"Positive": "#2ca02c", "Negative": "#d62728"},
        title=f"Variance by Metric — {pd.to_datetime(period).strftime('%b %Y')}",
    )
    fig.update_layout(showlegend=False, xaxis_title="Metric", yaxis_title="Variance")
    return fig


def variance_waterfall(var_by_metric: pd.DataFrame, period: pd.Timestamp, top_n: int = 10) -> go.Figure:
    """Waterfall chart from Plan total to Actual total using metric-level variances."""
    df = var_by_metric.copy()
    df = df.sort_values("Variance", ascending=False)
    head = df.head(max(0, top_n // 2))
    tail = df.tail(max(0, top_n - len(head)))
    display_df = pd.concat([head, tail]) if not head.empty or not tail.empty else df

    measure = ["relative"] * len(display_df)
    x = display_df["metric"].tolist()
    y = display_df["Variance"].tolist()

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measure,
        x=x,
        textposition="outside",
        y=y,
        decreasing={"marker": {"color": "#d62728"}},
        increasing={"marker": {"color": "#2ca02c"}},
        totals={"marker": {"color": "#1f77b4"}},
    ))

    fig.update_layout(
        title=f"Variance Waterfall — {pd.to_datetime(period).strftime('%b %Y')}",
        xaxis_title="Metric",
        yaxis_title="Variance",
        showlegend=False,
    )
    return fig

