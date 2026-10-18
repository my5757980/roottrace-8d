---
id: 23
title: SnapDeploy live demo deployed
stage: misc
date: 2026-10-18
surface: agent
model: claude-opus-5-5
feature: 001-roottrace-8d
branch: 001-roottrace-8d
user: ASFAR
command: none (free-form prompt)
labels: ["deploy", "snapdeploy", "live-demo", "submission"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - .env.example
 - README.md
 - docs/submission/SUBMISSION.md
tests:
 - /api/health on https://roottrace-8d-a18dc.containers.snapdeploy.app returned live mode, AMD models
 - remote end-to-end sample run finished in 190.5 s; 3 AI steps live on AMD; 8D draft served from the recorded run after the 100 s budget
---

## Prompt

hogayaaaaaa

## Response snapshot

- **Setup:** created a free Small container (512 MB) on SnapDeploy from the GitHub repo, on port 7860 with auto-deploy off.
- **Required-settings fix:** SnapDeploy's env detector marked the empty optional settings in `.env.example` as required. I commented them out (`AMD_VISION_BASE_URL`, `AMD_VISION_API_KEY`, `LLM_REASONING_EFFORT`), pushed, and re-ran detection.
- **Settings:** filled 18 values. The AMD key went in by clipboard and was never shown. I deleted the snapshots that captured it.
- **Live URL:** https://roottrace-8d-a18dc.containers.snapdeploy.app passed the health check in live mode.
- **End-to-end run:** vision, complaint facts and hypotheses ran live on AMD (11 s, 39 s, 52 s). The 8D draft exceeded the 100 s budget and fell back to the recorded AMD run, as labelled in the UI. Every number traced to evidence.
- **Docs:** README and SUBMISSION.md now carry the demo URL and platform.

## Outcome

- ✅ Impact: the judges have a live, public demo URL that needs no card
- 🧪 Tests: health PASS; remote end-to-end PASS (190.5 s)
- 📁 Files: .env.example, README.md, docs/submission/SUBMISSION.md
- 🔁 Next prompts: demo video, lablab form
- 🧠 Reflection: optional settings should be commented out in `.env.example` so host detectors do not mark them required

## Evaluation notes (flywheel)

- Failure modes observed: host env detector treated empty example values as required
- Graders run and results (PASS/FAIL): health PASS, e2e PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): lower LIVE_STEP_BUDGET_S on the host if judges find the run slow
