from __future__ import annotations
from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {"Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"}


def read_online_retail(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None)
        df = pd.concat(sheets.values(), ignore_index=True)
    else:
        df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    return clean_transactions(df)


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["InvoiceDate"] = pd.to_datetime(out["InvoiceDate"], errors="coerce")
    out["Customer ID"] = pd.to_numeric(out["Customer ID"], errors="coerce")
    out["Quantity"] = pd.to_numeric(out["Quantity"], errors="coerce")
    out["Price"] = pd.to_numeric(out["Price"], errors="coerce")
    out = out.dropna(subset=["Invoice", "InvoiceDate", "StockCode"])
    out["is_cancelled"] = out["Invoice"].astype(str).str.startswith("C")
    out["revenue"] = out["Quantity"] * out["Price"]
    out["order_month"] = out["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    return out


def customer_level_transactions(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[(~df["is_cancelled"]) & (df["Quantity"] > 0) & (df["Price"] > 0) & df["Customer ID"].notna()].copy()
    first = valid.groupby("Customer ID")["InvoiceDate"].transform("min")
    valid["cohort_month"] = first.dt.to_period("M").dt.to_timestamp()
    valid["months_since_cohort"] = (
        (valid["order_month"].dt.year - valid["cohort_month"].dt.year) * 12
        + valid["order_month"].dt.month - valid["cohort_month"].dt.month
    )
    return valid
