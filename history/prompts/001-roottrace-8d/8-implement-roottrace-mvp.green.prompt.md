---
id: 8
title: Implement RootTrace MVP
stage: green
date: 2026-10-17
surface: agent
model: claude-opus-5-5
feature: 001-roottrace-8d
branch: 001-roottrace-8d
user: ASFAR
command: /sp.implement
labels: ["implementation", "fastapi", "spc", "amd-inference", "frontend", "submission"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - app/ (config, models, store, ingest, spc, correlate, evidence, numbers, report, pipeline, sample, main, llm/client, llm/mock, llm/prompts, tools/record_sample_run)
 - static/ (index.html, report.html, css/app.css, css/print.css, js/api.js, js/app.js, js/render.js, js/chart.js, js/report.js)
 - scripts/generate_sample_case.py, scripts/make_cover.py, scripts/check_submission.py
 - sample_case/ (case.json, complaint.txt, defect_photo.jpg, process_data.csv, maintenance_log.csv)
 - tests/ (unit: llm_client, ingest, spc, correlate, numbers, report_state, throttle; integration: golden_path)
 - Dockerfile, .dockerignore, .gitignore, .env.example, requirements*.txt, pytest.ini, LICENSE, README.md
 - docs/submission/ (SUBMISSION.md, VIDEO_SCRIPT.md, slides.html, cover.png)
 - specs/001-roottrace-8d/tasks.md
tests:
 - pytest: 45 passed (unit + golden-path integration, mock LLM)
 - UI smoke: all render functions executed against live API data without errors
---

## Prompt

continue

(Executed as /sp.implement with input: "Implement specs/001-roottrace-8d/tasks.md in order, MVP first (Phase 1, Phase 2, US1), marking tasks [X] as completed. T032 and T033 need the user's AMD key and HF account: prepare everything and report them as pending.")

## Response snapshot

Implemented the full MVP plus US2 (review, approve and export) and US3 (custom upload):

- **Backend:** a FastAPI app with a deterministic SPC engine:
  - I-MR limits and Western Electric rules 1–4
  - Cp/Cpk
  - change point (global least-squares split refined locally, confirmed by Welch t)
  - containment from the last known-good sample
- **Shift context:** event correlation and machine-parameter shifts.
- **Trust checks:** an evidence registry with citation IDs, and a number-trace check.
- **Inference:** an OpenAI-compatible AMD client with a semaphore, an RPM limiter, Retry-After and backoff, a field whitelist and a JSON-repair retry. A deterministic MOCK provider covers local runs. The 8-step pipeline has a per-step cached AMD fallback, plus a per-IP live throttle.
- **Frontend:** a vanilla JS frontend with an SVG control chart, the 8D editor with an approval state machine, and a printable report with DRAFT watermarks.
- **Sample case:** generated with a seed. The shift is detected at 14:30, 10 minutes after the 14:20 tool change. 11 lots are suspect, against the 2 the customer named.
- **Assets:** the cover image, slides, video script and submission text (lengths validated).
- **Tests:** 45 tests pass.

Pending (blocked on the user):
- T032: record the cached AMD run, which needs the AMD key.
- T033: deploy to an HF Space, which needs the account.
- T030: Docker build verification, because Docker Desktop is not running.
- T046 and T047: final checks and README links.

## Outcome

- ✅ Impact: The judge-ready MVP works end to end in mock mode. Live AMD mode needs only the .env values
- 🧪 Tests: 45 passed; the UI smoke run is clean
- 📁 Files: see the list above
- 🔁 Next prompts: add the AMD key to .env → list models → record the cached run → git commit/push → deploy the HF Space → record the video
- 🧠 Reflection: Keeping numbers deterministic and making the AI cite evidence IDs gives a strong trust story that maps directly to the judging criteria

## Evaluation notes (flywheel)

- Failure modes observed: a slow network broke the first dependency install (fixed by dropping uvicorn[standard] and raising the timeout). Spurious parameter shifts from the daily cycle were fixed with longer segments and a std-based reference.
- Graders run and results (PASS/FAIL): pytest PASS (45); submission length check PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): tune the prompts on real AMD model output once the key is available
