# Research: RootTrace 8D

Phase 0 decisions. The external facts come from `docs/hackathon/HACKATHON_BRIEF.md` (scanned
2026-10-16). No NEEDS CLARIFICATION items remain.

## R1. Inference provider on AMD

- **Decision**: a single OpenAI-compatible chat-completions client, configured by environment
  variables. Default target: the **AMD TokenFactory** API (the event FAQ says "just the API from
  the tokenfactory"). Optional target: **vLLM on AMD Developer Cloud MI300X**
  (`http://<droplet-ip>:8000/v1`, started with `--api-key`). Each role (text, vision) can override
  the base URL, key and model, so the vision step can run Gemma on a different AMD endpoint.
- **Rationale**: the global TokenFactory base URL and model catalog are only visible after login.
  Making them configurable means no code change when they turn out to be different. The vLLM
  OpenAI server exposes the same API.
- **Alternatives considered**:
  - Provider SDKs: they add dependencies and may send fields the gateway drops.
  - Fireworks: not guaranteed to count as AMD hardware for judging.
  - Evolus: out of scope.

## R2. Request shape and gateway compatibility

- **Decision**: send only `model`, `messages`, `temperature`, `max_tokens`, `response_format`
  (`json_object`) and, optionally, `reasoning_effort`, which is sent only when the env value is
  set. Images go in as OpenAI `image_url` data URLs (JPEG, longest side 1024 px or less). Replies
  are parsed with a tolerant JSON extractor that strips code fences and takes the first balanced
  object, then validated with Pydantic. Invalid output gets one retry with the validation error
  appended.
- **Rationale**: the gateway documentation lists exactly these fields and drops the rest. Some
  models return reasoning separately or wrap JSON in fences, and the tolerant parser handles
  both.
- **Alternatives considered**:
  - Tool calling for structured output: support varies by model and parser.
  - Strict `json_schema`: only one model in the reference catalog supports it.

## R3. Rate limits and resilience

- **Decision**: an asyncio semaphore (8), a sliding 60-second RPM limiter (default 20), a 90 s
  timeout per request and up to 3 attempts. The client honors `Retry-After` on 429 and 503, uses
  exponential backoff with full jitter otherwise, and does not retry 4xx errors other than 429.
  Each step falls back to the cached AMD run for the sample case.
- **Rationale**: the reference limits are 20 RPM per account and 8 concurrent requests per key.
  During judging many visitors share one key, so the per-step cache keeps the golden path green.
- **Alternatives considered**: a global queue that serializes all analyses. It is simpler, but a
  queue of judges would see long waits.

## R4. Progress delivery: polling instead of SSE

- **Decision**: `POST /api/cases/{id}/analyze` starts a background asyncio task. The UI polls
  `GET /api/cases/{id}/analysis` every 800 ms and renders steps as their status changes.
- **Rationale**: reverse proxies (including hosted Spaces) can buffer SSE, and polling works
  everywhere. It is also trivial to test, and with 8 steps the extra latency does not matter.
- **Alternatives considered**: SSE (risk of proxy buffering) and WebSockets (more moving parts).

## R5. SPC methods (deterministic)

- **Decision**:
  - **Individuals (I-MR) chart**: CL is the baseline mean, σ̂ = MR̄ / 1.128, UCL/LCL = CL ± 3σ̂,
    with zones at 1σ and 2σ.
  - **Western Electric rules**:
    - Rule 1: 1 point beyond 3σ.
    - Rule 2: 2 of 3 consecutive points beyond 2σ on the same side.
    - Rule 3: 4 of 5 consecutive points beyond 1σ on the same side.
    - Rule 4: 8 consecutive points on one side of the CL.
  - **Capability**:
    - Cp = (USL − LSL) / 6σ̂.
    - Cpk = min(USL − μ, μ − LSL) / 3σ̂.
    - μ and σ̂ come from the moving range of each window (baseline and after the shift).
  - **Change point**: single mean-shift binary split that maximizes
    k(n − k)/n · (x̄₁ − x̄₂)², with segments of at least 10 points. It counts as significant when
    the Welch t statistic is above 5 and |Δμ| ≥ 1σ̂.
  - **Baseline**: the first 25% of points (between 20 and 200), unless the case sets
    `baseline_end`.
  - **Containment start**: the last sample before the change point, i.e. the last known-good
    point.
- **Rationale**: these are textbook methods that quality engineers recognise, with no SciPy
  dependency, and a one-line explanation can be shown for each.
- **Alternatives considered**:
  - CUSUM or EWMA: better for detecting small shifts, but harder to explain in one line.
  - PELT multiple change points: overkill for the MVP.

## R6. Machine parameters and event correlation

- **Decision**:
  - Run the same change-point test on each numeric machine-parameter column and report the mean
    before and after the measurement change point.
  - Correlate maintenance and shift-log events within ±2 h of the change point, sorted by |Δt|.
  - Every result becomes evidence in the registry (`P*` and `L*` IDs).
- **Rationale**: this gives the AI concrete supporting and contradicting evidence. For example,
  a coolant dip 31 h after the shift counts against the coolant hypothesis.

## R7. Evidence registry and number tracing

- **Decision**:
  - The evidence registry assigns IDs to the facts the AI can see: `C*` complaint quotes,
    `I*` image observations, `S*` SPC facts, `P*` parameter facts and `L*` log entries.
  - Prompts list the evidence as `[ID] text`.
  - The server drops cited IDs that do not exist and marks the claim "unsupported".
  - The number trace extracts numbers that stand alone as tokens (so `D3`, `8D` and `5W2H` are
    skipped) from each section. It compares them with the numbers present in the evidence texts,
    at the same rounding. Integers of 12 or less and years are ignored, and anything left is
    flagged.
- **Rationale**: this enforces Principles III and IV mechanically and cheaply.

## R8. Frontend

- **Decision**: vanilla ES modules with no build step, and a hand-rolled **SVG control chart**
  (no chart library). Series larger than 3,000 points are downsampled by stride, while rule
  violations always stay visible. The printable report is a separate `report.html` that fetches
  the case JSON and uses print CSS, with a DRAFT watermark on unapproved sections.
- **Rationale**: no CDN or library risk, SVG prints crisply in a PDF, and it is fast to build.
- **Alternatives considered**:
  - Chart.js: a canvas does not print as well and adds a dependency.
  - React or Vite: needs a build step.
  - Streamlit: looks generic and gives less control.

## R9. Hosting

- **Decision**: one Docker image (python:3.12-slim) that runs uvicorn on `$PORT` (default 7860).
  The primary host is a Hugging Face Space (Docker SDK) with the API key stored as a Space
  secret. Fallbacks are any container host, or the AMD Developer Cloud droplet itself.
- **Rationale**: free, public, and no cold start within the judging window. Secrets are
  supported. One container also satisfies the "containerized app" norm.

## R10. Sample case design (synthetic, seeded)

- **Decision**: a fictional customer, *Ardena Motors S.p.A.*, and a fictional supplier
  part **AH-2207 water-pump housing**.
  - **Characteristic**: bore Ø42.000 mm, LSL 42.000, USL 42.025, target 42.0125.
  - **Data**: 14 days of samples every 30 minutes (672 rows) on machine `CNC-07`, with three
    shifts and one lot per shift (`L261008-B`, ...), and columns for spindle temperature,
    coolant concentration, tool ID and tool life.
  - **Baseline**: σ about 0.0022 mm.
  - **Injected story**: a tool change on **2026-10-08 14:20** (BB-17 → BB-18) carries an offset
    error of +0.0085 mm, followed by a wear drift of +0.00012 mm/h. The out-of-spec parts start
    within hours of the change. There is also a coolant top-up dip on 2026-10-09 22:10, which is
    a distractor, and spindle temperature stays stable.
  - **Log**: records the tool change, a first-piece check done "visually only, CMM busy", and a
    shift handover note that ignored warning points.
  - **Complaint**: names 2 lots (L261008-B and L261009-A), while SPC shows more suspect lots,
    which is the containment insight.
  - **Photo**: a procedurally rendered bore with chatter marks and a reject tag.
- **Rationale**: realistic, self-made and MIT-safe (no third-party images), and it exercises
  every step and every edge in the evidence chain.
