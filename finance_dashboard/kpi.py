from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class VarianceSummary:
    period: pd.Timestamp
    total_plan: float
    total_actual: float
    total_variance: float
    total_variance_pct: float
    top_positive_contributors: List[Tuple[str, float]]
    top_negative_contributors: List[Tuple[str, float]]


def compute_totals_by_period(tidy: pd.DataFrame, entity: Optional[str] = None) -> pd.DataFrame:
    """Return totals per period and series. Expects tidy columns: date, metric, value, series, [entity]."""
    df = tidy.copy()
    if entity and "entity" in df.columns:
        df = df[df["entity"] == entity]
    totals = (
        df.groupby(["date", "series"], as_index=False)["value"].sum().rename(columns={"value": "total"})
    )
    return totals


def compute_variance_by_metric_for_period(tidy: pd.DataFrame, period: pd.Timestamp, entity: Optional[str] = None) -> pd.DataFrame:
    df = tidy.copy()
    if entity and "entity" in df.columns:
        df = df[df["entity"] == entity]
    df = df[df["date"] == period]
    pivot = df.pivot_table(index=["metric"], columns="series", values="value", aggfunc="sum", fill_value=0.0)
    for col in ["Actual", "Plan"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
    pivot["Variance"] = pivot.get("Actual", 0.0) - pivot.get("Plan", 0.0)
    pivot = pivot.reset_index().sort_values("Variance", ascending=False)
    return pivot


def latest_period(df: pd.DataFrame) -> Optional[pd.Timestamp]:
    if df.empty:
        return None
    return pd.to_datetime(df["date"]).max()


def build_variance_summary(tidy: pd.DataFrame, period: Optional[pd.Timestamp] = None, entity: Optional[str] = None, top_n: int = 5) -> Optional[VarianceSummary]:
    if tidy is None or tidy.empty:
        return None

    if period is None:
        period = latest_period(tidy)
    if period is None:
        return None

    totals = compute_totals_by_period(tidy, entity)
    totals_p = totals[totals["series"] == "Plan"].set_index("date")["total"]
    totals_a = totals[totals["series"] == "Actual"].set_index("date")["total"]

    total_plan = float(totals_p.get(period, 0.0)) if period in totals_p.index else float(totals_p.get(period, 0.0))
    total_actual = float(totals_a.get(period, 0.0)) if period in totals_a.index else float(totals_a.get(period, 0.0))
    total_variance = total_actual - total_plan
    total_variance_pct = (total_variance / total_plan * 100.0) if total_plan != 0 else np.nan

    var_by_metric = compute_variance_by_metric_for_period(tidy, period, entity)
    top_pos = var_by_metric.sort_values("Variance", ascending=False).head(top_n)
    top_neg = var_by_metric.sort_values("Variance", ascending=True).head(top_n)

    return VarianceSummary(
        period=pd.to_datetime(period),
        total_plan=total_plan,
        total_actual=total_actual,
        total_variance=total_variance,
        total_variance_pct=float(total_variance_pct) if not np.isnan(total_variance_pct) else float("nan"),
        top_positive_contributors=list(zip(top_pos["metric"].tolist(), top_pos["Variance"].tolist())),
        top_negative_contributors=list(zip(top_neg["metric"].tolist(), top_neg["Variance"].tolist())),
    )


def describe_totals_table(tidy: pd.DataFrame, entity: Optional[str] = None) -> pd.DataFrame:
    """Return a table with columns: date, Plan, Actual, Variance, Variance %"""
    totals = compute_totals_by_period(tidy, entity)
    pivot = totals.pivot_table(index="date", columns="series", values="total", fill_value=0.0)
    for col in ["Actual", "Plan"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
    pivot["Variance"] = pivot["Actual"] - pivot["Plan"]
    pivot["Variance %"] = np.where(pivot["Plan"] != 0, (pivot["Variance"] / pivot["Plan"]) * 100.0, np.nan)
    pivot = pivot.reset_index().sort_values("date")
    return pivot

