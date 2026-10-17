"""Analysis orchestration: deterministic steps, four AI steps on AMD, cached fallback, AI trace."""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app.correlate import correlate_events
from app.evidence import (
    build_process_evidence,
    complaint_evidence,
    format_evidence_block,
    image_evidence,
    ts,
    valid_ids,
)
from app.llm import prompts
from app.llm.client import LLMError
from app.models import (
    Analysis,
    ComplaintFacts,
    DefectFindings,
    Draft8D,
    HypothesesOut,
    StepState,
    TraceEntry,
)
from app.numbers import allowed_values
from app.report import build_report, trace_numbers
from app.spc import analyze, parameter_shifts
from app.store import Case

log = logging.getLogger("roottrace.pipeline")

STEP_DEFS = [
    ("ingest", "Read case inputs", "deterministic"),
    ("spc", "Statistical process control", "deterministic"),
    ("correlate", "Correlate shift with maintenance log", "deterministic"),
    ("complaint_facts", "Extract complaint facts", "ai"),
    ("defect_vision", "Analyze defect photo", "ai"),
    ("hypotheses", "Rank root-cause hypotheses (6M)", "ai"),
    ("draft_8d", "Draft 8D report D1–D8", "ai"),
    ("trace_check", "Verify every number against evidence", "deterministic"),
]
AI_STEPS = [name for name, _, kind in STEP_DEFS if kind == "ai"]
MAX_TOKENS = {"complaint_facts": 1500, "defect_vision": 1200, "hypotheses": 2500, "draft_8d": 5000}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_analysis(mode: str) -> Analysis:
    return Analysis(run_id=secrets.token_hex(6), mode=mode, started_at=_now(),  # type: ignore[arg-type]
                    steps=[StepState(name=n, label=lbl, kind=k) for n, lbl, k in STEP_DEFS])  # type: ignore[arg-type]


def case_context(case: Case) -> str:
    s = case.spec
    m = case.meta
    limits = " / ".join(x for x in (f"LSL {s.lsl}" if s.lsl is not None else "",
                                    f"USL {s.usl}" if s.usl is not None else "") if x)
    ds = case.dataset_summary
    return "\n".join(x for x in (
        f"Case: {case.title}",
        f"Part: {m.get('part_number', '')} {m.get('part_name', '')}".strip(),
        f"Customer: {m['customer']}" if m.get("customer") else "",
        f"Machine: {m['machine']}" if m.get("machine") else "",
        f"Characteristic: {s.characteristic} [{s.unit}], specification {limits or 'not given'}"
        + (f", target {s.target}" if s.target is not None else ""),
        f"Process data: {ds.rows} samples from {ts(ds.start)} to {ts(ds.end)}, {ds.lots} lots",
    ) if x)


def containment_block(case: Case, analysis: Analysis) -> str:
    c = analysis.spc.containment if analysis.spc else None
    if c is None or c.start is None:
        return ("- No computed suspect range (no significant shift or out-of-specification samples): "
                "contain the lots named in the complaint.")
    return "\n".join([
        f"- Suspect time range: {ts(c.start)} to {ts(c.end)} (last known-good sample before the shift to the "
        "last production record)",
        f"- Suspect lots: {', '.join(c.lots)}",
        f"- Samples in range: {c.n_samples} ({c.n_out_of_spec} out of specification)",
    ])


