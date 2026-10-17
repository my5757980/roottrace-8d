"""Deterministic statistical process control (no AI computes these numbers).

Individuals (I-MR) chart: CL = baseline mean, sigma = MR-bar / 1.128, limits CL ± 3 sigma.
Western Electric rules 1-4, Cp/Cpk per window, a single mean-shift change point (global
least-squares split refined locally, confirmed by Welch t), the out-of-spec summary and the
containment range from the last known-good sample.
"""

from __future__ import annotations

import math
from datetime import datetime

import numpy as np
import pandas as pd

from app.models import (
    Baseline,
    CapabilityWindow,
    ChangePoint,
    Containment,
    Limits,
    OutOfSpec,
    ParameterShift,
    Series,
    SpecLimits,
    SPCResult,
    Violation,
)

D2 = 1.128  # bias constant for moving ranges of size 2
MIN_BASELINE = 20
MIN_SEGMENT = 10
T_THRESHOLD = 5.0
MAX_SERIES_POINTS = 3000

RULE_TEXT = {
    1: "Rule 1: one point beyond the 3σ control limit",
    2: "Rule 2: 2 of 3 consecutive points beyond 2σ on the same side",
    3: "Rule 3: 4 of 5 consecutive points beyond 1σ on the same side",
    4: "Rule 4: 8 consecutive points on the same side of the centre line",
}


def _dt(x) -> datetime:
    return pd.Timestamp(x).to_pydatetime()


def mr_sigma(values: np.ndarray) -> tuple[float, float]:
    """Return (sigma_hat, mr_bar) from the average moving range of consecutive points."""
    if len(values) < 2:
        return 0.0, 0.0
    mr_bar = float(np.mean(np.abs(np.diff(values))))
    return mr_bar / D2, mr_bar


def western_electric(z: np.ndarray) -> dict[int, np.ndarray]:
    """Boolean flags per rule for standardized values z = (x - CL) / sigma."""
    n = len(z)
    flags = {k: np.zeros(n, dtype=bool) for k in (1, 2, 3, 4)}
    flags[1] = np.abs(z) > 3
    for i in range(n):
        if i >= 2:
            w = z[i - 2:i + 1]
            if (z[i] > 2 and (w > 2).sum() >= 2) or (z[i] < -2 and (w < -2).sum() >= 2):
                flags[2][i] = True
        if i >= 4:
            w = z[i - 4:i + 1]
            if (z[i] > 1 and (w > 1).sum() >= 4) or (z[i] < -1 and (w < -1).sum() >= 4):
                flags[3][i] = True
    run, side = 0, 0
    for i in range(n):
        s = 1 if z[i] > 0 else (-1 if z[i] < 0 else 0)
        if s != 0 and s == side:
            run += 1
        else:
            run, side = (1, s) if s != 0 else (0, 0)
        if run >= 8:
            flags[4][i] = True
    return flags


def capability(values: np.ndarray, spec: SpecLimits, label: str) -> CapabilityWindow | None:
    if len(values) < 2:
        return None
    mu = float(np.mean(values))
    sigma, _ = mr_sigma(values)
    cp = cpk = None
    if sigma > 0:
        if spec.lsl is not None and spec.usl is not None:
            cp = (spec.usl - spec.lsl) / (6 * sigma)
        sides = []
        if spec.usl is not None:
            sides.append((spec.usl - mu) / (3 * sigma))
        if spec.lsl is not None:
            sides.append((mu - spec.lsl) / (3 * sigma))
        cpk = min(sides) if sides else None
    return CapabilityWindow(label=label, n=int(len(values)), mean=mu, sigma=sigma,
                            cp=None if cp is None else round(cp, 4), cpk=None if cpk is None else round(cpk, 4))


def _ls_scores(v: np.ndarray, lo: int, hi: int) -> np.ndarray:
    """Least-squares mean-shift score k(n-k)/n (mean1-mean2)^2 for splits k in [lo, hi)."""
    n = len(v)
    cs = np.cumsum(v)
    total = cs[-1]
    ks = np.arange(lo, hi)
    m1 = cs[ks - 1] / ks
    m2 = (total - cs[ks - 1]) / (n - ks)
    return ks * (n - ks) / n * (m1 - m2) ** 2


