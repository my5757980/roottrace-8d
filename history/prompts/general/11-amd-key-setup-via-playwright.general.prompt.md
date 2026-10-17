---
id: 11
title: AMD key setup via Playwright
stage: general
date: 2026-10-17
surface: agent
model: claude-opus-5-5
feature: none
branch: 001-roottrace-8d
user: ASFAR
command: none (free-form prompt)
labels: ["amd-tokenfactory", "api-key", "playwright", "lablab", "registration"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - .gitignore (added .playwright-mcp/)
 - .dockerignore (added .playwright-mcp/)
tests:
 - none
---

## Prompt

playwrite connected haiii ya walaa kaam tum khud karoooo or project koo 1oo% readyyy karooo 1. AMD key: .env file mein daal kar mujhe batayein. Iske baghair app AMD par nahi chalegi.

(follow-up: "login kar diaaa haiii mannayyyy")

(follow-up: "nahiii mujayy team nahii banannii haii mayy hamesaha soloo hi kartaa huuuu")

## Response snapshot

1. Opened notebooks.amd.com/tokenfactory in the Playwright browser, and the user signed in with their own AMD account.
2. The Token Factory page said "Your email is not registered for API key distribution". Its rules require a team registered on the ACT III lablab page, even for a solo member.
3. On lablab the user is already logged in and enrolled. The "Submit Project" link points to an undefined team slug, which confirms a team is needed for submission too.
4. The user does not want a team because they always work solo.
5. Explained that a lablab "team" can be the user alone (1 member, closed), and asked for permission before creating it. No team was created.
6. Added `.playwright-mcp/` to the ignore files so page artifacts are never committed.

## Outcome

- ✅ Impact: Found the real blocker for the AMD key: the lablab team registration
- 🧪 Tests: none
- 📁 Files: .gitignore, .dockerignore
- 🔁 Next prompts: user approves a 1-member team → create it → wait for the key sync → put the key in .env → record the cached run
- 🧠 Reflection: An outward action on the user's account (creating a team) needs consent, and the user's explicit "no" must be respected and clarified, not overridden

## Evaluation notes (flywheel)

- Failure modes observed: the cookie and onsite-preference dialogs intercepted clicks; the "team" concept was misunderstood as needing other people
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): ask for consent with a clear explanation that a solo team has 1 member
