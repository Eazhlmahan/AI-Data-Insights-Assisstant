"""
AI-Powered Data Insights Assistant
----------------------------------
Upload a CSV, ask a question in plain English, get back:
  - the pandas code the LLM generated
  - the computed result
  - an auto-picked chart (line / bar / KPI)

Run with:  streamlit run app.py
Needs an ANTHROPIC_API_KEY environment variable set.
"""

import io
import os
import re
import traceback

import pandas as pd
import plotly.express as px
import streamlit as st
from google import genai

# ----------------------------- CONFIG ----------------------------------

st.set_page_config(page_title="AI Data Insights Assistant", layout="wide")
MODEL = "gemini-1.5-flash"

# Use GEMINI_API_KEY from environment or streamlit secrets.
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Only these names are allowed inside the generated code's exec() sandbox.
SAFE_BUILTINS = {"len": len, "sum": sum, "min": min, "max": max, "round": round,
                 "sorted": sorted, "abs": abs, "range": range}

BANNED_PATTERNS = [
    r"\bimport\b", r"\bopen\s*\(", r"\bexec\s*\(", r"\beval\s*\(",
    r"\b__\w+__\b", r"\bos\.", r"\bsys\.", r"\bsubprocess\b", r"\bshutil\b",
    r"\bdel\s+", r"\bglobals\s*\(", r"\blocals\s*\(",
]


# ------------------------- LLM -> PANDAS CODE ---------------------------

def build_prompt(question: str, df: pd.DataFrame) -> str:
    schema = "\n".join(f"- {c} ({df[c].dtype})" for c in df.columns)
    sample = df.head(3).to_string()
    return f"""You are a data analyst assistant. You are given a pandas DataFrame called `df`.

Schema:
{schema}

Sample rows:
{sample}

User question: "{question}"

Write ONLY a single Python expression or short snippet (no imports, no function
definitions, no file/network access) that computes the answer using `df` and
assigns the final output to a variable called `result`. `result` should be
either a pandas DataFrame/Series (for anything chartable) or a plain
number/string (for a single-value answer).

Return ONLY the code, no explanation, no markdown fences.
"""


def ask_llm_for_code(question: str, df: pd.DataFrame) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=build_prompt(question, df),
    )
    code = response.text
    return code.strip().strip("`").replace("python\n", "", 1)


def is_code_safe(code: str) -> bool:
    return not any(re.search(p, code) for p in BANNED_PATTERNS)


def run_generated_code(code: str, df: pd.DataFrame):
    local_vars = {"df": df, "pd": pd}
    exec(compile(code, "<llm_code>", "exec"), {"__builtins__": SAFE_BUILTINS}, local_vars)
    return local_vars.get("result")


# ------------------------------ CHARTING --------------------------------

def auto_chart(result):
    """Pick a reasonable chart type based on the shape of `result`."""
    if isinstance(result, (int, float, str)):
        st.metric("Result", result)
        return

    if isinstance(result, pd.Series):
        result = result.reset_index()
        result.columns = ["category", "value"]

    if isinstance(result, pd.DataFrame):
        if result.shape[1] < 2:
            st.dataframe(result)
            return
        x_col, y_col = result.columns[0], result.columns[1]
        # datetime-like x axis -> line chart, else bar chart
        if pd.api.types.is_datetime64_any_dtype(result[x_col]) or "date" in str(x_col).lower():
            fig = px.line(result, x=x_col, y=y_col, markers=True)
        else:
            fig = px.bar(result, x=x_col, y=y_col)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(result, use_container_width=True)


# --------------------------------- UI ------------------------------------

st.title("📊 AI-Powered Data Insights Assistant")
st.caption("Upload a CSV, ask a question in plain English, get an answer + chart.")

uploaded = st.file_uploader("Upload CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    st.session_state["df"] = df
    with st.expander("Preview data"):
        st.dataframe(df.head(20))
        st.caption(f"{df.shape[0]} rows × {df.shape[1]} columns")

if "df" in st.session_state:
    df = st.session_state["df"]
    question = st.text_input(
        "Ask a question about your data",
        placeholder="e.g. What are total sales by region?",
    )

    if st.button("Analyze") and question:
        with st.spinner("Thinking..."):
            try:
                code = ask_llm_for_code(question, df)

                if not is_code_safe(code):
                    st.error("Generated code failed a safety check — try rephrasing your question.")
                else:
                    with st.expander("Generated code"):
                        st.code(code, language="python")

                    result = run_generated_code(code, df)
                    auto_chart(result)

            except Exception as e:
                st.error(f"Couldn't answer that: {e}")
                with st.expander("Details"):
                    st.code(traceback.format_exc())
else:
    st.info("Upload a CSV to get started, or use the sample Superstore dataset in /data.")
