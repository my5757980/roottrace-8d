"""Record the cached AMD run of the sample case (sample_case/cached_run.json).

Runs the full pipeline live against the configured AMD endpoint, checks that every AI step
succeeded live and that no number in the draft is untraceable, then writes the recording.

Usage:  python -m app.tools.record_sample_run [--force]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone

from app.config import load_settings
from app.llm.client import LLMClient
from app.pipeline import AI_STEPS, new_analysis, run_analysis
from app.sample import CACHED_RUN, SAMPLE_DIR, build_case, load_sample_inputs

RESULT_FIELDS = {
    "complaint_facts": lambda a, c: a.complaint_facts.model_dump(mode="json") if a.complaint_facts else None,
    "defect_vision": lambda a, c: {"findings": [f.model_dump(mode="json") for f in a.defect_findings]} if a.defect_findings else None,
    "hypotheses": lambda a, c: {"hypotheses": [h.model_dump(mode="json", exclude={"unsupported"}) for h in a.hypotheses]} if a.hypotheses else None,
    "draft_8d": lambda a, c: {"sections": [{"id": s.id, "title": s.title, "content": s.ai_content, "evidence": s.evidence}
                                           for s in c.report.sections]} if c.report else None,
}


async def record(force: bool) -> int:
    settings = load_settings()
    if settings.mode != "live":
        print("ERROR: AMD endpoint not configured (set AMD_LLM_BASE_URL, AMD_LLM_API_KEY, AMD_TEXT_MODEL).")
        return 2
    client = LLMClient(settings)
    case = build_case(load_sample_inputs())
    analysis = new_analysis("live")
    print(f"Running live analysis on {settings.provider_label} (text={settings.text.model}, vision={settings.vision.model})…")
    await run_analysis(case, analysis, client, cached_run=None)
    await client.aclose()

    ok = True
    for st in analysis.steps:
        print(f"  {st.name:16s} {st.status:8s} {st.source or '':8s} {st.message or ''}")
        if st.name in AI_STEPS and (st.status != "done" or st.source != "live"):
            ok = False
    flagged = {s.id: s.untraceable_numbers for s in (case.report.sections if case.report else []) if s.untraceable_numbers}
    if flagged:
        print(f"  untraceable numbers: {flagged}")
        ok = False
    for t in analysis.trace:
        print(f"  trace {t.step:16s} {t.model:30s} {t.latency_ms:6d} ms  tokens {t.prompt_tokens}/{t.completion_tokens}  {t.status}")

    traces = {t.step: t for t in analysis.trace if t.status == "ok"}
    steps = {}
    for name in AI_STEPS:
        result = RESULT_FIELDS[name](analysis, case)
        if result is not None and name in traces:
            steps[name] = {"result": result, "trace": traces[name].model_dump(mode="json")}
    recording = {
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": settings.provider_label,
        "models": {"text": settings.text.model, "vision": settings.vision.model},
        "elapsed_seconds": analysis.elapsed_seconds,
        "steps": steps,
    }
    target = CACHED_RUN if (ok or force) else SAMPLE_DIR / "cached_run.candidate.json"
    target.write_text(json.dumps(recording, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{'OK' if ok else 'CHECKS FAILED'}: wrote {target}")
    if not ok and not force:
        print("Re-run, or pass --force to accept this recording anyway.")
    return 0 if ok or force else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="write cached_run.json even if checks fail")
    args = parser.parse_args()
    sys.exit(asyncio.run(record(args.force)))


if __name__ == "__main__":
    main()
