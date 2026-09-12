# Interview guide

## Product analytics questions you should be able to answer

1. What is the unit of analysis: transaction line, invoice/order, customer, cohort, or experiment assignment?
2. Why exclude cancelled invoices and negative quantities from realized revenue?
3. Why are raw monthly customer counts not the same as retention?
4. How do you define first-purchase cohort and month-N retention?
5. How would duplicate invoices, missing Customer IDs, or malformed dates bias results?
6. Why is revenue concentration useful to a product/business team?

## Experimentation questions

1. What is sample-ratio mismatch and why do you check it before treatment lift?
2. Absolute lift vs relative lift?
3. What determines minimum sample size?
4. Why do confidence intervals matter beyond p-values?
5. When does regression adjustment help?
6. Why should heterogeneous-treatment-effect slices come from hypotheses rather than significance hunting?
7. Why can a statistically significant experiment still be a no-launch decision?

## Strong project narrative

- Start with the product question, not the code.
- Explain the data grain and quality checks.
- Show how warehouse-style metrics answer product-health questions.
- Separate observational findings from randomized causal evidence.
- Explain the decision trade-off and what you would monitor after launch.

## What not to claim

Do not claim causal effects from the Online Retail II data. Do not claim a lift number until the Criteo pipeline is actually run. Do not claim this system was deployed at a real company.