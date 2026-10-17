---
id: 3
title: Short summary request
stage: general
date: 2026-10-16
surface: agent
model: claude-opus-5-5
feature: none
branch: none
user: ASFAR
command: none (free-form prompt)
labels: ["clarification", "communication", "brevity"]
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

short mayy batooo kiaa bol rahayyy haooooo

## Response snapshot

A 3-line Roman Urdu summary: the scan is done (deadline 18 Oct, 3 PM PKT, and AMD API use is required). Asked the user to pick a project by number (1 = factory complaint helper, the recommendation; 2 = hospital paperwork; 3 = shop stock). If they just run /sp.constitution, idea 1 is used.

## Outcome

- ✅ Impact: The decision request is reduced to a single number reply
- 🧪 Tests: none
- 📁 Files: none
- 🔁 Next prompts: user replies 1, 2 or 3, or runs /sp.constitution
- 🧠 Reflection: The user wants very short replies. Saved to feedback memory

## Evaluation notes (flywheel)

- Failure modes observed: The previous reply was too long for the user
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): keep replies to 3–5 lines
