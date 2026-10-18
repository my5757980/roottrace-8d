---
id: 18
title: Hugging Face deploy attempt
stage: misc
date: 2026-10-18
surface: agent
model: claude-opus-5-5
feature: 001-roottrace-8d
branch: 001-roottrace-8d
user: ASFAR
command: none (free-form prompt)
labels: ["deploy", "hugging-face", "blocked"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - none (scratch deploy script only)
tests:
 - none
---

## Prompt

login kar diaa haii hugging face

## Response snapshot

- Created an HF access token and ran a deploy script that keeps the AMD key out of the output.
- Space creation failed with `402 Payment Required`. HF said: "Static Spaces are free for everyone, but hosting Gradio and Docker Spaces on free cpu-basic requires a PRO subscription."
- Next step: try a different free host.

## Outcome

- ✅ Impact: confirmed that HF cannot host the live backend for free
- 🧪 Tests: none
- 📁 Files: none in the repo
- 🔁 Next prompts: try Render
- 🧠 Reflection: check a host's current free-tier rules before investing in its deploy flow

## Evaluation notes (flywheel)

- Failure modes observed: HF free tier changed (Docker/Gradio now PRO-only)
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): none
