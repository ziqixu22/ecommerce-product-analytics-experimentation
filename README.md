# E-commerce Product Analytics & Experimentation Platform

A reproducible Product Data Science portfolio project built around two public datasets:

- **UCI Online Retail II** for real transaction-level product analytics, customer cohorts, retention, revenue, and cancellation behavior.
- **Criteo Uplift** for randomized incrementality experiments with treatment assignment and conversion/visit outcomes.

The project mirrors an industry Product Data Scientist workflow:

`raw transactions -> validated analytics tables -> SQL product metrics -> cohort/retention analysis -> experiment QA -> treatment-effect estimation -> heterogeneous-effect analysis -> business recommendation`

## Verified full-data highlights

The full analysis was executed in GitHub Actions against the public source files. See [`RESULTS.md`](RESULTS.md) and `results/*.json` for the persisted outputs.

### Product analytics — UCI Online Retail II

- **1,067,371** raw transaction lines across two years
- **36,969** completed orders from **5,878** identified customers after removing cancellations/invalid sales
- **£17.74M** completed-sales revenue; **£479** average order value
- **15.46%** invoice cancellation rate
- **72.39%** repeat-customer rate
- Top 10% of customers contribute **63.93%** of completed-sales revenue
- UK contributes **82.98%** of revenue
- Month-1 / Month-3 / Month-6 / Month-12 cohort retention: **23.15% / 24.51% / 21.78% / 22.34%**

### Randomized experimentation — Criteo Uplift

- **13,979,592** randomized experiment rows; observed treatment share **85.00%**
- Sample-ratio-mismatch test versus the intended 85/15 allocation: **p = 0.9989**
- Visit rate increased from **3.82% to 4.85%**: **+1.03 percentage points** (95% CI **+1.006 to +1.063 pp**)
- Conversion increased from **0.194% to 0.309%**: **+0.115 pp** (95% CI **+0.108 to +0.122 pp**)
- A 10% relative conversion lift at the observed baseline requires about **848,466 users per arm** for 80% power
- Exploratory heterogeneity analysis found the strongest conversion response in the second `f0` quartile (**+0.386 pp**), motivating targeted follow-up validation rather than an unqualified targeting claim

## Business questions

### Product analytics
- How much revenue is generated and how does it change over time?
- What share of orders are cancellations/returns?
- Which countries, products, and customers drive revenue concentration?
- How do customer cohorts retain and generate revenue over time?
- How do repeat-purchase behavior and order frequency evolve?

### Experimentation
- Is treatment allocation balanced?
- What are treatment effects on visit and conversion?
- What are absolute lift, relative lift, confidence intervals, and statistical significance?
- How large would a future experiment need to be?
- Does treatment impact vary across user segments/features?
- Would the result justify broad rollout, targeted validation, or another experiment?

## Why two datasets?

Online Retail II is observational commerce data and is excellent for product-health analysis, but it has no randomized treatment assignment. Criteo Uplift contains real randomized incrementality-test data but anonymizes product context. Keeping these workstreams separate avoids pretending observational differences are causal.

## Architecture

```text
UCI Online Retail II                    Criteo Uplift
        |                                    |
        v                                    v
transaction validation                 experiment QA
        |                                    |
        v                                    v
analytics tables / SQL                ATE / confidence intervals
        |                                    |
        v                                    v
revenue, cohorts, retention           regression adjustment
repeat purchase, cancellations             |
        |                                    v
        |                               heterogeneous effects
        \____________________________________/
                         |
                         v
                  decision synthesis
```

## Repository structure

```text
.
├── README.md
├── RESULTS.md
├── pyproject.toml
├── results/
│   ├── retail_metrics.json
│   └── experiment_metrics.json
├── scripts/
│   ├── download_data.py
│   └── full_analysis.py
├── sql/
│   ├── product_metrics.sql
│   └── cohort_retention.sql
├── src/product_ds/
│   ├── data.py
│   ├── metrics.py
│   ├── experiment.py
│   └── run_experiment.py
├── tests/
└── docs/
    ├── architecture.md
    └── interview_guide.md
```

## Data sources

### UCI Online Retail II
Source: UCI Machine Learning Repository, dataset ID 502.

The project combines both workbook sheets, identifies cancellation invoices, removes non-positive quantities/prices and missing customer IDs from completed-sales metrics, then derives revenue, orders, repeat purchasing, cohort month, and retention.

### Criteo Uplift
Source: Hugging Face dataset `criteo/criteo-uplift`.

The full randomized dataset contains anonymized features `f0`-`f11`, `treatment`, `conversion`, `visit`, and `exposure`. Raw data is intentionally not committed to Git; the full-analysis workflow downloads it from the public source.

## Core methods

**SQL / analytics**
- CTEs and window functions
- monthly revenue and order volume
- cancellation-rate guardrail
- repeat-purchase analysis
- cohort assignment and retention matrix
- customer and geography revenue concentration

**Experimentation / statistics**
- sample-ratio-mismatch checks
- two-sample proportion tests
- absolute and relative lift
- confidence intervals
- power / minimum sample size
- regression-adjusted treatment effect
- segment-level heterogeneous-effect analysis

## Interpretation

Three ideas matter more than any single metric:

1. **Diagnosis and causality are different.** The retail data tells us what customer behavior looks like; the randomized Criteo data tells us what the treatment caused.
2. **Effect size matters more than p-value alone.** With nearly 14M experiment rows, very small effects can be statistically precise; decisions should focus on absolute lift, uncertainty, economics, and guardrails.
3. **Exploratory segments are hypotheses.** The strong Q2 response is interesting, but it should be validated in a pre-specified follow-up experiment before production targeting.

## Testing and reproducibility

The statistical core is unit tested and GitHub Actions CI passes. A separate full-analysis workflow downloads the public datasets, runs the analysis, writes `RESULTS.md`/JSON outputs, and uploads the run artifact.

```bash
PYTHONPATH=src pytest -q
```

The project never silently substitutes synthetic data for a missing public source.

## Resume-ready description

> Built a reproducible product analytics and experimentation platform across 1.07M retail transaction lines and 13.98M randomized treatment observations, combining SQL/Python cohort and retention analysis with experiment QA, treatment-effect estimation, statistical power, and heterogeneous-effect analysis.

## Why this is not a toy project

The project separates observational analytics from randomized causal measurement, executes against full public datasets, persists verified outputs, uses modular code/tests/CI rather than notebook-only analysis, explicitly checks experiment validity, and translates statistical results into decision-oriented takeaways rather than stopping at a model score.
