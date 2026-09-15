from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from .experiment import binary_effect, regression_adjusted_ate, sample_ratio_mismatch, heterogeneous_effects


CRITEO_EXPECTED_TREATMENT_SHARE = 0.85


def load_criteo(path: Path, sample: int | None = None) -> pd.DataFrame:
    usecols = [f"f{i}" for i in range(12)] + ["treatment", "conversion", "visit"]
    df = pd.read_csv(path, usecols=usecols)
    if sample and len(df) > sample:
        df = df.sample(sample, random_state=42)
    return df


def summarize(
    df: pd.DataFrame,
    expected_treatment_share: float = CRITEO_EXPECTED_TREATMENT_SHARE,
) -> dict:
    if not 0 < expected_treatment_share < 1:
        raise ValueError("expected_treatment_share must be between 0 and 1")

    observed_treatment_share = float(df["treatment"].mean())
    # SRM must compare the observed allocation with the experiment's DESIGN allocation.
    # Do not use the observed treatment share itself as the expected share; doing so makes
    # the goodness-of-fit check tautological and unable to detect allocation/logging issues.
    srm_stat, srm_p = sample_ratio_mismatch(
        df["treatment"],
        expected_treatment_share=expected_treatment_share,
    )
    visit = binary_effect(df["visit"], df["treatment"])
    conv = binary_effect(df["conversion"], df["treatment"])
    covariates = [f"f{i}" for i in range(12)]
    adjusted = regression_adjusted_ate(df, "conversion", "treatment", covariates)

    # f0 quartiles are used only as an illustrative HTE slice. In a company setting,
    # segments should be chosen from product hypotheses, not after looking for significance.
    work = df.copy()
    work["f0_quartile"] = pd.qcut(work["f0"], 4, duplicates="drop")
    hte = heterogeneous_effects(work, "conversion", "treatment", "f0_quartile")
    return {
        "rows": len(df),
        "observed_treatment_share": observed_treatment_share,
        "expected_treatment_share": expected_treatment_share,
        "srm_stat": srm_stat,
        "srm_p": srm_p,
        "visit_effect": visit.__dict__,
        "conversion_effect": conv.__dict__,
        "regression_adjusted_conversion_ate": adjusted,
        "hte_f0_quartiles": hte.astype({"segment": str}).to_dict(orient="records") if not hte.empty else [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--sample", type=int, default=1_000_000)
    ap.add_argument(
        "--expected-treatment-share",
        type=float,
        default=CRITEO_EXPECTED_TREATMENT_SHARE,
        help="Treatment allocation specified by the experiment design; Criteo uses 0.85.",
    )
    ap.add_argument("--output", type=Path, default=Path("results/experiment_summary.json"))
    args = ap.parse_args()
    result = summarize(
        load_criteo(args.input, args.sample),
        expected_treatment_share=args.expected_treatment_share,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
