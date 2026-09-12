# Full Analysis Results

These numbers were computed by the repository's GitHub Actions workflow from the public source files; they are not hand-entered estimates.

## 1. E-commerce product analytics — UCI Online Retail II

- Raw transaction lines: **1,067,371**
- Completed orders after removing cancellations/invalid sales: **36,969**
- Identified customers: **5,878**
- Completed-sales revenue: **£17,743,429**
- Average order value: **£479**
- Invoice cancellation rate: **15.46%**
- Repeat-customer rate: **72.39%**
- Top 10% of customers contribute **63.93%** of completed-sales revenue.
- Largest country: **United Kingdom**, contributing **82.98%** of revenue.
- Month-1 / Month-3 / Month-6 / Month-12 retention: **23.15% / 24.51% / 21.78% / 22.34%**.
- Peak revenue month: **2010-11** at **£1,172,336**.

### Product takeaways

1. **Customer value is concentrated.** The top-decile revenue share quantifies why lifecycle/retention work should focus on high-value repeat buyers, not only top-of-funnel acquisition.
2. **Longer-term cohort retention settles in the low-20% range.** Month-1 through Month-12 retention stays roughly 22–25%; this is more decision-useful than raw monthly active-customer counts because it separates cohort growth from repeat behavior.
3. **Cancellations are a guardrail.** Revenue reporting should exclude canceled invoices from realized sales while cancellation rate is monitored separately as a product/operations quality metric.
4. **Geographic concentration matters.** Country-level revenue concentration limits how safely aggregate patterns can be generalized to every market.

## 2. Randomized experimentation — Criteo Uplift

- Experiment rows: **13,979,592**
- Treatment share: **85.00%**
- Visit rate: control **3.82%**, treatment **4.85%**; absolute lift **1.03 pp** (95% CI **1.006 to 1.063 pp**), relative lift **27.07%**.
- Conversion rate: control **0.194%**, treatment **0.309%**; absolute lift **0.115 pp** (95% CI **0.108 to 0.122 pp**), relative lift **59.45%**.
- Regression-adjusted conversion ATE on a deterministic 1M-row reservoir sample: **0.077 pp**.
- Approx. sample size per arm to detect a 10% relative conversion lift at 80% power: **848,466**.
- Sample-ratio-mismatch test against the intended 85/15 allocation: **p = 0.9989**, showing no allocation anomaly.

### Heterogeneous treatment effects (conversion lift by f0 quartile)

- Q1: **+0.038 pp**
- Q2: **+0.386 pp**
- Q3: **+0.019 pp**
- Q4: **+0.010 pp**

The Q2 segment shows materially larger response than the other quartiles. This is a useful targeting hypothesis, but segment discovery should be validated in a follow-up experiment rather than treated as guaranteed production uplift.

### Experiment takeaways

1. **Statistical significance is not the same as product significance.** With millions of observations, tiny effects can be precisely estimated; decisions should use absolute lift and business value, not p-value alone.
2. **Rare conversion outcomes require large samples.** Power calculations explain why conversion experiments need far more traffic than higher-base-rate engagement metrics such as visits.
3. **Average treatment effects can hide heterogeneity.** The f0 quartile analysis shows a much stronger response in Q2, motivating targeted follow-up testing.
4. **Randomized and observational analyses answer different questions.** Retail transaction cohorts diagnose behavior; Criteo randomization supports causal treatment-effect estimates.

## Interview narrative

Business framing → define product health metrics → validate transaction semantics/cancellations → build customer cohorts → quantify retention/value concentration → validate experiment assignment → estimate treatment effects with uncertainty → check power/heterogeneity → translate results into rollout and targeting decisions.
