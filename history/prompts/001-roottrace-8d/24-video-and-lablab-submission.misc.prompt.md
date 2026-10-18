---
id: 24
title: Video and lablab submission
stage: misc
date: 2026-10-18
surface: agent
model: claude-opus-5-5
feature: 001-roottrace-8d
branch: 001-roottrace-8d
user: ASFAR
command: none (free-form prompt)
labels: ["video", "submission", "lablab", "release"]
links:
  spec: specs/001-roottrace-8d/spec.md
  ticket: null
  adr: null
  pr: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii/roottrace-8d/roottrace-8d-complaint-to-8d-report-on-amd
files:
 - README.md
 - docs/submission/REQUIREMENTS_CHECKLIST.md
 - .gitignore
tests:
 - final MP4 probe: 4:11, 1920x1080 H.264 + AAC, 12.4 MB, audio mean -20.6 dB
 - live AMD run recorded on the deployed app finished in 92 s
 - lablab showed "You have successfully submitted your project"; submission page shows video, GitHub, slides PDF and demo link
---

## Prompt

haaaaaaaaa ab sab cheezayyy reay karooo or hackathone submit karooooooo

## Response snapshot

- **Narration:** 15 English clips made with edge-tts (`en-US-AndrewNeural`), 222 s in total. The script follows the rubric: problem, live demo, business, competition, roadmap.
- **Slides:** rendered to 1920×1080 PNGs with headless Chrome.
- **Demo recording:** a CDP screencast of the deployed SnapDeploy app, with a scripted cursor and captions.
  - The first attempt clicked an off-screen button, so no analysis ran. Fixed by scrolling elements into view before clicking.
  - The second run finished live on AMD in 92 s. The wait was sped up ×8.2 and labelled.
- **Assembly:** ffmpeg (imageio-ffmpeg) produced `docs/submission/RootTrace8D_demo.mp4` (gitignored): 4:11, 1080p, 12.4 MB.
- **lablab form, step 1:** title, short and long text, Online, categories (Automotive, Business, Productivity), track Intelligent Industry, technologies (Token Factory, AMD Developer Cloud, AMD ROCm, Gemma).
- **Step 2:** cover, video and slides PDF.
- **Step 3:** GitHub URL, platform Other, demo URL and additional info. Then submitted, at about 06:38 UTC.
- **Docs:** README now links the submission page, and the checklist is marked as submitted.

## Outcome

- ✅ Impact: the hackathon entry is submitted with every required item, 3h20m before the deadline
- 🧪 Tests: video probe OK; live run OK; submission page verified
- 📁 Files: README.md, docs/submission/REQUIREMENTS_CHECKLIST.md, .gitignore
- 🔁 Next prompts: optional cleanup (delete the expired Back4app app that stores the key); watch judging
- 🧠 Reflection: a scripted screencast plus TTS gives a repeatable, honest video in under an hour; always scroll targets into view before synthetic clicks

## Evaluation notes (flywheel)

- Failure modes observed: synthetic click on an off-screen element silently did nothing
- Graders run and results (PASS/FAIL): video probe PASS; submission PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): assert that a run started right after the click
