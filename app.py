from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st

from finance_dashboard.data_io import align_series, load_csv
from finance_dashboard.kpi import build_variance_summary, compute_variance_by_metric_for_period, describe_totals_table, latest_period
from finance_dashboard.charts import time_series_totals_chart, variance_bar_by_metric, variance_waterfall
from finance_dashboard.theme import extract_palette, get_default_theme, infer_theme_from_palette
from finance_dashboard.llm import generate_explanation


st.set_page_config(page_title="Finance Performance Dashboard", layout="wide")

st.title("Finance Performance Dashboard and Analyst")
st.caption("Upload Actuals and Plan CSVs. Columns expected: date, metric, value, [entity].")


with st.sidebar:
    st.header("Data Uploads")
    actuals_file = st.file_uploader("Actuals CSV", type=["csv"], key="actuals")
    plan_file = st.file_uploader("Plan CSV", type=["csv"], key="plan")
    st.markdown("Example columns: `date, metric, value, entity` (entity optional)")

    with st.expander("Column Mapping (optional)"):
        use_mapping = st.checkbox("Use custom column mapping", value=False)
        actuals_mapping = {}
        plan_mapping = {}
        if actuals_file is not None:
            tmp_df = pd.read_csv(actuals_file)
            cols = list(tmp_df.columns)
            def pick(label, options, key):
                return st.selectbox(label, options=["<none>"] + options, index=options.index("date") + 1 if "date" in options else 0, key=key)
            def picker_block(df_cols, prefix):
                date_col = st.selectbox("Actuals date", options=["<none>"] + df_cols, index=(df_cols.index("date") + 1) if "date" in df_cols else 0, key=f"{prefix}-date")
                metric_col = st.selectbox("Actuals metric", options=["<none>"] + df_cols, index=(df_cols.index("metric") + 1) if "metric" in df_cols else 0, key=f"{prefix}-metric")
                value_col = st.selectbox("Actuals value", options=["<none>"] + df_cols, index=(df_cols.index("value") + 1) if "value" in df_cols else 0, key=f"{prefix}-value")
                entity_col = st.selectbox("Actuals entity (optional)", options=["<none>"] + df_cols, index=(df_cols.index("entity") + 1) if "entity" in df_cols else 0, key=f"{prefix}-entity")
                return {"date": date_col, "metric": metric_col, "value": value_col, "entity": entity_col}
            actuals_mapping = picker_block(cols, "act")
        if plan_file is not None:
            tmp_df = pd.read_csv(plan_file)
            cols = list(tmp_df.columns)
            def picker_block_plan(df_cols, prefix):
                date_col = st.selectbox("Plan date", options=["<none>"] + df_cols, index=(df_cols.index("date") + 1) if "date" in df_cols else 0, key=f"{prefix}-date")
                metric_col = st.selectbox("Plan metric", options=["<none>"] + df_cols, index=(df_cols.index("metric") + 1) if "metric" in df_cols else 0, key=f"{prefix}-metric")
                value_col = st.selectbox("Plan value", options=["<none>"] + df_cols, index=(df_cols.index("value") + 1) if "value" in df_cols else 0, key=f"{prefix}-value")
                entity_col = st.selectbox("Plan entity (optional)", options=["<none>"] + df_cols, index=(df_cols.index("entity") + 1) if "entity" in df_cols else 0, key=f"{prefix}-entity")
                return {"date": date_col, "metric": metric_col, "value": value_col, "entity": entity_col}
            plan_mapping = picker_block_plan(cols, "plan")

    st.divider()
    st.header("Design Slide (optional)")
    design_img = st.file_uploader("Upload slide image (PNG/JPG)", type=["png", "jpg", "jpeg"], key="design")
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
    actuals_df = pd.read_csv(actuals_file)
    plan_df = pd.read_csv(plan_file)
    # Apply optional mapping by renaming to standard names
    if 'use_mapping' in locals() and use_mapping:
        def apply_mapping(df, mapping):
            df2 = df.copy()
            rename_map = {}
            for std_col in ["date", "metric", "value", "entity"]:
                src = mapping.get(std_col)
                if src and src != "<none>" and src in df2.columns:
                    rename_map[src] = std_col
            if rename_map:
                df2 = df2.rename(columns=rename_map)
            return df2
        actuals_df = apply_mapping(actuals_df, actuals_mapping)
        plan_df = apply_mapping(plan_df, plan_mapping)
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

if 'theme' not in st.session_state:
    st.session_state.theme = get_default_theme()

with st.expander("Theme", expanded=False):
    # If slide provided, extract palette and prefill theme
    if design_img is not None:
        st.image(design_img, caption="Design slide", use_column_width=True)
        palette = extract_palette(design_img, color_count=6)
        st.write("Extracted palette:")
        st.write(" ".join([f"<span style='display:inline-block;width:20px;height:20px;background:{c};border:1px solid #ccc;'></span>" for c in palette]), unsafe_allow_html=True)
        inferred = infer_theme_from_palette(palette)
        st.session_state.theme.update(inferred)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.session_state.theme["plan"] = st.color_picker("Plan", st.session_state.theme.get("plan", "#1f77b4"))
    with c2:
        st.session_state.theme["actual"] = st.color_picker("Actual", st.session_state.theme.get("actual", "#ff7f0e"))
    with c3:
        st.session_state.theme["positive"] = st.color_picker("Positive", st.session_state.theme.get("positive", "#2ca02c"))
    with c4:
        st.session_state.theme["negative"] = st.color_picker("Negative", st.session_state.theme.get("negative", "#d62728"))

ts_fig = time_series_totals_chart(totals_table, theme=st.session_state.theme)
st.plotly_chart(ts_fig, use_container_width=True)

if current_period is not None:
    var_by_metric = compute_variance_by_metric_for_period(tidy, current_period)
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(variance_bar_by_metric(var_by_metric, current_period, theme=st.session_state.theme), use_container_width=True)
    with col_b:
        st.plotly_chart(variance_waterfall(var_by_metric, current_period, top_n=top_n, theme=st.session_state.theme), use_container_width=True)


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

