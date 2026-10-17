# RootTrace 8D

**Turns a customer quality complaint into an evidence-backed 8D report draft in minutes, with AI running on AMD.**

Entry for the **AMD Developer Hackathon: ACT III** (lablab.ai), Track 1: *Intelligent Industry*.

- **Live demo:** _<add the Hugging Face Space URL here>_
- **Video:** _<add link>_
- **Slides:** _<add link>_

---

## The problem

An automotive customer rejects 37 housings because the bearing bore is oversize, and asks the
supplier for containment within 24 hours and an 8D report soon after. The supplier's quality
engineer now has to:

- collect the complaint email, the photos, two weeks of SPC measurements and the maintenance log
- find when the process changed and why
- decide which lots to quarantine
- write eight report sections from scratch

That usually takes **hours to days**. The containment decision is often a guess: the lots the
customer named, not the lots the data shows are suspect.

## What RootTrace 8D does

One click on a complaint case runs eight steps:

| # | Step | Who does it |
|---|------|-------------|
| 1 | Read the case inputs (complaint, photos, process CSV, maintenance log) | deterministic |
| 2 | **Statistical process control**: I-MR control limits, Western Electric rules 1–4, Cp/Cpk before and after, change-point detection, out-of-spec summary, containment range | **deterministic Python, no AI computes these numbers** |
| 3 | Correlate the shift with the maintenance and shift log (±2 h), plus machine-parameter shifts | deterministic |
| 4 | Extract the complaint facts with verbatim source quotes | **AI on AMD** |
| 5 | Classify the defect photo (vision model) | **AI on AMD** (Gemma preferred) |
| 6 | Rank root-cause hypotheses across the 6M, each citing evidence IDs, with contradicting evidence | **AI on AMD** |
| 7 | Draft the 8D report D1–D8, with D3 containment fixed to the computed suspect lots | **AI on AMD** |
| 8 | Check every number in the draft against the evidence and flag anything untraceable | deterministic |

The engineer then **edits and approves each section** and opens a printable report (save as PDF).
Unapproved sections are watermarked **DRAFT**. The AI writes the draft and the engineer signs it.

**On the sample case**, the complaint names 2 lots. The SPC shows the bore stepped up by
+0.0133 mm at **2026-10-08 14:30**, which is 10 minutes after a logged boring-bar change whose
first-piece check was "visual only". RootTrace 8D therefore tells the engineer to contain
**11 lots**, not 2. The other 9 are still at the plant or in transit.

### Trust by design

- **Evidence registry:** every fact the AI can use has an ID (`S4`, `L6`, `P2`, `C3`, `I1`, …).
  Hypotheses and sections must cite these IDs, and the server drops any invented IDs.
- **Numbers are computed, never generated:** a number-trace check flags any number in the AI
  narrative that does not match a computed value or an input record.
- **Uncertainty is visible:** each claim carries a high, medium or low confidence, unsupported
  hypotheses are marked, and contradicting evidence is shown.
- **Human approval:** each section moves through AI draft → edited → approved, and an edit after
  approval sets it back to needs re-approval.

## How AMD is used

All AI inference runs on **AMD infrastructure** through one OpenAI-compatible client
(`app/llm/client.py`). You can point it at either backend:

- **AMD TokenFactory API**, the event's hosted inference on AMD Instinct GPUs
  (`notebooks.amd.com/tokenfactory`), or
- **your own vLLM server on AMD Developer Cloud (Instinct MI300X, ROCm)**:
  `vllm serve <model> --api-key …`, base URL `http://<droplet-ip>:8000/v1`.

The vision step can use a separate AMD endpoint and model, for example **Gemma** served with vLLM
on MI300X. Every AI step is recorded in the **AMD inference trace** that the UI shows: provider,
model, live or cached, latency, tokens in and out, and attempts.

The client respects the AMD gateway's limits:

- a concurrency semaphore of 8 and a 20 requests/min sliding window
- `Retry-After` honored on 429
- exponential backoff with jitter on 5xx
- only the accepted request fields are sent

A **recorded AMD run** of the sample case (`sample_case/cached_run.json`) is served per step, and
clearly labeled, if live capacity runs out while many judges try the demo at once.

## Architecture