def detect_change_point(v: np.ndarray, sigma_ref: float | None = None, min_seg: int = MIN_SEGMENT) -> dict:
    """Single most significant mean shift. Returns index of first shifted point (or None)."""
    n = len(v)
    if n < 2 * min_seg:
        return {"detected": False, "index": None, "reason": "too few points"}
    scores = _ls_scores(v, min_seg, n - min_seg + 1)
    k1 = int(np.argmax(scores)) + min_seg
    # local refinement: a short window around the global split isolates the onset of a step
    w = 20
    lo, hi = max(min_seg, k1 - w), min(n - min_seg, k1 + w)
    best_k, best_s = k1, -1.0
    for k in range(lo, hi + 1):
        a, b = v[max(0, k - w):k], v[k:min(n, k + w)]
        if len(a) < 3 or len(b) < 3:
            continue
        s = len(a) * len(b) / (len(a) + len(b)) * (a.mean() - b.mean()) ** 2
        if s > best_s:
            best_k, best_s = k, s
    k = best_k
    a, b = v[:k], v[k:]
    va, vb = a.var(ddof=1), b.var(ddof=1)
    denom = math.sqrt(va / len(a) + vb / len(b)) if (va + vb) > 0 else 0.0
    delta = float(b.mean() - a.mean())
    t = delta / denom if denom > 0 else (math.inf if delta else 0.0)
    ref = sigma_ref if sigma_ref and sigma_ref > 0 else mr_sigma(a)[0]
    detected = abs(t) > T_THRESHOLD and (ref == 0 or abs(delta) >= ref)
    return {"detected": bool(detected), "index": k, "mean_before": float(a.mean()), "mean_after": float(b.mean()),
            "delta": delta, "t": float(t)}


def _fmt(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}"


def analyze(df: pd.DataFrame, spec: SpecLimits, baseline_end: datetime | None = None) -> SPCResult:
    t = df["_ts"].to_numpy()
    v = df["_v"].to_numpy(dtype=float)
    lots = df["_lot"].astype(str).to_numpy()
    n = len(v)
    warnings: list[str] = []
    explanations: dict[str, str] = {}
    unit = spec.unit

    # ---- baseline window
    if baseline_end is not None:
        nb = int(np.searchsorted(t, np.datetime64(baseline_end), side="right"))
    else:
        nb = int(min(200, max(MIN_BASELINE, round(0.25 * n))))
    nb = min(nb, n)
    baseline = limits = None
    sigma = 0.0
    if nb >= MIN_BASELINE:
        vb = v[:nb]
        sigma, mr_bar = mr_sigma(vb)
        cl = float(vb.mean())
        baseline = Baseline(start=_dt(t[0]), end=_dt(t[nb - 1]), n=nb, mean=cl, sigma=sigma, mr_bar=mr_bar)
        if sigma > 0:
            limits = Limits(cl=cl, ucl=cl + 3 * sigma, lcl=cl - 3 * sigma, sigma=sigma,
                            zones={"pos1": cl + sigma, "pos2": cl + 2 * sigma, "neg1": cl - sigma, "neg2": cl - 2 * sigma})
            explanations["cl"] = f"Centre line = mean of the {nb} baseline samples ({_dt(t[0]):%Y-%m-%d %H:%M} to {_dt(t[nb - 1]):%Y-%m-%d %H:%M})."
            explanations["sigma"] = "σ̂ = average moving range / 1.128 (individuals I-MR chart, short-term variation)."
            explanations["limits"] = "Control limits = centre line ± 3σ̂: where the process can go on its own when stable."
        else:
            warnings.append("Baseline has zero variation; control limits not computed.")
    else:
        warnings.append(f"Insufficient data for control limits: {nb} baseline points (minimum {MIN_BASELINE}).")

    # ---- run rules
    violations: list[Violation] = []
    rule_counts = {str(k): 0 for k in (1, 2, 3, 4)}
    point_rule = np.zeros(n, dtype=int)
    if limits is not None:
        z = (v - limits.cl) / limits.sigma
        flags = western_electric(z)
        for k in (4, 3, 2, 1):  # lowest rule number wins per point
            point_rule[flags[k]] = k
        rule_counts = {str(k): int((point_rule == k).sum()) for k in (1, 2, 3, 4)}
        for i in np.nonzero(point_rule)[0]:
            violations.append(Violation(rule=int(point_rule[i]), index=int(i), timestamp=_dt(t[i]),
                                        value=float(v[i]), explanation=RULE_TEXT[int(point_rule[i])]))
        explanations["rules"] = "Western Electric run rules 1–4 checked against the baseline centre line and σ̂."

    # ---- change point
    cp_raw = detect_change_point(v, sigma_ref=sigma if sigma > 0 else None)
    if cp_raw.get("detected"):
        k = cp_raw["index"]
        change = ChangePoint(
            detected=True, index=k, timestamp=_dt(t[k]), last_good_timestamp=_dt(t[k - 1]) if k > 0 else None,
            mean_before=cp_raw["mean_before"], mean_after=cp_raw["mean_after"], delta=cp_raw["delta"],
            t_stat=cp_raw["t"],
            explanation=("Most significant single mean shift (least-squares split refined on a ±20-point window), "
                         f"confirmed by Welch t = {cp_raw['t']:.1f} (threshold {T_THRESHOLD:.0f}) and |Δ| ≥ 1σ̂."),
        )
    else:
        change = ChangePoint(detected=False, explanation="No statistically significant mean shift detected "
                                                         f"(Welch t threshold {T_THRESHOLD:.0f} and |Δ| ≥ 1σ̂).")

    # ---- capability
    windows = []
    cap_base = capability(v[:nb], spec, "baseline") if nb >= 2 else None
    if cap_base:
        windows.append(cap_base)
    after_start = change.index if change.detected else nb
    if after_start is not None and n - after_start >= 2:
        cap_after = capability(v[after_start:], spec, "after shift" if change.detected else "after baseline")
        if cap_after:
            windows.append(cap_after)
    if spec.lsl is None and spec.usl is None:
        warnings.append("No specification limits given; capability indices not computed.")
    else:
        explanations["capability"] = ("Cp = (USL − LSL) / 6σ̂ and Cpk = min(USL − μ, μ − LSL) / 3σ̂, "
                                      "with σ̂ from the moving range of each window.")

    # ---- out of spec
    oos_mask = np.zeros(n, dtype=bool)
    if spec.usl is not None:
        oos_mask |= v > spec.usl
    if spec.lsl is not None:
        oos_mask |= v < spec.lsl
    idx = np.nonzero(oos_mask)[0]
    if len(idx):
        oos_lots = list(dict.fromkeys(lots[idx].tolist()))
        oos = OutOfSpec(count=int(len(idx)), first=_dt(t[idx[0]]), last=_dt(t[idx[-1]]), lots=oos_lots,
                        max_value=float(v[idx].max()), min_value=float(v[idx].min()))
    else:
        oos = OutOfSpec(count=0)
    explanations["out_of_spec"] = "Samples outside the specification limits (LSL/USL), counted directly from the data."

    # ---- containment (deterministic)
    if change.detected:
        start_i = max(0, change.index - 1)  # last known-good sample before the shift
        if len(idx):
            start_i = min(start_i, int(idx[0]))
        end_i = n - 1
        rng_lots = list(dict.fromkeys(lots[start_i:end_i + 1].tolist()))
        containment = Containment(
            start=_dt(t[start_i]), end=_dt(t[end_i]), lots=rng_lots,
            n_samples=int(end_i - start_i + 1), n_out_of_spec=int(oos_mask[start_i:end_i + 1].sum()),
            rationale=("From the last known-good sample before the detected shift to the last production record: "
                       "every part made in this window is suspect until sorted."),
        )
    elif len(idx):
        start_i, end_i = int(idx[0]), n - 1
        containment = Containment(
            start=_dt(t[start_i]), end=_dt(t[end_i]), lots=list(dict.fromkeys(lots[start_i:end_i + 1].tolist())),
            n_samples=int(end_i - start_i + 1), n_out_of_spec=int(oos_mask[start_i:].sum()),
            rationale="No significant shift detected; range starts at the first out-of-specification sample.",
        )
    else:
        containment = Containment(rationale="No shift and no out-of-specification samples: contain the lots named in the complaint.")

    # ---- series for the chart (downsample very long series, keep flagged points)
    keep = np.arange(n)
    downsampled = False
    if n > MAX_SERIES_POINTS:
        stride = math.ceil(n / MAX_SERIES_POINTS)
        mask = (np.arange(n) % stride == 0) | (point_rule > 0) | oos_mask
        keep = np.nonzero(mask)[0]
        downsampled = True
    series = Series(
        t=[pd.Timestamp(t[i]).strftime("%Y-%m-%dT%H:%M") for i in keep],
        v=[round(float(v[i]), 6) for i in keep],
        lot=[str(lots[i]) for i in keep],
        flags=[int(point_rule[i]) for i in keep],
        downsampled=downsampled,
    )
    _ = unit
    return SPCResult(n_points=n, n_dropped=0, baseline=baseline, limits=limits, violations=violations,
                     rule_counts=rule_counts, capability=windows, change_point=change, out_of_spec=oos,
                     containment=containment, series=series, explanations=explanations, warnings=warnings)


