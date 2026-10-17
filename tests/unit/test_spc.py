import numpy as np
import pandas as pd
import pytest

from app.models import SpecLimits
from app.spc import analyze, capability, detect_change_point, western_electric


def frame(values, start="2026-01-01 00:00", lots=None):
    t = pd.date_range(start, periods=len(values), freq="30min")
    return pd.DataFrame({"_ts": t, "_v": np.asarray(values, dtype=float),
                         "_lot": lots if lots is not None else ["L1"] * len(values)})


def test_rule1_point_beyond_3_sigma():
    z = np.zeros(20)
    z[10] = 4.0
    assert western_electric(z)[1][10]


def test_rule2_two_of_three_beyond_2_sigma():
    z = np.array([0.1, -0.2, 2.5, 0.3, 2.4, -0.1])
    assert western_electric(z)[2][4]


def test_rule3_four_of_five_beyond_1_sigma():
    z = np.array([0.0, 1.2, 1.3, 0.2, 1.5, 1.1])
    assert western_electric(z)[3][5]


def test_rule4_eight_on_one_side():
    z = np.array([-0.5] + [0.3] * 8)
    flags = western_electric(z)[4]
    assert flags[8] and not flags[7]


def test_centred_noise_has_no_rule1_violations():
    rng = np.random.default_rng(1)
    z = rng.normal(0, 0.5, 300)
    assert western_electric(z)[1].sum() == 0


def test_capability_matches_hand_computation():
    v = np.array([10.0, 10.2, 10.0, 10.2, 10.0, 10.2])  # MR-bar 0.2 -> sigma 0.2/1.128
    cap = capability(v, SpecLimits(lsl=9.0, usl=11.0), "w")
    sigma = 0.2 / 1.128
    assert cap.cp == pytest.approx(2.0 / (6 * sigma), abs=1e-3)
    assert cap.cpk == pytest.approx((11.0 - 10.1) / (3 * sigma), abs=1e-3)


def test_change_point_found_at_injected_step():
    rng = np.random.default_rng(7)
    v = np.concatenate([rng.normal(10, 0.1, 120), rng.normal(10.5, 0.1, 80)])
    res = detect_change_point(v, sigma_ref=0.1)
    assert res["detected"] and abs(res["index"] - 120) <= 1


def test_no_change_point_on_stationary_data():
    rng = np.random.default_rng(3)
    v = rng.normal(10, 0.1, 200)
    assert not detect_change_point(v, sigma_ref=0.1)["detected"]


def test_containment_covers_all_out_of_spec_and_starts_before_shift():
    rng = np.random.default_rng(11)
    v = np.concatenate([rng.normal(10, 0.05, 100), rng.normal(10.4, 0.05, 60)])
    lots = [f"L{i // 16}" for i in range(len(v))]
    res = analyze(frame(v, lots=lots), SpecLimits(lsl=9.7, usl=10.3))
    assert res.change_point.detected
    assert res.out_of_spec.count > 0
    assert res.containment.start <= res.out_of_spec.first
    assert res.containment.start < res.change_point.timestamp
    assert set(res.out_of_spec.lots).issubset(set(res.containment.lots))
    assert res.containment.n_out_of_spec == res.out_of_spec.count


def test_insufficient_baseline_warns_and_skips_limits():
    res = analyze(frame([1.0, 1.1, 1.0, 1.2, 1.1]), SpecLimits(lsl=0.5, usl=1.5))
    assert res.limits is None
    assert any("Insufficient data" in w for w in res.warnings)


def test_missing_spec_limits_warns():
    rng = np.random.default_rng(5)
    res = analyze(frame(rng.normal(5, 0.1, 60)), SpecLimits())
    assert any("No specification limits" in w for w in res.warnings)


def test_analysis_is_deterministic():
    rng = np.random.default_rng(9)
    v = np.concatenate([rng.normal(10, 0.1, 90), rng.normal(10.6, 0.1, 50)])
    a = analyze(frame(v), SpecLimits(lsl=9.5, usl=10.5)).model_dump()
    b = analyze(frame(v), SpecLimits(lsl=9.5, usl=10.5)).model_dump()
    assert a == b
