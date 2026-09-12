# Step-by-Step Learning Guide — Product Analytics & Experimentation

This guide explains the project in the order you should learn and present it in interviews.

## 1. Business framing

The project has two separate questions:

1. **What is happening in the e-commerce business?**
   - revenue
   - cancellations
   - repeat customers
   - customer concentration
   - cohort retention

2. **Did a treatment cause a measurable change in behavior?**
   - visit rate
   - conversion rate
   - treatment effect
   - confidence interval
   - power
   - heterogeneity

The first question is observational product analytics. The second is causal experimentation. They use different datasets on purpose.

## 2. Product analytics data — UCI Online Retail II

### Raw data

The full dataset contains **1,067,371 transaction lines** from 2009-12-01 through 2011-12-09.

Key fields:
- Invoice
- StockCode
- Description
- Quantity
- InvoiceDate
- Price
- Customer ID
- Country

### Why this is not immediately an order table

Each row is an invoice line, not an order. One invoice can contain multiple products. Therefore:

- row count != order count
- revenue must be summed across lines
- order-level metrics require aggregation by invoice

## 3. Cleaning rules

Completed-sales metrics exclude:

- invoices marked as cancellation
- non-positive quantity
- non-positive price
- missing customer ID when customer-level metrics are required

Why? Because realized revenue should not count canceled or invalid sales.

But cancellations are not discarded conceptually. They become a **guardrail metric**.

### Result

- Raw invoice lines: **1,067,371**
- Completed orders: **36,969**
- Identified customers: **5,878**
- Invoice cancellation rate: **15.46%**

### Interview takeaway

> I separated realized-sales metrics from cancellation behavior so that revenue was not overstated while cancellations remained visible as an operational guardrail.

## 4. Revenue and customer value

For each completed line:

`revenue = quantity * price`

Then aggregate by invoice for order value, and by customer for customer value.

### Results

- Completed-sales revenue: **£17.74M**
- Average order value: **£479**
- Repeat-customer rate: **72.39%**
- Top 10% of customers contribute **63.93%** of revenue
- United Kingdom contributes **82.98%** of revenue
- Peak revenue month: **2010-11**, approximately **£1.17M**

### Takeaway

Customer value is highly concentrated. That suggests retention and lifecycle strategy should prioritize high-value repeat customers rather than treating all customers equally.

Geographic concentration also means aggregate results should not automatically be generalized to every market.

## 5. Cohort retention

### Why cohorts?

Raw active-customer counts mix together:
- customer acquisition
- repeat behavior

A cohort groups customers by first purchase month, then asks what fraction return in later months.

### Calculation

For each customer:
1. find first purchase month
2. assign cohort month
3. identify each later activity month
4. compute `month_index = activity_month - cohort_month`
5. retention = returning customers / original cohort size

### Results

- Month 1 retention: **23.15%**
- Month 3 retention: **24.51%**
- Month 6 retention: **21.78%**
- Month 12 retention: **22.34%**

### Takeaway

Only around one-fifth to one-quarter of customers return in these later cohort months. Retention is therefore a meaningful growth lever.

Do not interpret small non-monotonic differences such as month 3 > month 1 as a universal behavioral law; different cohorts, seasonality, and irregular purchase cadence affect the aggregate retention profile.

## 6. Why a second dataset for experimentation?

Online Retail II has no randomized treatment assignment. Comparing groups inside it cannot establish causality.

Criteo Uplift contains randomized incrementality-test data, so it is appropriate for treatment-effect estimation.

### Full experiment data

- Rows: **13,979,592**
- Treatment share: **85.00%**
- Control: **2,096,937**
- Treatment: **11,882,655**

## 7. Experiment QA — sample-ratio mismatch

Before analyzing lift, check whether observed assignment matches intended allocation.

Observed 85/15 allocation produced:

- SRM p-value: **0.9989**

This provides no evidence of a sample-ratio mismatch.

### Interview takeaway

> I checked experiment integrity before estimating treatment effects because broken randomization or logging can invalidate downstream inference.

## 8. Visit treatment effect

Control visit rate: **3.82%**

Treatment visit rate: **4.85%**

Absolute lift:

`4.85% - 3.82% = 1.03 percentage points`

95% CI: approximately **+1.006 to +1.063 pp**

Relative lift: approximately **27.1%**

### Interpretation

The treatment clearly increased visits, both statistically and practically relative to the baseline rate.

## 9. Conversion treatment effect

Control conversion: **0.194%**

Treatment conversion: **0.309%**

Absolute lift: **+0.115 percentage points**

95% CI: approximately **+0.108 to +0.122 pp**

Relative lift: approximately **59.4%**

### Why both absolute and relative lift matter

A 59% relative lift sounds huge, but the absolute increase is only around 0.115 percentage points because baseline conversion is very low.

That distinction is important for product decisions.

## 10. Statistical significance vs business significance

With almost 14 million observations, even small effects can become extremely statistically significant.

Therefore the decision should not be:

> p-value < 0.05, therefore launch.

It should consider:
- absolute lift
- revenue/value per conversion
- cost of treatment
- guardrails
- operational impact
- uncertainty

## 11. Power analysis

At the observed baseline conversion rate, detecting a **10% relative lift** with 80% power requires approximately:

**848,466 users per arm**

### Takeaway

Rare outcomes require large samples. This explains why conversion experiments often run longer than engagement experiments.

## 12. Regression adjustment

A deterministic 1M-row sample was used for regression-adjusted treatment-effect estimation.

Adjusted conversion ATE: approximately **+0.0765 percentage points**.

Purpose:
- improve precision
- account for pre-treatment predictive covariates
- preserve causal interpretation under randomized treatment

## 13. Heterogeneous treatment effects

Exploratory analysis by `f0` quartile found the largest conversion lift in Q2:

**+0.386 percentage points**

This is exploratory, not a production targeting rule.

### Correct interpretation

> The segment is a hypothesis for follow-up validation, not proof that we should immediately target Q2 users.

Why? Segment searches create multiple-testing and overfitting risks.

## 14. Final business synthesis

Main conclusions:

1. Customer revenue is concentrated, so lifecycle strategy should prioritize high-value repeat customers.
2. Cohort retention is modest, making retention a meaningful product opportunity.
3. The randomized treatment improves both visits and conversions.
4. Conversion effects are statistically precise but should be evaluated in absolute business-value terms.
5. Heterogeneous effects suggest possible targeting opportunities that require confirmatory experiments.

## 15. 60-second interview version

> I built a product analytics and experimentation platform using two real datasets because observational product health and causal experimentation answer different questions. On 1.07 million retail transaction lines, I cleaned cancellations and invalid sales, built order/customer metrics and cohort retention, and found that the top 10% of customers generated about 64% of revenue while month-6 retention was about 22%. For causal measurement, I analyzed 13.98 million randomized Criteo observations. I first checked sample-ratio integrity, then estimated visit and conversion lifts with confidence intervals and power analysis. Conversion increased from 0.194% to 0.309%, a 0.115 percentage-point lift. I also explored regression adjustment and treatment heterogeneity. The main lesson was to separate statistical significance from product significance and translate effects into business decisions rather than stopping at p-values.

## 16. Questions you should be ready for

- Why use two datasets?
- Why not infer causality from Online Retail II?
- How did you define completed sales?
- Why is cancellation rate a guardrail?
- Why cohort retention instead of monthly active customers?
- What is sample-ratio mismatch?
- Absolute vs relative lift?
- Why do rare outcomes require more samples?
- Why can a huge relative lift still have small business impact?
- Why should exploratory heterogeneous effects be re-tested?