def parameter_shifts(df: pd.DataFrame, params: list[str], cp_time: datetime | None) -> list[ParameterShift]:
    out: list[ParameterShift] = []
    t_all = df["_ts"].to_numpy()
    for name in params:
        col = pd.to_numeric(df[name], errors="coerce")
        mask = col.notna().to_numpy()
        if mask.sum() < 2 * MIN_SEGMENT:
            continue
        p = col.to_numpy(dtype=float)[mask]
        tp = t_all[mask]
        # machine parameters are often autocorrelated (daily cycles): use long segments and the overall
        # spread as reference so cyclic drift is not reported as a shift
        res = detect_change_point(p, sigma_ref=float(np.std(p)), min_seg=max(MIN_SEGMENT, len(p) // 10))
        shift = ParameterShift(name=name, detected=bool(res.get("detected")))
        if res.get("index") is not None and res.get("detected"):
            k = res["index"]
            shift.change_time = _dt(tp[k])
            shift.mean_before, shift.mean_after, shift.delta = res["mean_before"], res["mean_after"], res["delta"]
            if cp_time is not None:
                shift.hours_from_cp = round((_dt(tp[k]) - cp_time).total_seconds() / 3600, 1)
        if cp_time is not None:
            before = p[tp < np.datetime64(cp_time)]
            after = p[tp >= np.datetime64(cp_time)]
            if len(before) and len(after):
                shift.mean_before_cp, shift.mean_after_cp = float(before.mean()), float(after.mean())
        out.append(shift)
    return out
