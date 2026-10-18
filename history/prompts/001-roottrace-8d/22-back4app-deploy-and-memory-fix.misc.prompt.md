---
id: 22
title: Back4app deploy and memory fix
stage: misc
date: 2026-10-18
surface: agent
model: claude-opus-5-5
feature: 001-roottrace-8d
branch: 001-roottrace-8d
user: ASFAR
command: none (free-form prompt)
labels: ["deploy", "back4app", "snapdeploy", "memory"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - app/ingest.py
 - static/js/app.js
tests:
 - pytest: 45 passed
 - 12 MP JPEG normalizes to 1024x768 via reduced-scale decode
 - Back4app /api/health returned live mode with AMD models
---

## Prompt

kardiaaaa github sayyyy login

## Response snapshot

- **Back4app:** installed the Back4app GitHub app on the roottrace-8d repo only. Set port 7860 and the health check `/api/health`, and added 18 settings. The AMD key went in by clipboard and was never shown.
- **Result:** the app ran and was healthy (live mode, AMD models). But the free plan keeps the URL live for only 60 minutes, so it is no use for judges.
- **Memory fix:** in `app/ingest.py`, `normalize_image` now calls `img.draft("RGB", ...)` so phone photos decode at reduced scale. This keeps 256–512 MB hosts safe.
- **Rate fix:** in `static/js/app.js`, polling went from every 0.8 s to every 1.5 s, to stay under the shared host's limit of 100 requests a minute.
- **Next host:** SnapDeploy is free with no card, 512 MB, and a permanent `*.containers.snapdeploy.app` address. It sleeps after 15 minutes idle and wakes in about 60 s. Asked the user to log in with GitHub.

## Outcome

- ✅ Impact: confirmed the Docker image runs live on a small host; two hardening fixes pushed
- 🧪 Tests: 45 pytest passed; health check OK on Back4app
- 📁 Files: app/ingest.py, static/js/app.js
- 🔁 Next prompts: user logs in to SnapDeploy
- 🧠 Reflection: read the plan's footnotes (here, "URL expires") before creating the app

## Evaluation notes (flywheel)

- Failure modes observed: Back4app free URL expires after 60 min
- Graders run and results (PASS/FAIL): pytest PASS; health PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): none