class _Runner:
    def __init__(self, case: Case, analysis: Analysis, llm: Any, cached_run: dict | None):
        self.case, self.a, self.llm, self.cached = case, analysis, llm, cached_run
        self.t0 = time.perf_counter()

    def start(self, name: str) -> StepState:
        st = self.a.step(name)
        st.status, st.started_at = "running", _now()
        return st

    @staticmethod
    def finish(st: StepState, status: str = "done", source: str | None = None, message: str | None = None) -> None:
        st.status, st.finished_at = status, _now()  # type: ignore[assignment]
        if source:
            st.source = source  # type: ignore[assignment]
        if message:
            st.message = message

    def _cached(self, name: str, schema) -> tuple[Any, TraceEntry] | None:
        if not self.cached:
            return None
        rec = (self.cached.get("steps") or {}).get(name)
        if not rec:
            return None
        result = schema.model_validate(rec["result"])
        tr = dict(rec.get("trace") or {})
        tr.update(source="cached", recorded_at=self.cached.get("recorded_at"), status="ok", error=None)
        tr.setdefault("step", name)
        tr.setdefault("provider", self.cached.get("provider", "AMD"))
        tr.setdefault("model", (self.cached.get("models") or {}).get("text", "unknown"))
        tr.setdefault("started_at", self.cached.get("recorded_at") or _now().isoformat())
        tr.setdefault("latency_ms", 0)
        return result, TraceEntry.model_validate(tr)

    async def ai_step(self, name: str, schema, call: Callable[[], Awaitable[tuple[Any, TraceEntry]]]):
        st = self.start(name)
        if self.a.mode == "cached":
            got = self._cached(name, schema)
            if got is None:
                self.finish(st, "failed", message="No cached AMD run recorded for this step.")
                return None
            self.a.trace.append(got[1])
            self.finish(st, "done", "cached", "Served from the recorded AMD run.")
            return got[0]
        try:
            result, trace = await call()
        except (LLMError, asyncio.TimeoutError) as exc:
            if isinstance(exc, LLMError) and exc.trace is not None:
                self.a.trace.append(exc.trace)
            reason = exc.code if isinstance(exc, LLMError) else "timeout"
            got = self._cached(name, schema) if self.case.is_sample else None
            if got is not None:
                self.a.trace.append(got[1])
                self.finish(st, "done", "cached", f"Live AMD call failed ({reason}); served the recorded AMD run.")
                return got[0]
            self.finish(st, "failed", message=f"AI unavailable ({reason}). Retry the analysis.")
            return None
        self.a.trace.append(trace)
        self.finish(st, "done", trace.source)
        return result

    async def run(self) -> None:
        a, case = self.a, self.case
        # 1 ingest (already parsed and validated at case creation)
        st = self.start("ingest")
        ds = case.dataset_summary
        self.finish(st, "done", "computed", f"{ds.rows} samples, {len(case.events)} log events, "
                                            f"{len(case.images)} photo(s)")
        # 2 SPC
        st = self.start("spc")
        spc = analyze(case.df, case.spec, case.baseline_end)
        spc.n_dropped = ds.dropped_rows
        a.spc = spc
        cp_time = spc.change_point.timestamp if spc.change_point.detected else None
        a.parameter_shifts = parameter_shifts(case.df, case.parameters, cp_time)
        msg = (f"Shift at {ts(cp_time)}; {spc.out_of_spec.count} samples out of spec" if cp_time
               else "No significant shift detected")
        self.finish(st, "done", "computed", msg)
        # 3 correlate
        st = self.start("correlate")
        a.correlated_events = correlate_events(case.events, cp_time)
        a.evidence = build_process_evidence(spc, a.parameter_shifts, a.correlated_events, case.events, case.spec)
        self.finish(st, "done", "computed", f"{len(a.correlated_events)} event(s) within ±2 h of the shift"
                    if cp_time else "Skipped: no shift to correlate")

        context = case_context(case)

        # 4 + 5 in parallel
        async def facts_call():
            return await self.llm.chat_json("text", prompts.complaint_facts_messages(case.complaint_text),
                                            ComplaintFacts, "complaint_facts", max_tokens=MAX_TOKENS["complaint_facts"])

        async def vision_call():
            ctx = f"{context}\nComplaint summary: rejected parts, see complaint."
            return await self.llm.chat_json("vision", prompts.defect_vision_messages([im.data for im in case.images], ctx),
                                            DefectFindings, "defect_vision", max_tokens=MAX_TOKENS["defect_vision"])

        facts_task = self.ai_step("complaint_facts", ComplaintFacts, facts_call) if case.complaint_text else None
        vision_task = self.ai_step("defect_vision", DefectFindings, vision_call) if case.images else None
        if facts_task is None:
            self.finish(self.a.step("complaint_facts"), "skipped", message="No complaint text provided")
        if vision_task is None:
            self.finish(self.a.step("defect_vision"), "skipped", message="No photo provided")
        results = await asyncio.gather(*(t for t in (facts_task, vision_task) if t is not None))
        it = iter(results)
        facts = next(it) if facts_task is not None else None
        vision = next(it) if vision_task is not None else None
        if facts is not None:
            a.complaint_facts = facts
            a.evidence += complaint_evidence(facts)
        if vision is not None:
            a.defect_findings = vision.findings
            a.evidence += image_evidence(vision.findings)

        valid = valid_ids(a.evidence)
        evidence_block = format_evidence_block(a.evidence)

        # 6 hypotheses
        async def hyp_call():
            return await self.llm.chat_json("text", prompts.hypotheses_messages(context, evidence_block),
                                            HypothesesOut, "hypotheses", max_tokens=MAX_TOKENS["hypotheses"])

        hyps = await self.ai_step("hypotheses", HypothesesOut, hyp_call)
        if hyps is not None:
            cleaned = []
            for h in sorted(hyps.hypotheses, key=lambda x: x.rank)[:6]:
                h.supporting = [i for i in dict.fromkeys(h.supporting) if i in valid]
                h.contradicting = [i for i in dict.fromkeys(h.contradicting) if i in valid]
                if not h.supporting:
                    h.unsupported, h.confidence = True, "low"
                cleaned.append(h)
            for i, h in enumerate(cleaned, start=1):
                h.rank = i
            a.hypotheses = cleaned

        # 7 draft 8D
        block = containment_block(case, a)
        hyp_json = json.dumps([h.model_dump(exclude={"unsupported"}) for h in a.hypotheses], ensure_ascii=False)

        async def draft_call():
            return await self.llm.chat_json("text", prompts.draft_8d_messages(context, block, hyp_json, evidence_block),
                                            Draft8D, "draft_8d", max_tokens=MAX_TOKENS["draft_8d"])

        draft = await self.ai_step("draft_8d", Draft8D, draft_call)
        if draft is not None:
            case.report = build_report(draft, valid, block)
            a.first_draft_seconds = round(time.perf_counter() - self.t0, 1)

        # 8 number trace
        st = self.start("trace_check")
        if case.report is not None:
            allowed = allowed_values([e.text for e in a.evidence] + [case.complaint_text, block, context])
            trace_numbers(case.report, allowed)
            flagged = sum(len(s.untraceable_numbers) for s in case.report.sections)
            self.finish(st, "done", "computed", "All numbers trace to evidence" if not flagged
                        else f"{flagged} number(s) need checking")
        else:
            self.finish(st, "skipped", message="No draft to check")


async def run_analysis(case: Case, analysis: Analysis, llm: Any, cached_run: dict | None) -> Analysis:
    """Run the full pipeline. Never raises: failures are recorded on the analysis and its steps."""
    runner = _Runner(case, analysis, llm, cached_run)
    try:
        await runner.run()
        analysis.status = "done" if analysis.step("draft_8d").status == "done" else "failed"
        if analysis.status == "failed":
            analysis.error = "The 8D draft could not be produced; see failed steps."
    except asyncio.CancelledError:
        analysis.status, analysis.error = "failed", "Analysis cancelled."
        raise
    except Exception as exc:  # defensive: record, never crash the server
        log.exception("analysis failed")
        analysis.status, analysis.error = "failed", f"Unexpected error: {type(exc).__name__}: {exc}"
        for st in analysis.steps:
            if st.status in ("pending", "running"):
                st.status, st.message = "failed", "Not completed because of an earlier error."
    finally:
        analysis.finished_at = _now()
        analysis.elapsed_seconds = round(time.perf_counter() - runner.t0, 1)
    return analysis
