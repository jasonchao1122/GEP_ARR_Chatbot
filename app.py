from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st

from finance_dashboard.data_io import align_series, load_csv
from finance_dashboard.kpi import build_variance_summary, compute_variance_by_metric_for_period, describe_totals_table, latest_period
from finance_dashboard.charts import time_series_totals_chart, variance_bar_by_metric, variance_waterfall
from finance_dashboard.llm import generate_explanation


st.set_page_config(page_title="Finance Performance Dashboard", layout="wide")

st.title("Finance Performance Dashboard and Analyst")
st.caption("Upload Actuals and Plan CSVs. Columns expected: date, metric, value, [entity].")


with st.sidebar:
    st.header("Data Upload")
    actuals_file = st.file_uploader("Actuals CSV", type=["csv"], key="actuals")
    plan_file = st.file_uploader("Plan CSV", type=["csv"], key="plan")
    st.markdown("Example columns: `date, metric, value, entity` (entity optional)")
    entity_filter = st.text_input("Entity filter (optional)")
    top_n = st.slider("Top N for charts", min_value=3, max_value=25, value=10)


def _load_example_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    example_actuals = os.path.join(os.path.dirname(__file__), "samples", "actuals.csv")
    example_plan = os.path.join(os.path.dirname(__file__), "samples", "plan.csv")
    if os.path.exists(example_actuals) and os.path.exists(example_plan):
        return pd.read_csv(example_actuals), pd.read_csv(example_plan)
    # fallback tiny dataset
    dates = pd.date_range("2025-01-31", periods=6, freq="M")
    metrics = ["Revenue", "COGS", "OpEx"]
    a_rows, p_rows = [], []
    for d in dates:
        for m in metrics:
            p_rows.append({"date": d, "metric": m, "value": 1000 if m == "Revenue" else (400 if m == "COGS" else 300)})
            a_rows.append({"date": d, "metric": m, "value": 1100 if m == "Revenue" else (420 if m == "COGS" else 280)})
    return pd.DataFrame(a_rows), pd.DataFrame(p_rows)


if actuals_file and plan_file:
    actuals_df = load_csv(actuals_file)
    plan_df = load_csv(plan_file)
else:
    st.info("Using example data. Upload your CSVs to replace.")
    actuals_df, plan_df = _load_example_data()


tidy = align_series(actuals_df, plan_df)

if entity_filter:
    if "entity" in tidy.columns:
        tidy = tidy[tidy["entity"].astype(str).str.contains(entity_filter, case=False, na=False)]
    else:
        st.warning("No `entity` column found; entity filter ignored.")

totals_table = describe_totals_table(tidy)
current_period = latest_period(tidy)

col1, col2, col3, col4 = st.columns(4)
if current_period is not None:
    summary = build_variance_summary(tidy, current_period)
    if summary:
        col1.metric("Period", summary.period.strftime("%b %Y"))
        col2.metric("Plan", f"{summary.total_plan:,.0f}")
        col3.metric("Actual", f"{summary.total_actual:,.0f}")
        col4.metric("Variance", f"{summary.total_variance:,.0f} ({summary.total_variance_pct:.1f}%)")


with st.expander("Totals Table", expanded=True):
    st.dataframe(totals_table, use_container_width=True)

ts_fig = time_series_totals_chart(totals_table)
st.plotly_chart(ts_fig, use_container_width=True)

if current_period is not None:
    var_by_metric = compute_variance_by_metric_for_period(tidy, current_period)
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(variance_bar_by_metric(var_by_metric, current_period), use_container_width=True)
    with col_b:
        st.plotly_chart(variance_waterfall(var_by_metric, current_period, top_n=top_n), use_container_width=True)


st.subheader("Ask the Analyst")
question = st.text_input("Ask a question about performance", value="Explain the main drivers vs plan and highlight risks/opportunities.")
if st.button("Explain"):
    if current_period is None:
        st.warning("No data available to explain.")
    else:
        summary = build_variance_summary(tidy, current_period)
        if summary:
            payload = {
                "period": summary.period.strftime("%Y-%m-%d"),
                "total_plan": summary.total_plan,
                "total_actual": summary.total_actual,
                "total_variance": summary.total_variance,
                "total_variance_pct": summary.total_variance_pct,
                "top_positive_contributors": summary.top_positive_contributors,
                "top_negative_contributors": summary.top_negative_contributors,
            }
            with st.spinner("Generating explanation..."):
                result = generate_explanation(payload, user_question=question)
            st.write(result)
        else:
            st.warning("Could not build summary.")

