from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.stats import norm, chisquare
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


@dataclass(frozen=True)
class BinaryEffect:
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift: float
    z_stat: float
    p_value: float
    ci_low: float
    ci_high: float


def sample_ratio_mismatch(treatment: pd.Series, expected_treatment_share: float = 0.5) -> tuple[float, float]:
    t = treatment.dropna().astype(int)
    counts = t.value_counts().reindex([0, 1], fill_value=0).to_numpy()
    n = counts.sum()
    expected = np.array([(1 - expected_treatment_share) * n, expected_treatment_share * n])
    stat, p = chisquare(counts, f_exp=expected)
    return float(stat), float(p)


def binary_effect(outcome: pd.Series, treatment: pd.Series, alpha: float = 0.05) -> BinaryEffect:
    df = pd.DataFrame({"y": outcome, "t": treatment}).dropna()
    c = df.loc[df.t == 0, "y"].astype(float)
    tr = df.loc[df.t == 1, "y"].astype(float)
    pc, pt = c.mean(), tr.mean()
    diff = pt - pc
    se = np.sqrt(pc * (1 - pc) / len(c) + pt * (1 - pt) / len(tr))
    z = diff / se if se > 0 else 0.0
    p = 2 * (1 - norm.cdf(abs(z)))
    zcrit = norm.ppf(1 - alpha / 2)
    rel = diff / pc if pc > 0 else np.nan
    return BinaryEffect(float(pc), float(pt), float(diff), float(rel), float(z), float(p),
                        float(diff - zcrit * se), float(diff + zcrit * se))


def minimum_sample_size_per_arm(baseline: float, target: float, alpha: float = 0.05, power: float = 0.80) -> int:
    effect = abs(proportion_effectsize(baseline, target))
    n = NormalIndPower().solve_power(effect_size=effect, alpha=alpha, power=power, ratio=1.0)
    return int(np.ceil(n))


def regression_adjusted_ate(df: pd.DataFrame, outcome: str, treatment: str, covariates: list[str]) -> float:
    from sklearn.linear_model import Ridge
    X = df[covariates].astype(float)
    y = df[outcome].astype(float)
    t = df[treatment].astype(int)
    m0 = Ridge(alpha=1.0).fit(X[t == 0], y[t == 0])
    m1 = Ridge(alpha=1.0).fit(X[t == 1], y[t == 1])
    return float(np.mean(m1.predict(X) - m0.predict(X)))


def heterogeneous_effects(df: pd.DataFrame, outcome: str, treatment: str, segment: str) -> pd.DataFrame:
    rows = []
    for value, g in df.groupby(segment, dropna=False):
        if g[treatment].nunique() < 2:
            continue
        e = binary_effect(g[outcome], g[treatment])
        rows.append({"segment": value, "n": len(g), **e.__dict__})
    return pd.DataFrame(rows).sort_values("n", ascending=False)
