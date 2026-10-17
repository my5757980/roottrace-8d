---
id: 2
title: Clarify question in simple words
stage: general
date: 2026-10-16
surface: agent
model: claude-opus-5-5
feature: none
branch: none
user: ASFAR
command: none (free-form prompt)
labels: ["clarification", "communication", "idea-selection"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - none
tests:
 - none
---

## Prompt

samjaa nahiii kiaaa pochaaa haiiii

## Response snapshot

Re-explained in plain Roman Urdu: a short hackathon summary, then the only two things needed from the user. (1) Which of 3 simply described project ideas to build. Idea 1, the factory quality-complaint report helper, is recommended. (2) Whether they already have the AMD TokenFactory API key. Gave a one-line reply format ("1, haan") and a default: if they just run /sp.constitution, Idea 1 is used.

## Outcome

- ✅ Impact: Decision request made understandable. The project can proceed on reply or by default
- 🧪 Tests: none
- 📁 Files: none
- 🔁 Next prompts: user replies with idea number + key status, or runs /sp.constitution
- 🧠 Reflection: Keep decision prompts jargon-free with everyday examples. Saved as feedback memory

## Evaluation notes (flywheel)

- Failure modes observed: Previous question used domain jargon (8D, SPC, PHI, Croston) without explanation
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): plain numbered options with a default action
