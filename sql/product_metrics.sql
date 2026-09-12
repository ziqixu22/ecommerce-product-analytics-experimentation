-- DuckDB-compatible product analytics over a cleaned `transactions` table.

-- Monthly revenue, customers, orders, and cancellation rate
WITH monthly AS (
  SELECT
    date_trunc('month', InvoiceDate) AS month,
    count(DISTINCT Invoice) AS orders,
    count(DISTINCT "Customer ID") AS customers,
    sum(CASE WHEN NOT is_cancelled AND Quantity > 0 AND Price > 0 THEN revenue ELSE 0 END) AS revenue,
    count(DISTINCT CASE WHEN is_cancelled THEN Invoice END) AS cancelled_orders
  FROM transactions
  GROUP BY 1
)
SELECT
  *,
  cancelled_orders::DOUBLE / NULLIF(orders, 0) AS cancellation_rate,
  revenue / NULLIF(customers, 0) AS revenue_per_customer
FROM monthly
ORDER BY month;

-- Top products by non-cancelled revenue
SELECT
  StockCode,
  any_value(Description) AS Description,
  count(DISTINCT Invoice) AS orders,
  sum(Quantity) AS units,
  sum(revenue) AS revenue
FROM transactions
WHERE NOT is_cancelled AND Quantity > 0 AND Price > 0
GROUP BY 1
ORDER BY revenue DESC
LIMIT 50;

-- Revenue concentration by country
SELECT
  Country,
  count(DISTINCT Invoice) AS orders,
  count(DISTINCT "Customer ID") AS customers,
  sum(revenue) AS revenue
FROM transactions
WHERE NOT is_cancelled AND Quantity > 0 AND Price > 0
GROUP BY 1
ORDER BY revenue DESC;
