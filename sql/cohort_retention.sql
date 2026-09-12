-- Customer cohort retention from cleaned Online Retail II transactions.
WITH valid_tx AS (
  SELECT *
  FROM transactions
  WHERE NOT is_cancelled
    AND Quantity > 0
    AND Price > 0
    AND "Customer ID" IS NOT NULL
), first_seen AS (
  SELECT
    "Customer ID" AS customer_id,
    date_trunc('month', min(InvoiceDate)) AS cohort_month
  FROM valid_tx
  GROUP BY 1
), activity AS (
  SELECT DISTINCT
    "Customer ID" AS customer_id,
    date_trunc('month', InvoiceDate) AS activity_month
  FROM valid_tx
), indexed AS (
  SELECT
    a.customer_id,
    f.cohort_month,
    a.activity_month,
    date_diff('month', f.cohort_month, a.activity_month) AS month_index
  FROM activity a
  JOIN first_seen f USING(customer_id)
), cohort_counts AS (
  SELECT
    cohort_month,
    month_index,
    count(DISTINCT customer_id) AS active_customers
  FROM indexed
  GROUP BY 1,2
), sizes AS (
  SELECT cohort_month, active_customers AS cohort_size
  FROM cohort_counts
  WHERE month_index = 0
)
SELECT
  c.cohort_month,
  c.month_index,
  c.active_customers,
  s.cohort_size,
  c.active_customers::DOUBLE / s.cohort_size AS retention_rate
FROM cohort_counts c
JOIN sizes s USING(cohort_month)
ORDER BY cohort_month, month_index;
