---
id: 4
title: Ratify RootTrace constitution
stage: constitution
date: 2026-10-17
surface: agent
model: claude-opus-5-5
feature: none
branch: main
user: ASFAR
command: /sp.constitution
labels: ["constitution", "principles", "amd", "hackathon"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
 - .specify/templates/tasks-template.md
tests:
 - none
---

## Prompt

continue

(Executed as /sp.constitution with input: "Project: RootTrace 8D, an entry for the AMD Developer Hackathon ACT III (Track 1: Intelligent Industry). Use docs/hackathon/HACKATHON_BRIEF.md as the source of requirements. Principles: AMD-powered inference visible in the product; deadline-first MVP scope; evidence-cited, human-approved AI output; deterministic statistics for any analytics or prediction; configurable OpenAI-compatible provider with rate-limit resilience and cached golden path; judge-proof public demo (no login, preloaded sample data, containerized); security (no secrets in repo); MIT open source; test the deterministic core; simplicity.")

## Response snapshot

Ratified constitution v1.0.0 with nine principles. I (AMD-Powered, Visibly) and II (Deadline-First Scope) are NON-NEGOTIABLE. The others: III Evidence-Cited, Human-Approved Output · IV Deterministic Analytics · V Resilient, Configurable Inference · VI Test the Deterministic Core · VII Judge-Proof Demo and Delivery · VIII Security and Open Source · IX Simplicity. Added two sections, Hackathon Constraints and Submission Standards and Development Workflow and Quality Gates, plus Governance. The tasks-template note now makes the Principle VI tests mandatory.

## Outcome

- ✅ Impact: Project principles and gates fixed for every later SDD phase
- 🧪 Tests: none
- 📁 Files: .specify/memory/constitution.md, .specify/templates/tasks-template.md
- 🔁 Next prompts: /sp.specify for the RootTrace 8D feature
- 🧠 Reflection: Principles map directly to judging criteria and the brief's derived constraints

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): placeholder scan PASS (no bracket tokens left)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): none
