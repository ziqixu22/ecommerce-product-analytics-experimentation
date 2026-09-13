# Interview Guide — E-commerce Product Analytics & Experimentation

## 60-second walkthrough
I used two complementary public datasets because they answer different questions. UCI Online Retail II supports descriptive product analytics—revenue, cancellations, concentration, cohorts, and retention—while Criteo Uplift has randomized treatment assignment and supports causal measurement. I kept the analyses separate so observational patterns were never presented as treatment effects. The pipeline runs on the full public sources, persists results, and adds experiment QA, lift, confidence intervals, power, and an exploratory heterogeneity analysis.

## Know these ideas
- **Descriptive vs causal:** cohorts explain behavior; randomization identifies treatment impact.
- **Sample-ratio mismatch:** test whether observed treatment allocation materially departs from the intended split.
- **Absolute lift:** treatment conversion minus control conversion; usually easier to evaluate economically than relative lift alone.
- **Power:** the probability of detecting a pre-specified meaningful effect when it truly exists.
- **Heterogeneity:** a post-hoc segment result is a hypothesis for validation, not a production targeting rule.

## Likely questions
**Why did you not infer causal effects from the retail data?**  
It has no treatment assignment. Differences across customers or countries can be confounded by many unobserved factors.

**What would you do before rollout?**  
Pre-specify primary and guardrail metrics, validate allocation and data quality, estimate effect size with uncertainty, translate lift into economics, and run a confirmatory test for any exploratory segment.

## Reproduce and learn
1. Read `RESULTS.md`; explain every reported metric in plain English.
2. Run `PYTHONPATH=src pytest -q`.
3. Trace `scripts/full_analysis.py` from source data to persisted JSON.
4. Recreate one proportion confidence interval and one power calculation by hand.
5. Give the walkthrough aloud without reading this page.

## Honest boundary
The two sources are separate workstreams. The project does not claim that the Criteo intervention caused the UCI retail outcomes.