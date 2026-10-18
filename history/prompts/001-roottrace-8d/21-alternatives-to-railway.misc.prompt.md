---
id: 21
title: Alternatives to Railway
stage: misc
date: 2026-10-18
surface: agent
model: claude-opus-5-5
feature: 001-roottrace-8d
branch: 001-roottrace-8d
user: ASFAR
command: none (free-form prompt)
labels: ["deploy", "hosting", "back4app"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - none
tests:
 - none
---

## Prompt

railwayyy kayyy elawaaa batoooo

## Response snapshot

- **Hugging Face:** the earlier 402 error said Gradio Spaces are PRO-only too, so it stays out.
- **Koyeb:** sources say it now needs a card.
- **Back4app Containers:** free with no card, 0.25 vCPU, 256 MB. Measured local memory was about 175 MB. Opened its login page for the user.

## Outcome

- ✅ Impact: picked a host that needs no card and keeps the live backend
- 🧪 Tests: memory check of the running server (175 MB private)
- 📁 Files: none
- 🔁 Next prompts: user logs in with GitHub
- 🧠 Reflection: the free-tier terms (such as URL lifetime) only showed up after creating the app

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): none
