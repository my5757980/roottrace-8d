# RootTrace 8D: hackathon requirements compliance check

Checked on 2026-10-18 at 04:15 UTC. I re-scanned the live event page and confirmed it has not
changed since the first scan, and I read the logged-in submission form (step 1 of 3).

**Deadline:** 2026-10-18 10:00 UTC = **15:00 PKT** (event `endAt`, plus a 5-minute grace period).

Legend: ✅ done and verified · ⏳ to do before the deadline

## 1. Eligibility and registration

| Requirement | Status | Evidence |
|---|---|---|
| lablab account, enrolled and approved | ✅ | The event page shows "Enrolled" |
| AMD AI Developer Program member | ✅ | AMD SSO login works; Token Factory access is granted |
| lablab Discord joined and connected | ✅ | Profile shows Discord "Connected"; joined the server |
| Team registered (solo team allowed) | ✅ | lablab team "RootTrace 8D" (closed, 1 member); Token Factory team-1341 |
| Participation mode | ✅ | Online (select it in the form) |

## 2. Technology requirement

| Requirement | Status | Evidence |
|---|---|---|
| AMD powers a meaningful part of the workload | ✅ | All 4 AI steps run on **AMD Token Factory** (AMD GPUs); the organizer confirmed "tokenfactory will satisfy" |
| AMD is visible in the working product shown to judges | ✅ | The header badge and the AMD inference trace (provider, model, latency, tokens) are shown in the UI and the report |
| Gemma (Google prize) | ✅ | **Gemma-4-31B-IT** runs the complaint facts and the root-cause hypotheses |

## 3. Track 1: Intelligent Industry brief

| "Good projects will show" | Status | Evidence |
|---|---|---|
| A real manufacturing problem | ✅ | A customer complaint leads to an 8D and containment, the daily work of supplier quality engineers |
| Processes realistic industrial data and produces an alert, explanation, recommendation or action | ✅ | 672 SPC samples, a machine-parameter CSV and a maintenance log produce a shift alert, a root-cause explanation, a containment action and an 8D |
| Clear about who uses it and what it improves | ✅ | Supplier quality engineer; the time to containment and to the first 8D draft is shown as a KPI |
| A working product, not just a dashboard | ✅ | End to end: analyze, review, approve, print to PDF; custom-case upload |
| Results operators understand | ✅ | Plain-language "How it's computed", evidence chips, confidence levels |
| Measurable improvement | ✅ | First draft in about 2 minutes (versus days); 11 suspect lots found where the customer named 2 |

## 4. Submission package (lablab form)

| Field | Status | Value or file |
|---|---|---|
| Title (5–50) | ✅ | "RootTrace 8D: Complaint to 8D Report on AMD" (43) |
| Short description (50–255) | ✅ | 226 characters (`SUBMISSION.md`) |
| Long description (600–2000, ≥100 words) | ✅ | 1,363 characters, 222 words |
| Categories / Event track / Technologies | ⏳ | Choose in the form: track **Intelligent Industry**; technologies AMD, Gemma, DeepSeek, Python, FastAPI, Docker |
| Cover image (16:9) | ✅ | `docs/submission/cover.png` (1920×1080) |
| Slide presentation (PDF) | ✅ | `docs/submission/RootTrace8D_slides.pdf` (10 slides: problem, user, solution, demo, AMD, trust, market, competition, roadmap) |
| Video presentation (MP4/MOV, ≤300 MB, 3–5 min) | ⏳ | Script ready: `docs/submission/VIDEO_SCRIPT.md` |
| Public GitHub repository | ⏳ | 9+ local commits ready; MIT license; README |
| Demo application platform and URL | ⏳ | Dockerfile ready (Hugging Face Space, Docker SDK) |

## 5. Rules

| Rule | Status | Evidence |
|---|---|---|
| Original, open source, MIT | ✅ | `LICENSE` (MIT); self-generated sample data, photo and companies |
| Containerized app with a README that runs | ✅ | `Dockerfile`, README quickstart (the local Docker build was skipped because the PC was low on memory; Hugging Face builds it) |
| No secrets committed | ✅ | `.env` is gitignored; secret scan is clean |

## 6. Quality and UI

| Check | Status | Evidence |
|---|---|---|
| Automated tests | ✅ | 45 pytest tests pass (SPC rules, capability, change point, number trace, ingest, client limits, golden path) |
| Live AMD analysis in the app | ✅ | All AI steps live; 0 untraceable numbers |
| Recorded AMD run fallback | ✅ | `sample_case/cached_run.json` (2026-10-18 04:03 UTC), labeled "cached AMD run" |
| Responsive from 320 px to 2560 px | ✅ | Headless audit at 320, 375, 414, 768, 1024, 1280, 1440, 1920 and 2560: 0 horizontal overflow and 0 console errors, using the real AMD data |
| Professional UI/UX | ✅ | Design system, icons, stacked tables on phones, sticky mobile action bar, accessible focus states, printable report |

## Remaining before 15:00 PKT

1. Push to a public GitHub repo.
2. Deploy the live demo (Hugging Face Space) with the AMD key as a secret.
3. Record the 3–5 minute demo video (MP4).
4. Fill in and submit the lablab form, then add the demo and video links to the README.
