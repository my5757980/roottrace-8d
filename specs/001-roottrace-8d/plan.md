# Implementation Plan: RootTrace 8D (complaint to evidence-backed 8D draft)

**Branch**: `001-roottrace-8d` | **Date**: 2026-10-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-roottrace-8d/spec.md`

## Summary

A single web app for supplier quality engineers. It takes a complaint case (complaint text,
defect photos, process measurements, maintenance log) and produces an evidence-backed 8D draft
with a deterministic containment range in under two minutes. The engineer then approves or edits
each section.

The architecture puts each kind of work where it belongs:

- **Deterministic Python** computes every number: SPC limits, Western Electric rules 1–4, Cp/Cpk,
  change point, out-of-spec summary and machine-parameter shifts.
- **AMD-hosted models** do four interpretation tasks through one OpenAI-compatible client:
  complaint fact extraction, defect-photo analysis, ranked 6M hypotheses and the 8D draft.
- **A deterministic number-trace check** flags any number in the AI narrative that does not come
  from a computed fact.

All AI output cites IDs from an evidence registry, and every model call is recorded in an AMD
inference trace that the UI shows. A precomputed "cached AMD run" of the bundled sample case keeps
the demo working under rate limits.

## Technical Context

**Language/Version**: Python 3.12 (backend). Vanilla HTML, CSS and JS ES modules (frontend, no build step).
**Primary Dependencies**: FastAPI, Uvicorn, Pydantic v2, pandas, numpy, httpx, python-multipart and Pillow. All are MIT, BSD, Apache or HPND licensed.
**Storage**: None. Cases live in an in-memory store with a TTL. The sample case and its cached run are bundled files.
**Testing**: pytest. httpx `MockTransport` fakes the LLM transport, and FastAPI `TestClient` runs the golden-path smoke test.
**Target Platform**: A Linux container (Docker). The primary host is Hugging Face Spaces (Docker SDK, port 7860), and any container host works.
**Project Type**: A web application served as one service. The backend package `app/` serves the API and the static frontend in `static/`.
**Performance Goals**: The golden path finishes live in 120 s or less (4 model calls, 2 of them parallel). The cached sample case appears in 5 s or less. Deterministic analytics on 10k rows take under 1 s.
**Constraints**:
- The AMD gateway allows about 20 RPM and 8 concurrent requests, and drops unknown fields.
- Upload limit is 10 MB per file.
- No secrets reach the browser.
- No login.
- Hard stop is 2026-10-17 17:00 UTC.

**Scale/Scope**: Hackathon judging traffic, with tens of concurrent visitors at most. There is one golden-path case, plus support for custom cases. The UI has one page plus a printable report page.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. AMD-Powered, Visibly | All model calls go through `app/llm/client.py` to the AMD endpoint in env. Each step has a trace entry (provider label, model, live/cached, latency, tokens) shown in the UI. The mock is labeled "MOCK (not AMD)" and is off when a key is set. A Gemma model can be selected per role (`AMD_VISION_MODEL`). | ✅ |
| II. Deadline-First Scope | The P1 golden path is built first, then deploy, then P2 (approve and export), then P3 (custom upload). Polish comes last. | ✅ |
| III. Evidence-Cited, Human-Approved | An evidence registry gives IDs to every fact. The LLM must cite IDs, and the server validates them. Each section has a state (AI draft, edited, approved, needs re-approval). The report watermarks unapproved sections as DRAFT. | ✅ |
| IV. Deterministic Analytics | `app/spc.py` and `app/correlate.py` compute every number. The LLM only receives facts, and `app/numbers.py` flags untraceable numbers. | ✅ |
| V. Resilient Inference | A single client. An asyncio semaphore caps concurrency at 8 and a sliding-window limiter caps RPM at 20. It honors `Retry-After`, retries 429 and 5xx with backoff and jitter, and sends only whitelisted fields. A per-step cached fallback covers the sample case. | ✅ |
| VI. Test the Deterministic Core | Unit tests cover SPC rules, capability, change point, number trace, ingest validation and client retry and limits. One golden-path smoke test runs with the mock LLM. | ✅ |
| VII. Judge-Proof Delivery | No login. The sample case is preloaded. One Dockerfile. The README and `.env.example` are part of the plan. The submission assets are tracked as tasks. | ✅ |
| VIII. Security & Open Source | Keys stay server-side and come from env. `.env` is gitignored. Uploads are capped at 10 MB, limited to whitelisted types and kept in memory only. The repo is MIT-licensed and the sample data is self-generated. | ✅ |
| IX. Simplicity | One container, no database, no auth, no frontend build. 4 model calls per analysis (6 or fewer). Polling instead of SSE (see research R4). | ✅ |

Post-design re-check (after Phase 1): ✅ all gates still pass. There are no violations, so
Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-roottrace-8d/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities and schemas
├── quickstart.md        # Phase 1 run, verify and deploy guide
├── contracts/
│   └── openapi.yaml     # Phase 1 HTTP API contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 (/sp.tasks)
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py              # FastAPI app: routes, static files, error handlers
├── config.py            # Settings from environment variables
├── models.py            # Pydantic schemas (domain + API)
├── store.py             # In-memory case store (TTL, max size, per-case lock)
├── ingest.py            # Parse and validate complaint text, images, process CSV, maintenance log
├── spc.py               # Deterministic SPC: I-MR limits, WE rules 1-4, Cp/Cpk, change point, OOS
├── correlate.py         # Event correlation window, machine-parameter shift analysis
├── evidence.py          # Evidence registry (IDs: C*, I*, S*, P*, L*) built from inputs and facts
├── numbers.py           # Number-trace check for AI narrative
├── pipeline.py          # Step orchestration, statuses, cached fallback, trace collection
├── sample.py            # Sample case loader and cached-run loader
├── llm/
│   ├── __init__.py
│   ├── client.py        # OpenAI-compatible async client: limiter, retries, JSON parsing
│   ├── mock.py          # Deterministic mock provider (dev/tests, labeled MOCK)
│   └── prompts.py       # Prompt builders for the 4 AI steps
└── tools/
    ├── __init__.py
    └── record_sample_run.py  # Records sample_case/cached_run.json from a live AMD run

static/
├── index.html           # Main single-page UI
├── report.html          # Printable 8D report page
├── css/app.css
├── css/print.css
└── js/
    ├── api.js           # Fetch helpers
    ├── app.js           # State, polling, event wiring
    ├── render.js        # Panels: facts, defect, SPC stats, hypotheses, 8D, trace
    ├── chart.js         # SVG control chart
    └── report.js        # Report page rendering

sample_case/
├── case.json            # Metadata: part, characteristic, spec limits, baseline, columns
├── complaint.txt
├── defect_photo.jpg
├── process_data.csv
├── maintenance_log.csv
└── cached_run.json      # Recorded live AMD run (created by app/tools/record_sample_run.py)

scripts/
└── generate_sample_case.py   # Seeded generator for the sample data and photo

tests/
├── unit/
│   ├── test_spc.py
│   ├── test_correlate.py
│   ├── test_numbers.py
│   ├── test_ingest.py
│   └── test_llm_client.py
└── integration/
    └── test_golden_path.py

Dockerfile · .dockerignore · .gitignore · .env.example · requirements.txt
requirements-dev.txt · pytest.ini · LICENSE · README.md
```

