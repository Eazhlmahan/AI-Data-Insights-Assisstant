# AI-Powered Data Insights Assistant

Ask your data questions in plain English. This app converts natural-language
questions into pandas code using Claude, runs it against your dataset, and
automatically renders the right chart (line for trends, bar for comparisons,
KPI card for single numbers).

**Example:** upload a sales CSV and ask *"What are total sales by region?"* —
get a bar chart back in seconds, no SQL or pandas needed.

## Why I built this

Most data analyst portfolios stop at dashboards. This project shows the next
step: using an LLM to make analysis conversational, while still keeping a
human-readable, auditable trail (the generated code is always shown, not
hidden behind a black box).

## Tech stack

- **Python / Pandas** — data handling
- **Claude API (Anthropic)** — natural language → pandas code generation
- **Streamlit** — UI
- **Plotly** — auto-generated charts

## How it works

1. User uploads a CSV (or the included sample Superstore dataset).
2. The app sends the dataframe's schema + a sample of rows + the user's
   question to Claude, asking for a short pandas snippet that computes the
   answer into a variable called `result`.
3. The generated code is checked against a blocklist (no imports, no file/
   network/OS access, no `eval`/`exec`) before running.
4. The code executes in a restricted namespace; the result is shown as a
   table, chart, or KPI depending on its shape.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python data_cleaning.py      # produces data/superstore_sales_clean.csv
streamlit run app.py
```

## Data

Sample dataset: Superstore Sales (8,399 orders, 21 columns). Raw source had
a broken line-terminator, one garbage row, and missing values in
`Product Base Margin` — see `data_cleaning.py` for the fix (category-wise
median imputation instead of a global fill, since margins vary a lot across
product categories).

## Known limitations (worth mentioning in interviews)

- LLM-generated code is sandboxed but not bulletproof — this is a portfolio
  project, not a production tool for untrusted users.
- Works best on single-table, tidy data. Multi-table joins would need a
  schema description added to the prompt.
- No conversation memory yet — each question is answered independently.

## Possible extensions

- Add SQL support for querying a real database instead of an in-memory CSV.
- Add a feedback loop where the user can correct a wrong chart choice.
- Cache repeated questions to cut down on API calls.
