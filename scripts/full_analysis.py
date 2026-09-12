from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import chisquare, norm
from sklearn.linear_model import LinearRegression
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str:
    lookup = {str(c).strip().lower().replace("_", "").replace(" ", ""): c for c in df.columns}
    for c in candidates:
        key = c.lower().replace("_", "").replace(" ", "")
        if key in lookup:
            return lookup[key]
    raise KeyError(f"Could not find any of {candidates}. Columns={list(df.columns)}")


def analyze_retail(xlsx: Path) -> tuple[dict, pd.DataFrame]:
    sheets = pd.read_excel(xlsx, sheet_name=None)
    raw = pd.concat(sheets.values(), ignore_index=True)
    invoice = _find_col(raw, ["Invoice", "InvoiceNo"])
    qty = _find_col(raw, ["Quantity"])
    dt = _find_col(raw, ["InvoiceDate"])
    price = _find_col(raw, ["Price", "UnitPrice"])
    customer = _find_col(raw, ["Customer ID", "CustomerID"])
    country = _find_col(raw, ["Country"])

    df = raw[[invoice, qty, dt, price, customer, country]].copy()
    df.columns = ["invoice", "quantity", "invoice_date", "unit_price", "customer_id", "country"]
    df["invoice"] = df["invoice"].astype(str)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["is_cancel"] = df["invoice"].str.upper().str.startswith("C")

    raw_invoices = int(df["invoice"].nunique())
    cancelled_invoices = int(df.loc[df["is_cancel"], "invoice"].nunique())
    clean = df[
        (~df["is_cancel"])
        & df["customer_id"].notna()
        & df["invoice_date"].notna()
        & (df["quantity"] > 0)
        & (df["unit_price"] > 0)
    ].copy()
    clean["revenue"] = clean["quantity"] * clean["unit_price"]
    clean["customer_id"] = clean["customer_id"].astype(str)

    orders = clean.groupby(["invoice", "customer_id", "invoice_date", "country"], as_index=False).agg(
        revenue=("revenue", "sum"), units=("quantity", "sum")
    )
    cust = orders.groupby("customer_id", as_index=False).agg(
        orders=("invoice", "nunique"), revenue=("revenue", "sum"), first_purchase=("invoice_date", "min")
    )
    repeat_rate = float((cust["orders"] > 1).mean())

    n_top = max(1, math.ceil(len(cust) * 0.10))
    top10_share = float(cust.nlargest(n_top, "revenue")["revenue"].sum() / cust["revenue"].sum())
    country_rev = clean.groupby("country")["revenue"].sum().sort_values(ascending=False)
    top_country = str(country_rev.index[0])
    top_country_share = float(country_rev.iloc[0] / country_rev.sum())

    clean["activity_month"] = clean["invoice_date"].dt.to_period("M")
    first_month = clean.groupby("customer_id")["activity_month"].min().rename("cohort_month")
    activity = clean[["customer_id", "activity_month"]].drop_duplicates().join(first_month, on="customer_id")
    activity["month_index"] = (
        (activity["activity_month"].dt.year - activity["cohort_month"].dt.year) * 12
        + (activity["activity_month"].dt.month - activity["cohort_month"].dt.month)
    )
    max_month = clean["activity_month"].max()
    retention = {}
    for k in [1, 3, 6, 12]:
        eligible_ids = first_month[first_month <= (max_month - k)].index
        if len(eligible_ids) == 0:
            retention[str(k)] = None
            continue
        retained = activity[(activity["month_index"] == k) & (activity["customer_id"].isin(eligible_ids))]["customer_id"].nunique()
        retention[str(k)] = float(retained / len(eligible_ids))

    monthly = clean.groupby(clean["invoice_date"].dt.to_period("M"))["revenue"].sum()
    peak_month = str(monthly.idxmax())
    peak_month_revenue = float(monthly.max())

    metrics = {
        "raw_rows": int(len(raw)),
        "raw_unique_invoices": raw_invoices,
        "cancelled_invoices": cancelled_invoices,
        "invoice_cancellation_rate": float(cancelled_invoices / raw_invoices),
        "clean_sales_rows": int(len(clean)),
        "completed_orders": int(orders["invoice"].nunique()),
        "unique_customers": int(cust["customer_id"].nunique()),
        "date_min": str(clean["invoice_date"].min()),
        "date_max": str(clean["invoice_date"].max()),
        "revenue_gbp": float(clean["revenue"].sum()),
        "average_order_value_gbp": float(orders["revenue"].mean()),
        "repeat_customer_rate": repeat_rate,
        "top_10pct_customer_revenue_share": top10_share,
        "top_country": top_country,
        "top_country_revenue_share": top_country_share,
        "retention_by_month_index": retention,
        "peak_revenue_month": peak_month,
        "peak_month_revenue_gbp": peak_month_revenue,
    }
    cohort_table = (
        activity.groupby(["cohort_month", "month_index"])["customer_id"].nunique().rename("active_customers").reset_index()
    )
    return metrics, cohort_table


