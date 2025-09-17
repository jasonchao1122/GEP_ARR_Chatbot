# Finance Performance Dashboard & Analyst

A Streamlit dashboard that ingests Actuals and Plan CSVs, computes KPI variances, renders Plotly charts, and includes a chat agent that explains performance vs plan using the OpenAI API.

## Features
- Upload Actuals and Plan CSVs (columns: `date, metric, value, [entity]`)
- Auto-standardizes column names and parses dates to month-end
- KPI totals and variance computation by period and metric
- Plotly charts: Plan vs Actual trend, variance by metric, variance waterfall
- Chat agent to explain results; requires `OPENAI_API_KEY`
 - Upload a design slide image to auto-extract a color theme, then fine-tune via color pickers
 - Optional column mapping UI for custom CSV schemas

## Quickstart

1. Create and activate a virtual environment
```bash
python -m venv .venv && source .venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. (Optional) Set your OpenAI API key for the chat agent
```bash
export OPENAI_API_KEY=sk-...
```

4. Run the app
```bash
streamlit run app.py
```

5. Upload your CSVs or use the bundled samples

## Data Format

- Required columns: `date, metric, value`
- Optional column: `entity`
- Dates can be any parseable string; they will be normalized to month-end.
- The app also accepts some synonyms and will standardize to required names.

## Project Structure

```
finance_dashboard/
  __init__.py
  data_io.py
  kpi.py
  charts.py
  llm.py
app.py
requirements.txt
README.md
samples/
  actuals.csv
  plan.csv
```

## Notes
- The chat feature falls back with a helpful message if no API key is set.
- This is a reference implementation; adapt metrics and visuals for your business.