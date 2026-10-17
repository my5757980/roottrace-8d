---
description: "Task list for RootTrace 8D (001-roottrace-8d)"
---

# Tasks: RootTrace 8D (complaint to evidence-backed 8D draft)

**Input**: Design documents in `specs/001-roottrace-8d/` (plan.md, spec.md, research.md,
data-model.md, contracts/openapi.yaml, quickstart.md)
**Tests**: Required by constitution Principle VI: unit tests for analytics, number tracing, ingest
validation and LLM client limits, plus one golden-path smoke test with the mock LLM.
**Organization**: Grouped by user story. US1 is the MVP: the judged golden path, deployed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: US1, US2 or US3 (from spec.md)

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create the package skeleton: `app/__init__.py`, `app/llm/__init__.py`, `app/tools/__init__.py`, the empty dirs `static/css`, `static/js`, `sample_case/`, `scripts/` and `tests/unit`, `tests/integration`, plus `tests/__init__.py` and `tests/conftest.py`
- [X] T002 [P] Create `requirements.txt` (fastapi, uvicorn[standard], pydantic, pandas, numpy, httpx, python-multipart, pillow), `requirements-dev.txt` (`-r requirements.txt`, pytest) and `pytest.ini` (testpaths=tests, asyncio not required)
- [X] T003 [P] Create `.gitignore` (.env, .venv, __pycache__, *.pyc, .pytest_cache), `.dockerignore`, `.env.example` (all AMD_* and LLM_* variables with comments) and `LICENSE` (MIT, 2026, RootTrace 8D contributors)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ Must be complete before user story work starts**

- [X] T004 Implement settings in `app/config.py`: read AMD_LLM_BASE_URL, AMD_LLM_API_KEY, AMD_TEXT_MODEL, AMD_VISION_MODEL, AMD_VISION_BASE_URL, AMD_VISION_API_KEY, AMD_PROVIDER_LABEL, LLM_MODE (auto, live or mock), LLM_MAX_CONCURRENCY=8, LLM_MAX_RPM=20, LLM_TIMEOUT_S=90, LLM_MAX_ATTEMPTS=3, LLM_REASONING_EFFORT (optional), CASE_TTL_S=7200, MAX_CASES=300, MAX_UPLOAD_MB=10 and PORT=7860. `mode` resolves to live when a key and base URL are set, otherwise mock
- [X] T005 [P] Implement the Pydantic schemas from data-model.md in `app/models.py`: SpecLimits, ColumnMap, MaintenanceEvent, SPCResult and its parts, ParameterShift, CorrelatedEvent, EvidenceItem, ComplaintFacts, DefectFinding, Hypothesis, ReportSection, Report, StepState, TraceEntry, Analysis and CaseView, including the enums for taxonomy, confidence, 6M category and section status
- [X] T006 [P] Implement the in-memory store in `app/store.py`: a CaseStore with create/get/touch, TTL expiry, LRU eviction at MAX_CASES and a per-case asyncio.Lock. Case IDs come from `secrets.token_urlsafe(16)`
- [X] T007 Implement the OpenAI-compatible async client in `app/llm/client.py`:
  - `LLMClient.chat_json(role, messages, schema, step)` returns (parsed model, TraceEntry)
  - Send only the whitelisted body fields
  - Concurrency semaphore and a sliding-window RPM limiter
  - Retries: honor Retry-After on 429/503, exponential backoff with full jitter on 5xx and timeouts, no retry on other 4xx
  - Tolerant JSON extraction (code fences, first balanced object) and Pydantic validation, with one corrective retry
  - Read token usage from `usage`
  - An injectable `httpx.AsyncClient` transport so tests can fake it
- [X] T008 [P] Write `tests/unit/test_llm_client.py` using httpx.MockTransport. Cover:
  - success parses JSON inside code fences
  - 429 with Retry-After is retried and then succeeds
  - 400 is not retried
  - invalid JSON triggers exactly one corrective retry and then raises
  - the request body contains only whitelisted keys
  - the semaphore caps concurrency
