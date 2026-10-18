---
id: 13
title: AMD key redeemed and live run
stage: green
date: 2026-10-18
surface: agent
model: claude-opus-5-5
feature: 001-roottrace-8d
branch: 001-roottrace-8d
user: ASFAR
command: none (free-form prompt)
labels: ["amd-tokenfactory", "gemma", "live-run", "cached-run", "resilience"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - .env (local only, gitignored)
 - app/config.py
 - app/pipeline.py
 - app/llm/prompts.py
 - static/js/render.js
 - static/js/report.js
 - .env.example
 - sample_case/cached_run.json
 - README.md
 - docs/submission/* (wording, cover, slides PDF)
 - specs/001-roottrace-8d/tasks.md
tests:
 - pytest: 45 passed
 - live AMD API probe: /models 200; Gemma text JSON ok; DeepSeek vision ok; Gemma vision 500 (provider OOM)
 - record_sample_run: clean recording 2026-10-18T04:03:43Z, all numbers traced
 - live analysis through the app API: all AI steps live, 0 untraceable numbers
---

## Prompt

karooo ab check dubaracontinue

## Response snapshot

TokenFactory now showed team-1341 (1 member). I redeemed the key in the Playwright browser and saved it to a gitignored file without printing it. I wrote .env with:
- base URL https://developer.amd.com.cn/radeon/api/v1
- text model Gemma-4-31B-IT
- vision model DeepSeek-V4-Flash-Vision-Exp (Gemma's vision request returned 500 because the provider ran out of GPU memory)
- fast model DeepSeek-V4-Flash, used for the 8D draft

Rate limits are 20 RPM and $1/day per key.

Code changes:
- an optional fast model role
- a sample-case live step budget that falls back to the cached run, with a label
- a stricter no-new-numbers rule in the prompt
- relative deadline extraction
- the provider prefix is stripped from displayed model names

Recording runs: the number-trace check rejected two runs because they contained invented numbers. The third run was clean and was committed. Hardware wording is now precise ("AMD GPUs via AMD Token Factory"), and the cover and slides were regenerated. The cron job was deleted.

## Outcome

- ✅ Impact: The project runs live on AMD (Gemma 4 + DeepSeek), and a verified cached AMD run is committed
- 🧪 Tests: 45 pass; live probes and recordings as listed above
- 📁 Files: see the list above (.env is not committed)
- 🔁 Next prompts: GitHub public repo + push; Hugging Face Space deploy with secrets; demo video; lablab submission before 2026-10-18 10:00 UTC
- 🧠 Reflection: The number-trace guardrail caught real invented numbers in live drafts, which is good evidence for the trust story in the pitch

## Evaluation notes (flywheel)

- Failure modes observed: shared-endpoint latency is highly variable (draft 33–169 s); Gemma image input hit a provider OOM; the DeepSeek draft invented numbers until the prompt was tightened
- Graders run and results (PASS/FAIL): record_sample_run checks PASS on the 3rd run; pytest PASS
- Prompt variant (if applicable): draft rule (3) tightened
- Next experiment (smallest change to try): none before the deadline
