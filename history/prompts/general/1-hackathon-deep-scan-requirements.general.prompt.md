---
id: 1
title: Hackathon deep scan requirements
stage: general
date: 2026-10-16
surface: agent
model: claude-opus-5-5
feature: none
branch: none
user: ASFAR
command: none (free-form prompt)
labels: ["hackathon", "research", "requirements", "amd", "lablab"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - docs/hackathon/HACKATHON_BRIEF.md
tests:
 - none
---

## Prompt

https://lablab.ai/ai-hackathone/amd-developer-hackathone-act-iii        claude is link par jaooo full scan karooo is kooo ya aik hackathone haiiii full deeplyy dekhoo full scan karoo kia requirement haiiii sab kuch kuch bhii miss mat karnaaaa phir ya hackathonee banayaa gayyyy spec drven development sayyy constitution specify plan tasks implemented tum full dekh loo samajlooo phir mayy tum koo aik aik kar kayyy command duu gaaa constitution specify plan tasks implemented tum khudiiii phlayy constitution likhnaaa phir specify phir plan phir tasks phir implemented kar denaa specs kayy mutabiq poora project shuruuuu karooooo

## Response snapshot

The given URL returns 404 because of typos. The canonical event page is https://lablab.ai/event/amd-developer-hackathon-act-iii. A deep scan covered the raw page HTML and RSC payload (timeline, judges, speakers), the live dashboard (stats, competing submissions), the lablab Rule Book (1 to 5 judging rubric), the Submission Guide (exact field limits), the Hackathon Guidelines, the How-to-Win guide, Terms §16–17 (MIT, original, open source, prize payout), the Evolus developer docs (APIs, limits), the AMD TokenFactory portal and the Radeon Cloud docs (OpenAI-compatible gateway, rate limits), and the AMD Developer Cloud vLLM tutorial.

Everything is captured in docs/hackathon/HACKATHON_BRIEF.md. Key findings:
- Deadline: Sun 18 Oct 2026, 10:00 UTC (12:00 CEST, 15:00 PKT), with a timeline "End" marker at 17 Oct 17:00 UTC used as the internal stop.
- AMD is mandatory, and judges must see it in the working product. TokenFactory API is enough.
- Four tracks plus the Evolus partner track. Gemma use qualifies for the Google $5k prize.
- Required: public MIT repo, live demo URL, 3 to 5 min video, PDF slides.

Three project ideas were proposed, with "8D Quality Copilot" (Track 1) recommended. The structured question dialog was rejected by the user.

## Outcome

- ✅ Impact: Complete hackathon requirements captured as the source of truth for the SDD phases
- 🧪 Tests: none (research only)
- 📁 Files: docs/hackathon/HACKATHON_BRIEF.md
- 🔁 Next prompts: user picks the idea, then /sp.constitution → /sp.specify → /sp.plan → /sp.tasks → /sp.implement
- 🧠 Reflection: WebFetch summaries were lossy. Raw HTML/RSC parsing found the exact deadline, schedule and rubric that the summaries missed.

## Evaluation notes (flywheel)

- Failure modes observed: User URL had typos (404). The global TokenFactory base URL is not public. The question dialog was too jargon-heavy for the user.
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): ask decisions as plain numbered Roman Urdu options