- [X] T009 [P] Implement the deterministic mock provider in `app/llm/mock.py`. It returns schema-valid outputs for the 4 AI steps, built from the prompt's evidence block (it cites the IDs it finds). Its trace provider label is "MOCK (not AMD)"
- [X] T010 Implement input parsing in `app/ingest.py`:
  - `parse_process_csv(bytes, ColumnMap)` checks the required columns, parses and sorts timestamps (counting drops), coerces numeric values and detects parameter columns, then returns a DataFrame and warnings
  - `parse_maintenance_log(bytes)` returns a list of MaintenanceEvent with IDs L1..Ln
  - `normalize_image(bytes)` validates the type and returns a JPEG with the longest side ≤ 1024 px
  - `read_complaint(text|bytes)` handles .eml (subject and plain body)
  - Every validation error is raised as an `IngestError` with an actionable message
- [X] T011 [P] Write `tests/unit/test_ingest.py`: missing value column → IngestError naming the column, non-numeric rows dropped and counted, mixed or unordered timestamps sorted, oversize or wrong-type image rejected, .eml subject and body extracted
- [X] T012 Implement the evidence registry in `app/evidence.py`. `build_evidence(spc, shifts, correlated, events, complaint_facts?, defect_findings?)` returns a list of EvidenceItem with stable IDs S*, P*, L*, C*, I*. Also implement `format_evidence_block(items)` → "[ID] text" lines and `valid_ids(items)`
- [X] T013 Implement the app skeleton in `app/main.py`: FastAPI app, an error handler that turns IngestError and HTTPException into `{"error":{code,message,details}}`, `GET /api/health` (mode, provider, models, cached_run_available, version), and static mounting with `/` → static/index.html and `/report.html`

**Checkpoint**: the foundation is ready, and `pytest tests/unit/test_llm_client.py tests/unit/test_ingest.py` passes

---

## Phase 3: User Story 1 - One-click analysis of the sample complaint (Priority: P1) 🎯 MVP

**Goal**: on first load, the sample case is visible, and a single Analyze click produces facts, a defect finding, SPC with a change point, correlated events, ranked hypotheses, the 8D draft with deterministic containment, and the AMD trace. A cached fallback covers failures.
**Independent Test**: the golden-path smoke test passes, and quickstart §6 steps 1–5 and 7 pass in a browser.

### Implementation for User Story 1

- [X] T014 [US1] Write the seeded generator `scripts/generate_sample_case.py` (numpy seed 2207). It writes:
  - `sample_case/process_data.csv`: 672 rows every 30 min from 2026-09-28 06:00, CNC-07, shifts A/B/C, lots L{yymmdd}-{A|B|C}, part serials, bore_diameter_mm, spindle_temp_c, coolant_conc_pct, tool_id and tool_life_count. The baseline is μ = 42.0125, σ = 0.0022. From 2026-10-08 14:20 there is a step of +0.0085 plus a drift of +0.00012 mm/h. Coolant dips from 7.5% to 5.6% at 2026-10-09 22:10
  - `sample_case/maintenance_log.csv`: about 12 events, including the TOOL_CHANGE at 2026-10-08 14:20, a FIRST_PIECE "visual only, CMM busy" at 14:45, the COOLANT top-up at 2026-10-09 22:10, a SHIFT_HANDOVER note about ignored warning points, and routine PM and checks
  - `sample_case/complaint.txt`: from Ardena Motors S.p.A. (fictional), 37 housings with low press-fit force, measured 42.027–42.031 mm vs 42.000 +0.025, lots L261008-B and L261009-A, D3 due within 24 h
  - `sample_case/defect_photo.jpg`: a procedural bore with chatter marks and a red REJECT tag reading L261009-A
  - `sample_case/case.json`: title, part, characteristic, unit, lsl, usl, target, column map and baseline_end
  - Then run it
- [X] T015 [US1] Implement `app/spc.py`:
  - `analyze(df, spec, value_col, baseline_end=None)` builds the I-MR baseline (σ̂ = MR̄/1.128), the limits and zones
  - Western Electric rules 1–4, deduplicated per point
  - Cp/Cpk for the baseline window and the window after the change point
  - The change point (best mean-shift split, minimum segment 10, Welch t > 5 and |Δ| ≥ 1σ̂)
  - The out-of-spec summary
  - Containment: from the last sample before the change point to the last record, with its lots
  - A downsampled series (keep flagged points) and a one-line explanation for each fact
  - Warnings for < 20 baseline points and for missing limits
  - `parameter_shifts(df, params, cp_time)` for the machine parameters