**Structure Decision**: one Python package (`app/`) serves both the JSON API under `/api` and
the static frontend (`static/`). This keeps a single container and avoids a frontend build, which
satisfies Principle IX. Tests sit at the root under `tests/`.

## Pipeline Design (steps and data flow)

| # | Step | Kind | Depends on | Output |
|---|------|------|-----------|--------|
| 1 | `ingest` | deterministic | inputs | Parsed dataset, events, complaint text, images, and validation warnings |
| 2 | `spc` | deterministic | 1 | SPCResult and machine-parameter shifts |
| 3 | `correlate` | deterministic | 1, 2 | Correlated events (±2 h window) |
| 4 | `complaint_facts` | **AI (text)** | 1 | ComplaintFacts with source quotes |
| 5 | `defect_vision` | **AI (vision)** | 1 | DefectFinding per image (one call, all images) |
| 6 | `hypotheses` | **AI (text)** | 2–5 + evidence registry | 3–6 ranked hypotheses citing evidence IDs |
| 7 | `draft_8d` | **AI (text)** | 2–6 + containment facts | D1–D8 sections citing evidence IDs |
| 8 | `trace_check` | deterministic | 7 | Untraceable-number flags per section |

- Steps 4 and 5 run concurrently after step 1. Steps 2 and 3 take milliseconds.
- The containment range is deterministic. It runs from the last in-control sample before the
  change point to the last production record, and the suspect lots are all lots with records in
  that range. The 8D draft has to use it verbatim.
- If an AI step fails after retries:
  - Sample case: that step's result is replaced by the cached AMD run's result for that step,
    labeled `cached`.
  - Custom case: the step is marked failed, and its dependants either run with partial evidence
    or are skipped with a reason.

## Complexity Tracking

No constitution violations.