def binary_effect(success_c: int, n_c: int, success_t: int, n_t: int) -> dict:
    pc, pt = success_c / n_c, success_t / n_t
    diff = pt - pc
    se = math.sqrt(pc * (1 - pc) / n_c + pt * (1 - pt) / n_t)
    z = diff / se if se else 0.0
    p = float(2 * (1 - norm.cdf(abs(z))))
    zc = float(norm.ppf(0.975))
    return {
        "control_rate": pc,
        "treatment_rate": pt,
        "absolute_lift": diff,
        "relative_lift": diff / pc if pc else None,
        "z_stat": z,
        "p_value": p,
        "ci_95_low": diff - zc * se,
        "ci_95_high": diff + zc * se,
    }


def analyze_criteo(path: Path) -> dict:
    con = duckdb.connect()
    src = str(path).replace("'", "''")
    q = f"read_csv_auto('{src}', header=true, sample_size=200000)"
    agg = con.execute(f"""
        SELECT treatment,
               COUNT(*) n,
               SUM(conversion)::BIGINT conversions,
               SUM(visit)::BIGINT visits
        FROM {q}
        GROUP BY treatment ORDER BY treatment
    """).df()
    rows = {int(r.treatment): r for _, r in agg.iterrows()}
    c, t = rows[0], rows[1]
    total_n = int(c.n + t.n)
    treat_share = float(t.n / total_n)
    obs = np.array([c.n, t.n], dtype=float)
    exp = np.array([0.15 * total_n, 0.85 * total_n], dtype=float)
    srm_stat, srm_p = chisquare(obs, f_exp=exp)

    visit = binary_effect(int(c.visits), int(c.n), int(t.visits), int(t.n))
    conversion = binary_effect(int(c.conversions), int(c.n), int(t.conversions), int(t.n))

    baseline = conversion["control_rate"]
    target = baseline * 1.10
    effect = abs(proportion_effectsize(baseline, target))
    n_power = int(math.ceil(NormalIndPower().solve_power(effect_size=effect, alpha=0.05, power=0.80, ratio=1.0)))

    quantiles = con.execute(f"SELECT quantile_cont(f0, [0.25,0.5,0.75]) FROM {q}").fetchone()[0]
    q1, q2, q3 = [float(x) for x in quantiles]
    hte = con.execute(f"""
        SELECT CASE WHEN f0 <= {q1} THEN 'Q1' WHEN f0 <= {q2} THEN 'Q2' WHEN f0 <= {q3} THEN 'Q3' ELSE 'Q4' END AS f0_quartile,
               treatment,
               COUNT(*) n,
               AVG(conversion) conversion_rate,
               AVG(visit) visit_rate
        FROM {q}
        GROUP BY 1,2 ORDER BY 1,2
    """).df()
    hte_rows = []
    for quartile, g in hte.groupby("f0_quartile"):
        gc = g[g.treatment == 0].iloc[0]
        gt = g[g.treatment == 1].iloc[0]
        hte_rows.append({
            "f0_quartile": quartile,
            "control_conversion": float(gc.conversion_rate),
            "treatment_conversion": float(gt.conversion_rate),
            "conversion_lift": float(gt.conversion_rate - gc.conversion_rate),
            "control_visit": float(gc.visit_rate),
            "treatment_visit": float(gt.visit_rate),
            "visit_lift": float(gt.visit_rate - gc.visit_rate),
        })

    sample = con.execute(f"SELECT f0,f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,treatment,conversion FROM {q} USING SAMPLE reservoir(1000000 ROWS) REPEATABLE(42)").df()
    X = sample[[f"f{i}" for i in range(12)] + ["treatment"]].to_numpy(dtype=float)
    y = sample["conversion"].to_numpy(dtype=float)
    lr = LinearRegression().fit(X, y)
    adjusted_ate = float(lr.coef_[-1])

    con.close()
    return {
        "rows": total_n,
        "control_n": int(c.n),
        "treatment_n": int(t.n),
        "treatment_share": treat_share,
        "srm_vs_85pct": {"chi_square": float(srm_stat), "p_value": float(srm_p)},
        "visit_effect": visit,
        "conversion_effect": conversion,
        "sample_size_per_arm_for_10pct_relative_conversion_lift": n_power,
        "regression_adjusted_conversion_ate_1m_sample": adjusted_ate,
        "heterogeneous_effect_by_f0_quartile": hte_rows,
    }


def pct(x: float | None) -> str:
    return "NA" if x is None else f"{100*x:.2f}%"


def money(x: float) -> str:
    return f"£{x:,.0f}"


