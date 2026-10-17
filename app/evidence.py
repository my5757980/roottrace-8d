"""Evidence registry: every fact the AI may use gets a stable ID it must cite.

S* computed SPC facts · P* machine-parameter facts · L* log entries · C* complaint facts ·
I* image observations · S0 standard capability targets.
"""

from __future__ import annotations

import math

from app.models import (
    ComplaintFacts,
    CorrelatedEvent,
    DefectFinding,
    EvidenceItem,
    MaintenanceEvent,
    ParameterShift,
    SpecLimits,
    SPCResult,
)


def ts(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt is not None else "n/a"


def value_decimals(sigma: float | None) -> int:
    if not sigma or sigma <= 0 or not math.isfinite(sigma):
        return 4
    return int(min(6, max(1, -math.floor(math.log10(sigma)) + 1)))


_UNIT_SUFFIX = {"_c": " (°C)", "_pct": " (%)", "_mm": " (mm)", "_count": " (count)", "_bar": " (bar)", "_rpm": " (rpm)"}


def _pretty(name: str) -> str:
    for suffix, unit in _UNIT_SUFFIX.items():
        if name.endswith(suffix):
            return name[: -len(suffix)].replace("_", " ") + unit
    return name.replace("_", " ")


def build_process_evidence(spc: SPCResult, shifts: list[ParameterShift], correlated: list[CorrelatedEvent],
                           events: list[MaintenanceEvent], spec: SpecLimits) -> list[EvidenceItem]:
    unit = spec.unit
    d = value_decimals(spc.limits.sigma if spc.limits else None)

    def f(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.{d}f}"

    items: list[EvidenceItem] = [EvidenceItem(
        id="S0", kind="standard",
        text="Capability targets: Cpk ≥ 1.33 for ongoing production; Cpk ≥ 1.67 for initial process approval.")]
    n = 1

    def add(text: str) -> None:
        nonlocal n
        items.append(EvidenceItem(id=f"S{n}", kind="spc", text=text))
        n += 1

    lim = [f"LSL {f(spec.lsl)}" if spec.lsl is not None else "", f"USL {f(spec.usl)}" if spec.usl is not None else ""]
    target = f" (target {f(spec.target)})" if spec.target is not None else ""
    add(f"Specification for {spec.characteristic}: {' / '.join(x for x in lim if x) or 'not given'} {unit}{target}.")
    if spc.baseline and spc.limits:
        b, L = spc.baseline, spc.limits
        add(f"Baseline window {ts(b.start)} to {ts(b.end)} ({b.n} samples): mean {f(b.mean)} {unit}, "
            f"σ̂ {f(b.sigma)} {unit}; control limits LCL {f(L.lcl)} / UCL {f(L.ucl)} {unit}.")
    base_cap = next((c for c in spc.capability if c.label == "baseline"), None)
    if base_cap and base_cap.cpk is not None:
        cp = f"Cp {base_cap.cp:.2f}, " if base_cap.cp is not None else ""
        add(f"Baseline capability: {cp}Cpk {base_cap.cpk:.2f}.")
    cpt = spc.change_point
    if cpt.detected:
        add(f"Process shift detected at {ts(cpt.timestamp)} (first shifted sample; last known-good sample "
            f"{ts(cpt.last_good_timestamp)}): mean {f(cpt.mean_before)} → {f(cpt.mean_after)} {unit} "
            f"(Δ {cpt.delta:+.{d}f} {unit}, Welch t = {cpt.t_stat:.1f}).")
    else:
        add("No statistically significant process shift detected in the data.")
    after_cap = next((c for c in spc.capability if c.label != "baseline"), None)
    if after_cap and after_cap.cpk is not None:
        add(f"Capability {after_cap.label} ({after_cap.n} samples): mean {f(after_cap.mean)} {unit}, "
            f"Cpk {after_cap.cpk:.2f}.")
    rc = spc.rule_counts
    if spc.violations:
        if cpt.detected:
            before = [x for x in spc.violations if x.index < cpt.index]
            after = [x for x in spc.violations if x.index >= cpt.index]
            first = after[0] if after else spc.violations[0]
            add(f"Western Electric run-rule violations: {len(after)} points from the shift onward "
                f"(rule 1: {sum(1 for x in after if x.rule == 1)}, rule 2: {sum(1 for x in after if x.rule == 2)}, "
                f"rule 3: {sum(1 for x in after if x.rule == 3)}, rule 4: {sum(1 for x in after if x.rule == 4)}) "
                f"versus {len(before)} isolated points before it; first violation after the shift at "
                f"{ts(first.timestamp)} ({first.explanation}).")
        else:
            first = spc.violations[0]
            add(f"Western Electric run-rule violations on {len(spc.violations)} points (rule 1: {rc['1']}, "
                f"rule 2: {rc['2']}, rule 3: {rc['3']}, rule 4: {rc['4']}); first at {ts(first.timestamp)}.")
    elif spc.limits:
        add("No Western Electric rule violations.")
    o = spc.out_of_spec
    if o.count:
        add(f"{o.count} of {spc.n_points} samples out of specification between {ts(o.first)} and {ts(o.last)} "
            f"(max {f(o.max_value)} {unit}); lots with out-of-specification samples: {', '.join(o.lots)}.")
    else:
        add(f"No samples out of specification ({spc.n_points} samples).")
    c = spc.containment
    if c.start is not None:
        add(f"Containment range (computed): {ts(c.start)} to {ts(c.end)}, {c.n_samples} samples "
            f"({c.n_out_of_spec} out of specification); suspect lots: {', '.join(c.lots)}.")

    for i, s in enumerate(shifts, start=1):
        name = _pretty(s.name)
        if s.detected and s.change_time is not None:
            rel = f", {s.hours_from_cp:+.1f} h from the measurement shift" if s.hours_from_cp is not None else ""
            text = (f"{name}: shift at {ts(s.change_time)} (mean {s.mean_before:.2f} → {s.mean_after:.2f}, "
                    f"Δ {s.delta:+.2f}){rel}.")
        elif s.mean_before_cp is not None:
            text = (f"{name}: no significant shift; mean {s.mean_before_cp:.2f} before vs "
                    f"{s.mean_after_cp:.2f} after the measurement shift.")
        else:
            text = f"{name}: no significant shift."
        items.append(EvidenceItem(id=f"P{i}", kind="parameter", text=text))

    corr = {c.event_id: c for c in correlated}
    for ev in events:
        who = ", ".join(x for x in (ev.type, f"shift {ev.shift}" if ev.shift else "", ev.author) if x)
        text = f"{ts(ev.timestamp)} [{who}] {ev.description}"
        if ev.id in corr:
            text += f" ({corr[ev.id].delta_minutes:+.0f} min from the detected shift)"
        items.append(EvidenceItem(id=ev.id, kind="log", text=text))
    return items


def complaint_evidence(facts: ComplaintFacts) -> list[EvidenceItem]:
    out = []
    k = 1
    for fact in facts.facts:
        if not fact.value or fact.value.strip().lower() == "not stated":
            continue
        quote = f' (quote: "{fact.quote.strip()}")' if fact.quote.strip() else ""
        out.append(EvidenceItem(id=f"C{k}", kind="complaint", text=f"{fact.name.replace('_', ' ')}: {fact.value}{quote}"))
        k += 1
    return out


def image_evidence(findings: list[DefectFinding]) -> list[EvidenceItem]:
    out = []
    for k, fd in enumerate(findings, start=1):
        obs = "; ".join(fd.observations[:6])
        out.append(EvidenceItem(
            id=f"I{k}", kind="image",
            text=f"Photo {fd.image_index + 1}: {fd.defect_class.replace('_', ' ')} ({fd.confidence} confidence). "
                 f"{fd.description}{' Observations: ' + obs + '.' if obs else ''}"))
    return out


def format_evidence_block(items: list[EvidenceItem]) -> str:
    return "\n".join(f"[{it.id}] {it.text}" for it in items)


def valid_ids(items: list[EvidenceItem]) -> set[str]:
    return {it.id for it in items}
