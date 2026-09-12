from __future__ import annotations
import pandas as pd


def monthly_kpis(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["order_month"] = pd.to_datetime(x["InvoiceDate"]).dt.to_period("M").dt.to_timestamp()
    orders = x.groupby("order_month")["Invoice"].nunique().rename("orders")
    customers = x.groupby("order_month")["Customer ID"].nunique().rename("customers")
    revenue = x.loc[(~x["is_cancelled"]) & (x["Quantity"] > 0) & (x["Price"] > 0)].groupby("order_month")["revenue"].sum().rename("revenue")
    cancellations = x.loc[x["is_cancelled"]].groupby("order_month")["Invoice"].nunique().rename("cancelled_orders")
    out = pd.concat([orders, customers, revenue, cancellations], axis=1).fillna(0).reset_index()
    out["cancellation_rate"] = out["cancelled_orders"] / out["orders"].replace(0, pd.NA)
    out["revenue_per_customer"] = out["revenue"] / out["customers"].replace(0, pd.NA)
    return out


def cohort_retention(customer_tx: pd.DataFrame) -> pd.DataFrame:
    activity = (
        customer_tx[["Customer ID", "cohort_month", "months_since_cohort"]]
        .drop_duplicates()
        .groupby(["cohort_month", "months_since_cohort"])["Customer ID"]
        .nunique()
        .rename("active_customers")
        .reset_index()
    )
    cohort_size = (
        activity.loc[activity["months_since_cohort"] == 0, ["cohort_month", "active_customers"]]
        .rename(columns={"active_customers": "cohort_size"})
    )
    out = activity.merge(cohort_size, on="cohort_month", how="left")
    out["retention_rate"] = out["active_customers"] / out["cohort_size"]
    return out


def customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[(~df["is_cancelled"]) & (df["Quantity"] > 0) & (df["Price"] > 0) & df["Customer ID"].notna()].copy()
    return (
        valid.groupby("Customer ID")
        .agg(
            orders=("Invoice", "nunique"),
            revenue=("revenue", "sum"),
            first_order=("InvoiceDate", "min"),
            last_order=("InvoiceDate", "max"),
        )
        .assign(repeat_customer=lambda d: d["orders"] > 1)
        .reset_index()
    )
