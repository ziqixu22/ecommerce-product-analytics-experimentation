import pandas as pd
from product_ds.data import clean_transactions, customer_level_transactions
from product_ds.metrics import monthly_kpis, cohort_retention


def sample_df():
    return pd.DataFrame({
        "Invoice": ["1", "2", "C3", "4"],
        "StockCode": ["A", "B", "C", "D"],
        "Description": ["a", "b", "c", "d"],
        "Quantity": [1, 2, -1, 1],
        "InvoiceDate": ["2010-01-01", "2010-02-01", "2010-02-02", "2010-03-01"],
        "Price": [10.0, 5.0, 5.0, 8.0],
        "Customer ID": [1, 1, 1, 2],
        "Country": ["UK", "UK", "UK", "FR"],
    })


def test_monthly_kpis():
    df = clean_transactions(sample_df())
    kpi = monthly_kpis(df)
    jan = kpi.loc[kpi["order_month"] == pd.Timestamp("2010-01-01")].iloc[0]
    assert jan["revenue"] == 10.0
    assert jan["orders"] == 1


def test_cohort_retention():
    df = customer_level_transactions(clean_transactions(sample_df()))
    r = cohort_retention(df)
    first = r.loc[(r["cohort_month"] == pd.Timestamp("2010-01-01")) & (r["months_since_cohort"] == 0)].iloc[0]
    assert first["retention_rate"] == 1.0
