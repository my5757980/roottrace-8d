# Quickstart: RootTrace 8D

## 1. Run locally (mock mode, no key needed)

```bash
python -m venv .venv && . .venv/Scripts/activate      # Windows Git Bash (macOS/Linux: .venv/bin/activate)
pip install -r requirements-dev.txt
python scripts/generate_sample_case.py                 # writes sample_case/* (seeded, reproducible)
pytest -q                                              # all tests must pass
uvicorn app.main:app --port 7860
```

Open http://localhost:7860 and press **Analyze**. Without a key the header shows
**MOCK (not AMD)**.

## 2. Connect AMD inference (live mode)

Copy `.env.example` to `.env` and fill in the values:

| Variable | Example | Notes |
|----------|---------|-------|
| `AMD_LLM_BASE_URL` | `https://<tokenfactory-host>/v1` | From notebooks.amd.com/tokenfactory, or `http://<droplet-ip>:8000/v1` for vLLM on MI300X |
| `AMD_LLM_API_KEY` | `...` | Never commit it |
| `AMD_TEXT_MODEL` | an ID listed by `GET /v1/models` | Text steps |
| `AMD_VISION_MODEL` | a vision-capable ID (Gemma preferred) | Vision step |
| `AMD_VISION_BASE_URL` / `AMD_VISION_API_KEY` | optional | A different AMD endpoint for vision |
| `AMD_PROVIDER_LABEL` | `AMD TokenFactory · AMD Instinct GPU` | Shown in the AI trace and must be truthful |

Verify the endpoint:

```bash
curl -s "$AMD_LLM_BASE_URL/models" -H "Authorization: Bearer $AMD_LLM_API_KEY"
```

## 3. Record the cached AMD run (once, before the demo goes public)

```bash
python -m app.tools.record_sample_run          # writes sample_case/cached_run.json
```

The run must finish with every step `ok` and `untraceable_numbers` empty. If either check fails,
re-run it.

## 4. Docker

```bash
docker build -t roottrace-8d .
docker run --rm -p 7860:7860 --env-file .env roottrace-8d
```

## 5. Deploy (Hugging Face Space, Docker SDK)

1. Create a Space with the Docker SDK.
2. Push this repo to the Space.
3. Add `AMD_LLM_API_KEY` as a **secret**, and add the other `AMD_*` values as variables.
4. Open the Space URL, run the sample case, and confirm the trace shows **live** AMD steps.

## 6. Acceptance walk-through (golden path)

1. On first load, the sample case inputs are visible, there is no login, and the AMD badge shows
   the provider and models.
2. Press **Analyze**. The 8 steps progress, and the run finishes in 120 s or less.
3. The control chart shows the limits, the violations and the shift at about 2026-10-08 14:20.
   D3 lists the suspect lots from L261008-B onward.
4. The hypotheses are ranked. The top one is Machine or Method (the tool-change offset), and the
   coolant hypothesis shows contradicting timing evidence.
5. The trace table has one row per AI step, with model, live/cached, latency and tokens.
6. Approve D1 to D4, then open **Printable report**. D5 to D8 show DRAFT, and the header shows
   4/8 approved.
7. Stop the network or invalidate the key, then press **Analyze**. The results come back as
   **cached AMD run** in 5 s or less.