def write_markdown(retail: dict, exp: dict, out: Path) -> None:
    r = retail
    e = exp
    lines = [
        "# Full Analysis Results",
        "",
        "These numbers were computed by the repository's GitHub Actions workflow from the public source files; they are not hand-entered estimates.",
        "",
        "## 1. E-commerce product analytics — UCI Online Retail II",
        "",
        f"- Raw transaction lines: **{r['raw_rows']:,}**",
        f"- Completed orders after removing cancellations/invalid sales: **{r['completed_orders']:,}**",
        f"- Identified customers: **{r['unique_customers']:,}**",
        f"- Completed-sales revenue: **{money(r['revenue_gbp'])}**",
        f"- Average order value: **{money(r['average_order_value_gbp'])}**",
        f"- Invoice cancellation rate: **{pct(r['invoice_cancellation_rate'])}**",
        f"- Repeat-customer rate: **{pct(r['repeat_customer_rate'])}**",
        f"- Top 10% of customers contribute **{pct(r['top_10pct_customer_revenue_share'])}** of completed-sales revenue.",
        f"- Largest country: **{r['top_country']}**, contributing **{pct(r['top_country_revenue_share'])}** of revenue.",
        f"- Month-1 / Month-3 / Month-6 retention: **{pct(r['retention_by_month_index']['1'])} / {pct(r['retention_by_month_index']['3'])} / {pct(r['retention_by_month_index']['6'])}**.",
        f"- Peak revenue month: **{r['peak_revenue_month']}** at **{money(r['peak_month_revenue_gbp'])}**.",
        "",
        "### Product takeaways",
        "",
        "1. **Customer value is concentrated.** The top-decile revenue share quantifies why lifecycle/retention work should focus on high-value repeat buyers, not only top-of-funnel acquisition.",
        "2. **Retention decays materially over time.** Cohort retention is more decision-useful than raw monthly active-customer counts because it separates growth from repeat behavior.",
        "3. **Cancellations are a guardrail.** Revenue reporting should exclude canceled invoices from realized sales while cancellation rate is monitored separately as a product/operations quality metric.",
        "4. **Geographic concentration matters.** Country-level revenue concentration limits how safely aggregate patterns can be generalized to every market.",
        "",
        "## 2. Randomized experimentation — Criteo Uplift",
        "",
        f"- Experiment rows: **{e['rows']:,}**",
        f"- Treatment share: **{pct(e['treatment_share'])}**",
        f"- Visit rate: control **{pct(e['visit_effect']['control_rate'])}**, treatment **{pct(e['visit_effect']['treatment_rate'])}**; absolute lift **{pct(e['visit_effect']['absolute_lift'])}** (95% CI {pct(e['visit_effect']['ci_95_low'])} to {pct(e['visit_effect']['ci_95_high'])}).",
        f"- Conversion rate: control **{pct(e['conversion_effect']['control_rate'])}**, treatment **{pct(e['conversion_effect']['treatment_rate'])}**; absolute lift **{pct(e['conversion_effect']['absolute_lift'])}** (95% CI {pct(e['conversion_effect']['ci_95_low'])} to {pct(e['conversion_effect']['ci_95_high'])}).",
        f"- Regression-adjusted conversion ATE on a deterministic 1M-row reservoir sample: **{pct(e['regression_adjusted_conversion_ate_1m_sample'])}**.",
        f"- Approx. sample size per arm to detect a 10% relative conversion lift at 80% power: **{e['sample_size_per_arm_for_10pct_relative_conversion_lift']:,}**.",
        "",
        "### Experiment takeaways",
        "",
        "1. **Statistical significance is not the same as product significance.** With millions of observations, tiny effects can be precisely estimated; launch decisions should use absolute lift and business value, not p-value alone.",
        "2. **Rare conversion outcomes require large samples.** Power calculations explain why conversion experiments need far more traffic than higher-base-rate engagement metrics such as visits.",
        "3. **Average treatment effects can hide heterogeneity.** The f0-quartile table in results/experiment_metrics.json is a reproducible first pass for checking whether segments respond differently.",
        "4. **Randomized and observational analyses answer different questions.** Retail transaction cohorts diagnose behavior; Criteo randomization supports causal treatment-effect estimates.",
        "",
        "## Interview narrative",
        "",
        "Business framing → define product health metrics → validate transaction semantics/cancellations → build customer cohorts → quantify retention/value concentration → validate experiment assignment → estimate treatment effects with uncertainty → check power/heterogeneity → translate results into launch and targeting decisions.",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--retail", type=Path, required=True)
    ap.add_argument("--criteo", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    retail, cohort = analyze_retail(args.retail)
    exp = analyze_criteo(args.criteo)
    (args.out / "retail_metrics.json").write_text(json.dumps(retail, indent=2), encoding="utf-8")
    (args.out / "experiment_metrics.json").write_text(json.dumps(exp, indent=2), encoding="utf-8")
    cohort.assign(cohort_month=cohort["cohort_month"].astype(str)).to_csv(args.out / "cohort_retention_long.csv", index=False)
    write_markdown(retail, exp, Path("RESULTS.md"))
    print(json.dumps({"retail": retail, "experiment": exp}, indent=2))


if __name__ == "__main__":
    main()
