# Architecture decisions

## Separate observational analytics from causal experiments
Online Retail II supports descriptive and diagnostic product analytics. It does not identify causal effects because treatment is not randomized. Criteo Uplift contains randomized treatment assignment, so causal measurement lives in a separate analysis path.

## Why DuckDB / SQL-style marts
The goal is to model how a Product DS works with a warehouse: raw transactions are validated, cleaned, and transformed into business-facing metrics. DuckDB keeps the project reproducible on a laptop while preserving SQL-first analytical thinking.

## Why cohort retention
Raw monthly active-customer counts mix acquisition and retention. Cohort analysis fixes the denominator at acquisition/first-order time and measures how the same customers return over subsequent months.

## Why SRM before lift
If observed treatment allocation materially differs from the experiment design, lift estimates may be untrustworthy. Assignment/instrumentation checks come before outcome interpretation.

## Why absolute and relative lift
Relative lift is easy to communicate but can exaggerate small baseline changes. Absolute lift shows the actual percentage-point change and is usually closer to capacity/revenue planning.

## Why regression adjustment
Pre-treatment covariates can reduce unexplained variance and increase precision when they are predictive of the outcome. Post-treatment variables must not be used as if they were baseline covariates.

## Production extension
In a real company, the next steps would include metric ownership, event-schema tests, dbt models in a cloud warehouse, automated experiment dashboards, and a launch-review process with primary and guardrail metrics.