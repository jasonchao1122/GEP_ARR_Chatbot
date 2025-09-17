from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

import pandas as pd


# Column synonyms to help standardize user-provided CSVs
DATE_COL_SYNONYMS = ["date", "month", "period", "period_start", "period_end"]
METRIC_COL_SYNONYMS = ["metric", "account", "line_item", "category", "kpi", "name"]
VALUE_COL_SYNONYMS = ["value", "amount", "actual", "plan", "val"]
ENTITY_COL_SYNONYMS = ["entity", "business_unit", "bu", "department", "cost_center"]


def _find_first_present(columns: Iterable[str], candidates: List[str]) -> Optional[str]:
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize common column names to: date, metric, value, entity (optional).

    - Trims whitespace and lowercases original column names for matching
    - Returns a copy with standardized column names where found
    """
    if df is None or df.empty:
        return df

    original_cols = list(df.columns)
    lower_map = {c: c.strip().lower() for c in original_cols}
    df = df.rename(columns=lower_map)

    date_col = _find_first_present(df.columns, DATE_COL_SYNONYMS)
    metric_col = _find_first_present(df.columns, METRIC_COL_SYNONYMS)
    value_col = _find_first_present(df.columns, VALUE_COL_SYNONYMS)
    entity_col = _find_first_present(df.columns, ENTITY_COL_SYNONYMS)

    rename_map = {}
    if date_col and date_col != "date":
        rename_map[date_col] = "date"
    if metric_col and metric_col != "metric":
        rename_map[metric_col] = "metric"
    if value_col and value_col != "value":
        rename_map[value_col] = "value"
    if entity_col and entity_col != "entity":
        rename_map[entity_col] = "entity"

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def parse_dates_to_month_end(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or "date" not in df.columns:
        return df
    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    # Normalize to month end for consistency
    result["date"] = result["date"].dt.to_period("M").dt.to_timestamp("M")
    return result


def coerce_numeric_values(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or "value" not in df.columns:
        return df
    result = df.copy()
    result["value"] = pd.to_numeric(result["value"], errors="coerce").fillna(0.0)
    return result


def prepare_tidy_frame(df: pd.DataFrame, series_name: str) -> pd.DataFrame:
    """Return a tidy DataFrame with columns: date, metric, value, series, [entity]."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "metric", "value", "series", "entity"])  # ensure schema

    df_std = standardize_columns(df)
    df_std = parse_dates_to_month_end(df_std)
    df_std = coerce_numeric_values(df_std)

    required_cols = {"date", "metric", "value"}
    missing = required_cols - set(df_std.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}. Expect columns: date, metric, value [entity optional].")

    tidy_cols = ["date", "metric", "value"] + (["entity"] if "entity" in df_std.columns else [])
    tidy = df_std[tidy_cols].copy()
    tidy["series"] = series_name
    # Enforce column order
    ordered = ["date", "metric", "value", "series"] + (["entity"] if "entity" in tidy.columns else [])
    return tidy[ordered]


def align_series(actuals: pd.DataFrame, plan: pd.DataFrame) -> pd.DataFrame:
    """Combine Actual and Plan into a single tidy frame.

    Output columns: date, metric, value, series, [entity]
    """
    tidy_actuals = prepare_tidy_frame(actuals, "Actual")
    tidy_plan = prepare_tidy_frame(plan, "Plan")

    # Align on required columns plus optional entity if present in both
    common_cols = ["date", "metric", "value", "series"] + (
        ["entity"] if ("entity" in tidy_actuals.columns and "entity" in tidy_plan.columns) else []
    )
    combined = pd.concat([tidy_actuals[common_cols], tidy_plan[common_cols]], ignore_index=True)

    # Ensure complete month-metric grid exists across series
    idx_cols = ["date", "metric"] + (["entity"] if "entity" in combined.columns else [])
    all_index = combined[idx_cols].drop_duplicates().sort_values(idx_cols)
    series_vals = combined["series"].drop_duplicates().tolist()

    # Build a complete cartesian product of idx_cols x series
    mesh = all_index.assign(key=1).merge(pd.DataFrame({"series": series_vals, "key": 1}), on="key").drop(columns="key")

    combined_full = mesh.merge(combined, on=idx_cols + ["series"], how="left")
    combined_full["value"] = combined_full["value"].fillna(0.0)

    return combined_full


def load_csv(path_or_buffer) -> pd.DataFrame:
    """Load CSV into DataFrame. Accepts local path or file-like object (e.g., Streamlit uploader)."""
    return pd.read_csv(path_or_buffer)

