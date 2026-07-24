"""
Cleans the raw Superstore Sales dataset.

Raw source: https://raw.githubusercontent.com/curran/data/gh-pages/superstoreSales/superstoreSales.csv

Issues found in the raw file:
  1. File uses \\r as the row line-terminator instead of \\n (needs
     lineterminator='\\r' when reading with pandas, plus a latin-1 -> utf-8
     re-encode first).
  2. One fully-blank garbage row (only Row ID populated) -> dropped.
  3. 'Product Base Margin' has 64 missing values -> filled with the
     median margin for that row's Product Category (better than a global
     median since margins vary a lot by category).
  4. 'Order Date' / 'Ship Date' are strings -> parsed to datetime.
  5. 'Order ID' / 'Row ID' loaded as floats because of the missing row -> cast to int.

Run: python data_cleaning.py
Output: data/superstore_sales_clean.csv
"""

import pandas as pd

RAW_URL = "https://raw.githubusercontent.com/curran/data/gh-pages/superstoreSales/superstoreSales.csv"


def clean(raw_path_or_url: str = RAW_URL) -> pd.DataFrame:
    df = pd.read_csv(raw_path_or_url, encoding="latin1", lineterminator="\r")
    df.columns = [c.strip() for c in df.columns]

    df = df.dropna(subset=["Order ID"])

    df["Product Base Margin"] = df.groupby("Product Category")["Product Base Margin"].transform(
        lambda x: x.fillna(x.median())
    )

    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"] = pd.to_datetime(df["Ship Date"])
    df["Order ID"] = df["Order ID"].astype(int)
    df["Row ID"] = df["Row ID"].astype(int)

    return df


if __name__ == "__main__":
    cleaned = clean()
    cleaned.to_csv("data/superstore_sales_clean.csv", index=False)
    print(f"Cleaned dataset: {cleaned.shape[0]} rows, {cleaned.shape[1]} cols, "
          f"{cleaned.isnull().sum().sum()} nulls remaining")