- [X] T016 [P] [US1] Write `tests/unit/test_spc.py` on synthetic arrays:
  - rule 1 fires on a +4σ point
  - rule 2 fires on 2 of 3 points beyond 2σ
  - rule 3 fires on 4 of 5 points beyond 1σ
  - rule 4 fires on 8 points on one side
  - no rule fires on centred noise (fixed seed)
  - Cp/Cpk matches the hand-computed value
  - the change point is found within ±1 index of an injected step
  - no change point is reported on stationary data
  - containment covers all OOS points
  - fewer than 20 points gives a warning and no limits
  - deterministic: same input, same output
- [X] T017 [US1] Implement `app/correlate.py`: `correlate_events(events, cp_time, window_h=2)` returns CorrelatedEvent sorted by |Δ| and `summarize_parameter_shifts(...)`, plus the evidence texts (for example "Coolant concentration shift at 2026-10-09 22:10 (−1.9 %), 31.8 h after the bore shift")
- [X] T018 [P] [US1] Write `tests/unit/test_correlate.py`: an event inside the window is matched with a signed Δ in minutes, an event outside the window is excluded, an empty log gives an empty list, and a parameter shift reports hours_from_cp
- [X] T019 [US1] Implement `app/numbers.py`. `find_untraceable(text, evidence_texts)` uses a standalone-number regex (skipping D3, 8D, 5W2H and 6M), matches at the same rounding (and the evidence values rounded to the candidate's decimals), and ignores integers ≤ 12 and years 1990–2100
- [X] T020 [P] [US1] Write `tests/unit/test_numbers.py`: "42.031" is traceable when present, "42.0305" is flagged when absent, "D3"/"8D"/"5W2H" are ignored, small integers are ignored, a rounded value ("1.9" from "1.87") is traceable, and percentages are handled
- [X] T021 [US1] Implement the prompt builders in `app/llm/prompts.py` for complaint_facts, defect_vision (taxonomy, images as data URLs), hypotheses (evidence block, 3–6 items, 6M, cite IDs only, contradicting evidence) and draft_8d (sections D1–D8, a fixed containment facts block used verbatim, numbers only from evidence, cited IDs). Add the output schemas used for validation
- [X] T022 [US1] Implement `app/sample.py`: `load_sample_case()` reads sample_case/* into the case inputs, and `load_cached_run()` returns the parsed cached_run.json or None
- [X] T023 [US1] Implement the orchestrator in `app/pipeline.py`. `run_analysis(case, mode, client, settings)` runs:
  - the steps in order: ingest → spc → correlate → (complaint_facts ∥ defect_vision) → hypotheses → draft_8d → trace_check
  - StepState updates, with the step source set to live, cached, mock or computed
  - validation of evidence IDs (flag unsupported ones)
  - building the Report sections with D3 containment facts prepended deterministically
  - untraceable-number flags
  - per-step cached fallback for the sample case, plus a `mode=cached` fast path
  - TraceEntry collection and elapsed_seconds
  - it never raises out of the task (failures are recorded per step)
- [X] T024 [US1] Add the US1 routes to `app/main.py`: `POST /api/cases/sample` (201 CaseView), `GET /api/cases/{id}`, `GET /api/cases/{id}/images/{index}`, `POST /api/cases/{id}/analyze` (202, background task, 409 if already running, cached allowed only for the sample case) and `GET /api/cases/{id}/analysis`, all matching contracts/openapi.yaml
- [X] T025 [US1] Write `tests/integration/test_golden_path.py`. With TestClient and LLM_MODE=mock, it creates the sample case, starts the analysis, polls until done and asserts:
  - all 8 steps are done
  - the change point is within 15 min of 2026-10-08 14:20
  - containment includes all OOS lots and starts ≤ 1 h before the change point
  - the report has 8 sections
  - the trace has 4 AI entries
  - every hypothesis has ≥ 1 supporting ID
- [X] T026 [P] [US1] Build `static/index.html` and `static/css/app.css`:
  - header with the RootTrace 8D brand and an AMD badge (provider, models, live/mock)
  - case panel (complaint, photo, data summary, log)
  - Analyze and "Use cached AMD run" buttons
  - step timeline
  - result panels: facts, defect, SPC chart and stats, correlated events, hypotheses, 8D, AI trace
  - a responsive 2-column layout and a clean industrial visual style
- [X] T027 [P] [US1] Implement `static/js/chart.js`. `renderControlChart(el, spc, events)` draws an SVG I-chart with CL, UCL/LCL, zones, LSL/USL, the data polyline, violation markers colored by rule, the change-point line, the shaded containment range and event markers, with `<title>` tooltips
- [X] T028 [US1] Implement `static/js/api.js` and `static/js/app.js` (boot → POST /api/cases/sample → render inputs, Analyze → POST analyze → poll every 800 ms → render steps and partial results) and `static/js/render.js` (panels for facts with quotes, the defect card, the stats table with explanations, correlated events, hypotheses with evidence chips that expand to the evidence text, 8D sections read-only for now, and the trace table with totals)
- [X] T029 [US1] Implement `app/tools/record_sample_run.py`. It runs the live pipeline on the sample case and checks that every AI step is ok and there are no untraceable numbers. It writes `sample_case/cached_run.json` (recorded_at, provider, models and per-step result and trace) and prints a summary. It exits non-zero when a check fails
- [ ] T030 [P] [US1] Write the `Dockerfile` (python:3.12-slim, a non-root user, pip install -r requirements.txt, copy app/static/sample_case, `CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}`, EXPOSE 7860) and verify `docker build`
- [X] T031 [P] [US1] Write `README.md`: problem, solution, demo link placeholder, how AMD is used (TokenFactory or vLLM on MI300X, the trace), architecture diagram (text), quickstart (local, Docker, HF Space), env vars, recording the cached run, tests, the MIT license and a link to docs/hackathon/HACKATHON_BRIEF.md
- [ ] T032 [US1] Record the cached AMD run with the real AMD key (`python -m app.tools.record_sample_run`) and commit `sample_case/cached_run.json` *(needs the AMD key from the user)*
- [ ] T033 [US1] Deploy to a Hugging Face Space (Docker SDK) with the secrets set, then verify quickstart §6 steps 1–5 and 7 on the public URL *(needs the user's HF account)*

**Checkpoint**: MVP is live. The golden path works publicly with the AMD trace and the cached fallback.

---

## Phase 4: User Story 2 - Review, approve and export the 8D report (Priority: P2)

**Goal**: the engineer edits and approves sections, then opens a printable report with DRAFT watermarks.
**Independent Test**: quickstart §6 step 6, plus `tests/unit/test_report_state.py`.

- [X] T034 [US2] Implement the section state transitions in `app/report.py`, following the data-model.md state diagram. `apply_section_update(section, content?, approved?, reviewer?)` returns the updated section and runs the trace check on content edits. Add `PATCH /api/cases/{id}/report/sections/{section_id}` to `app/main.py` (404, 409 when there is no report yet, 422 on validation)
- [X] T035 [P] [US2] Write `tests/unit/test_report_state.py`: edit → edited, approve → approved with reviewer and time, edit after approval → needs_reapproval, unapprove → back to edited or ai_draft, an unknown section → error
- [X] T036 [US2] Add the editing UI in `static/js/render.js` and `static/js/app.js`: a reviewer-name input, per-section Edit/Save textarea, Approve/Unapprove toggle, status badge, untraceable-number warning chips and the approval counter
- [X] T037 [P] [US2] Build `static/report.html`, `static/js/report.js` and `static/css/print.css`: fetch the case by `?case=`, then render the header (case ID, date, approval summary), the complaint facts, the SVG chart (reusing chart.js), the evidence table, the hypotheses, D1–D8 (DRAFT watermark on unapproved sections) and the AI trace appendix. Add a "Print / Save as PDF" button and A4 print styles

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Analyze my own complaint case (Priority: P3)

**Goal**: upload a custom case with validation and run the same analysis.
**Independent Test**: upload a valid CSV with a known shift → analysis runs. Upload a CSV without a timestamp column → a specific 422 error.

- [X] T038 [US3] Add `POST /api/cases` (multipart) to `app/main.py`, matching the contract: size and type limits (413/422), ingest validation errors with details, and creation of a non-sample case (mode=cached rejected with 422)
- [X] T039 [P] [US3] Extend `tests/integration/test_golden_path.py` (or add `tests/integration/test_custom_case.py`): a valid custom upload → 201 and the analysis completes in mock mode; a missing timestamp column → 422 naming the column; a 4th image → 422
- [X] T040 [US3] Add a "New case" dialog in `static/index.html` and `static/js/app.js` (complaint paste or file, up to 3 images, process CSV, column and limits fields prefilled with the defaults, optional log). Show the server's error details inline

---

## Phase 6: Polish, Hardening and Submission Assets

- [X] T041 [P] Add a per-IP throttle for live analyses (5 per 10 min, then serve cached for the sample case and 429 for custom cases) in `app/main.py`, with a small test
- [ ] T042 [P] Write `docs/submission/SUBMISSION.md`: title (≤ 50 chars), short description (50–255), long description (600–2,000), track, tech tags and the "Additional info" text. Validate the lengths with `scripts/check_submission.py`
- [ ] T043 [P] Write `docs/submission/VIDEO_SCRIPT.md`: a 3:30–4:30 script (problem 0:00–0:30, live demo 0:30–2:30, business case and TAM/revenue 2:30–3:30, competitors and roadmap 3:30–4:15) with a shot list
- [ ] T044 [P] Build `docs/submission/slides.html` (9 slides: problem, user, solution, live demo screenshot, how it works on AMD, results/KPIs, market and revenue, competition and USP, roadmap and team) with print CSS so it exports to PDF
- [ ] T045 [P] Generate `docs/submission/cover.png` (16:9, 1920×1080) with `scripts/make_cover.py` (Pillow)
- [ ] T046 Run the full test suite, a Docker build and the quickstart walk-through. Scan the repository and git history for secrets (`git grep -nE "(sk-|rc-|api[_-]?key\s*=\s*['\"][A-Za-z0-9])"`) and fix anything found
- [ ] T047 Update the README with the live demo URL, a screenshot and the submission links

---

## Dependencies & Execution Order

- **Setup (T001–T003)**: depends on nothing.
- **Foundational (T004–T013)**: depends on Setup and blocks every story. T007 depends on T004 and T005. T009 depends on T005. T012 depends on T005.
- **US1 (T014–T033)**:
  - T015 needs T014 (it needs the sample data to calibrate)
  - T023 needs T015, T017, T019, T021 and T022
  - T024 needs T023
  - T025 needs T024
  - T028 needs T024, T026 and T027
  - T029 needs T023
  - T032 needs T029 and the AMD key
  - T033 needs T030 and T032
- **US2 (T034–T037)**: needs T023 (a report exists). It is independent of US3.
- **US3 (T038–T040)**: needs T010 and T023. It is independent of US2.
- **Polish (T041–T047)**: T042–T045 can start any time after the MVP. T046 and T047 run last.

### Parallel Opportunities

- T002 ∥ T003. T005 ∥ T006. T008 ∥ T009 ∥ T011 (after T005 and T007 exist).
- In US1: T016 ∥ T018 ∥ T020 (tests), and T026 ∥ T027 ∥ T030 ∥ T031 (UI, chart, Docker, README).
- US2 and US3 can proceed in parallel after US1. T042–T045 can run in parallel.

## Parallel Example: User Story 1

```text
Task: "T016 tests/unit/test_spc.py"     Task: "T018 tests/unit/test_correlate.py"     Task: "T020 tests/unit/test_numbers.py"
Task: "T026 static/index.html + css"    Task: "T027 static/js/chart.js"               Task: "T030 Dockerfile"
```

## Implementation Strategy

1. **MVP first**: Setup, then Foundational, then US1 up to T031. Validate with the smoke test and a local browser run.
2. **Go live**: T032 (record the cached run with the AMD key) and T033 (deploy). From this point there is always a working public demo.
3. **Increment**: US2 (approve and export) adds the accountability story. US3 (custom upload) proves it generalizes.
4. **Submission**: T042–T047. Feature freeze 3 h before 2026-10-17 17:00 UTC (constitution Principle II).
