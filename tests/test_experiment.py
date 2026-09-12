import pandas as pd
from product_ds.experiment import binary_effect, minimum_sample_size_per_arm, sample_ratio_mismatch


def test_binary_effect_direction():
    y = pd.Series([0]*90 + [1]*10 + [0]*80 + [1]*20)
    t = pd.Series([0]*100 + [1]*100)
    r = binary_effect(y, t)
    assert r.treatment_rate > r.control_rate
    assert r.absolute_lift > 0


def test_power_positive():
    assert minimum_sample_size_per_arm(0.10, 0.11) > 0


def test_srm_balanced():
    t = pd.Series([0, 1] * 500)
    _, p = sample_ratio_mismatch(t, 0.5)
    assert p > 0.05