```text
Browser (vanilla JS, SVG chart, print CSS)
   │  REST + polling (/api/...)
   ▼
FastAPI app (one container)
   ├── ingest.py      parse + validate CSV / log / images / .eml
   ├── spc.py         I-MR limits, WE rules, Cp/Cpk, change point, containment
   ├── correlate.py   log events around the shift
   ├── evidence.py    evidence registry with citation IDs
   ├── pipeline.py    8-step orchestration, cached fallback, AI trace
   ├── numbers.py     number-trace check
   ├── report.py      8D sections + approval state machine
   └── llm/client.py ──► AMD TokenFactory  or  vLLM on AMD Instinct MI300X (ROCm)
```

There is no database. Cases live in memory with a 2 h TTL, and uploads are never stored.

## Quickstart

```bash
python -m venv .venv
. .venv/Scripts/activate            # Windows Git Bash; on macOS/Linux: . .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/generate_sample_case.py   # (re)creates sample_case/* (seeded)
pytest -q                                # 44 tests
uvicorn app.main:app --port 7860         # open http://localhost:7860
```

Without an AMD key the app runs in **mock mode** (clearly labeled *MOCK (not AMD)*) so the UI
works end to end. To run live on AMD, copy `.env.example` to `.env` and set:

| Variable | Meaning |
|----------|---------|
| `AMD_LLM_BASE_URL` | TokenFactory base URL, or `http://<droplet-ip>:8000/v1` for vLLM on MI300X |
| `AMD_LLM_API_KEY` | API key (never commit it) |
| `AMD_TEXT_MODEL` | model ID from `GET <base>/models` |
| `AMD_VISION_MODEL` | vision-capable model ID (Gemma preferred) |
| `AMD_VISION_BASE_URL`, `AMD_VISION_API_KEY` | optional separate AMD endpoint for vision |
| `AMD_PROVIDER_LABEL` | the label shown in the trace, for example `AMD TokenFactory · AMD Instinct GPU` |
| `LLM_REASONING_EFFORT` | optional (`low` recommended for reasoning models) |

Then record the cached AMD run once:

```bash
python -m app.tools.record_sample_run     # writes sample_case/cached_run.json after checks pass
```

### Docker / Hugging Face Space

```bash
docker build -t roottrace-8d .
docker run --rm -p 7860:7860 --env-file .env roottrace-8d
```

For a Hugging Face Space:

1. Create a Space with the **Docker** SDK.
2. Push this repository to it.
3. Add `AMD_LLM_API_KEY` as a secret, and the other `AMD_*` values as variables.

The container listens on port 7860.

## API

The OpenAPI contract is in `specs/001-roottrace-8d/contracts/openapi.yaml`, and the live docs are
at `/api/docs`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | mode (live or mock), provider, models, cached-run status |
| POST | `/api/cases/sample` | create a case from the bundled sample |
| POST | `/api/cases` | create a custom case (multipart upload) |
| POST | `/api/cases/{id}/analyze` | start a run (`live`, or `cached` for the sample) |
| GET | `/api/cases/{id}/analysis` | poll steps, results, report and trace |
| PATCH | `/api/cases/{id}/report/sections/{D1-D8}` | edit, approve or unapprove a section |

## Business case (summary)

- **User:** supplier quality engineers at automotive and industrial component suppliers
  (IATF 16949 environments). In the same company the buyers are quality managers and plant
  managers.
- **Value:** less time to containment and to a first 8D draft. Containment is based on data
  (suspect lots from SPC) rather than on the lots the customer happened to name. Every report
  is consistent and evidence-cited.
- **Model:** SaaS priced per plant per month, with an on-premises option that runs on the
  customer's own AMD Instinct or Ryzen AI hardware.
- **Next steps:** QMS and MES connectors (SPC data feeds), multi-characteristic analysis, and
  supplier-portal export formats.

## Spec-Driven Development

This project was built with SDD:
- constitution: `.specify/memory/constitution.md`
- spec, plan, research, data model, contracts, tasks: `specs/001-roottrace-8d/`
- prompt history: `history/prompts/`
- the hackathon requirements this was built against: `docs/hackathon/HACKATHON_BRIEF.md`

## License

MIT (see `LICENSE`). The sample case data, the photo, the companies and the people are
fictional and self-generated. AI output is a draft for engineer review, never a final quality
decision.
