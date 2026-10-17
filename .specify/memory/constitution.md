<!--
SYNC IMPACT REPORT
- Version change: template (unversioned) -> 1.0.0 (initial ratification)
- Principles defined:
  I. AMD-Powered, Visibly (NON-NEGOTIABLE)
  II. Deadline-First Scope (NON-NEGOTIABLE)
  III. Evidence-Cited, Human-Approved Output
  IV. Deterministic Analytics
  V. Resilient, Configurable Inference
  VI. Test the Deterministic Core
  VII. Judge-Proof Demo and Delivery
  VIII. Security and Open Source
  IX. Simplicity
- Added sections: Hackathon Constraints and Submission Standards; Development Workflow and
  Quality Gates; Governance
- Removed sections: none (template placeholders replaced)
- Templates:
  ✅ .specify/templates/plan-template.md (Constitution Check is derived from this file; no edit needed)
  ✅ .specify/templates/spec-template.md (no mandatory-section change needed)
  ✅ .specify/templates/tasks-template.md (tests note updated for Principle VI)
  ✅ CLAUDE.md (already points to this file for code standards)
- Deferred TODOs: none
-->

# RootTrace 8D Constitution

RootTrace 8D is an entry for the AMD Developer Hackathon: ACT III (Track 1: Intelligent
Industry). Event requirements live in `docs/hackathon/HACKATHON_BRIEF.md`. That brief, and the
live event page it cites, are the external source of truth.

## Core Principles

### I. AMD-Powered, Visibly (NON-NEGOTIABLE)

- All LLM and vision-model inference in the judged product MUST be served on AMD
  infrastructure. That means the AMD TokenFactory API (AMD Instinct GPUs) or a vLLM endpoint on
  AMD Developer Cloud (Instinct MI300X, ROCm).
- For every AI step, the UI MUST show the provider, the model ID, the latency and the token
  usage. This "AMD inference trace" makes the AMD component part of the working product that
  judges see.
- A Gemma model SHOULD power at least one meaningful step when the AMD endpoint offers one.
  This makes the entry eligible for the Google prize.
- A non-AMD or mock provider MAY exist only for local development and tests. It MUST be
  labeled as such in the UI, and the public demo MUST NOT use it.

Rationale: AMD is mandatory for prize eligibility, and judges must see it working.

### II. Deadline-First Scope (NON-NEGOTIABLE)

- Internal hard stop: **2026-10-17 17:00 UTC**. Official deadline: **2026-10-18 10:00 UTC**,
  plus a 5-minute grace period.
- Build order is fixed. First the golden path works end to end, then it is deployed publicly,
  then it is polished. Anything off the golden path waits until the P1 story ships.
- After the spec is ratified there is no pivot. When time runs short, scope is cut; late
  features are not added.
- Features freeze at least 3 hours before the internal hard stop. The remaining time goes to
  the video, slides and submission.

Rationale: an unfinished or unreachable demo scores as "not working".

### III. Evidence-Cited, Human-Approved Output

- Every AI claim in a report MUST cite the evidence it rests on and carry a confidence level
  (high, medium or low). Claims include defect descriptions, root-cause hypotheses and
  containment actions. Evidence means data points, rule violations, log entries or image
  observations.
- The UI MUST flag low-confidence or unsupported claims. An AI draft MUST NOT be presented as
  final. An engineer approves or edits each 8D section, and export marks unapproved sections
  as DRAFT.
- Structured model output MUST be validated against a schema. Invalid output is retried once.
  If it fails again, the step degrades with a visible error and does not invent content.

Rationale: quality engineers sign 8D reports for customers. Trust and accountability are the
product.

### IV. Deterministic Analytics

- All statistics and predictions MUST be computed by deterministic code. This covers control
  limits, run-rule violations, capability indices, change-point detection and correlations.
  An LLM never computes them.
- Models interpret computed facts and never produce new numbers. Every number in a report MUST
  trace back to a computed value or an input record.
- Each analytic method MUST be explained in the UI or report in one line, for example
  "Western Electric rule 2: 8 points on one side of the centre line".

Rationale: the results must be explainable and reproducible, and the track rules require it.

### V. Resilient, Configurable Inference

- A single OpenAI-compatible client handles all inference. It is configured only through
  environment variables: base URL, API key, and a model ID for each role (text, vision).
- Requests MUST include only fields the gateway accepts: model, messages, temperature,
  max_tokens, response_format, tools, tool_choice, stream and top_p.
- Client limits: at most 8 concurrent requests and a default budget of at most 20 requests
  per minute. The client honors `Retry-After` and retries 429 and 5xx with exponential backoff
  and jitter. It does not retry other 4xx errors.
- The results of the bundled sample case MUST be precomputed and stored. When live inference
  fails or the quota is exhausted, the app serves them labeled "cached AMD run", with the
  timestamp and model.

Rationale: free-tier rate limits and many judges trying the demo at once must not break it.

### VI. Test the Deterministic Core

- Unit tests are REQUIRED for the analytics (each SPC rule, capability, change point), for
  schema validation, and for the inference client's retry and limit logic, using a fake
  transport.
- One smoke test MUST run the golden path end to end with a mocked model.
- All tests MUST pass before every deploy. UI tests and coverage targets are not required.

Rationale: the numbers must be right, and the demo must not regress at the last minute.

### VII. Judge-Proof Demo and Delivery

- The public demo URL needs no login. It ships with the sample case preloaded, and a one-click
  run finishes the golden path in 120 s or less live, or instantly from the cache.
- One Dockerfile builds and runs the whole app. The README run steps work from a clean clone,
  and `.env.example` lists every variable.
- Submission assets are deliverables with the same priority as the code:
  - a video of 3 to 5 min (MP4)
  - slides as a PDF
  - a 16:9 cover image
  - a title of 50 characters or fewer
  - a short description of 50 to 255 characters
  - a long description of 600 to 2,000 characters

Rationale: judges spend minutes per project. Whatever they cannot open or understand fast
scores low.

### VIII. Security and Open Source

- Secrets MUST NOT be committed. `.env` is gitignored, keys come only from environment
  variables, and keys never reach the browser.
- Uploads are limited by size (10 MB or less per file) and by type (CSV, PNG, JPG, TXT, EML).
  They are processed in memory or temporary storage and are not stored after the request.
- The repository is MIT-licensed and public. Dependencies MUST use permissive licenses
  (MIT, BSD or Apache-2.0). Sample data and images are self-generated.

Rationale: these are lablab rules (original, open source, MIT), and a public demo needs basic
hygiene.

### IX. Simplicity

- The app is one backend service plus a static frontend, served from one container. There is
  no database and no authentication. State lives in memory and in bundled files.
- Each analysis makes at most 6 model calls. One well-structured call is preferred over a
  chain of calls.
- No speculative abstraction is allowed. Every module MUST serve the golden path or a P2 or P3
  story in the spec.

Rationale: every extra moving part is a new way for the demo to fail before the deadline.

## Hackathon Constraints and Submission Standards

- **Track 1 demo rule:** the product processes realistic industrial data and produces an alert,
  explanation, recommendation or action. It must be clear who uses it (a supplier quality
  engineer) and what it improves (time to containment and to a first 8D draft).
- **Judging (1 to 5 each):** Application of Technology, Presentation, Business Value,
  Originality. Every design choice should raise at least one of these.
- **Required links:** a public GitHub repo with commits spread across the event window, and a
  live demo URL that works for judges.
- **Presentation content:** problem, live demo, target user, measurable gain, TAM/SAM, revenue
  model, competitors and USP, roadmap.
- **Prize hooks:** the main AMD prize (mandatory AMD use) and the Google prize (Gemma use).
  The Evolus track is out of scope unless the constitution is amended.

## Development Workflow and Quality Gates

- **Spec-Driven Development:** constitution, then spec, then plan, then tasks, then implement.
  Artifacts live under `specs/<feature>/`. Each user prompt is recorded as a PHR under
  `history/prompts/`. Architecturally significant decisions are proposed as ADRs and need user
  consent.
- **Commits:** small and frequent, one per task or logical group, made only with the user's
  approval. A pre-commit check confirms no secrets are present.
- **Gate before every deploy:** tests pass, the Docker image builds, and the golden path runs
  locally with the configured provider.
- **Gate before submission:**
  - The golden path works on the public URL.
  - The AMD inference trace is visible.
  - The README run steps have been verified.
  - No secrets are in the git history.
  - The text, video, slides and cover image meet the limits in Principle VII.

## Governance

- This constitution supersedes other practices for this repository. Where it conflicts with
  the live event page, the event page wins, and the constitution is amended.
- Amendments need explicit user approval, a Sync Impact Report and a version bump. Versioning
  follows semantic versioning: MAJOR for removing or redefining a principle, MINOR for adding
  or materially expanding one, PATCH for clarifications.
- Compliance is checked at the plan's Constitution Check gate, after Phase 1 design, and at
  the pre-submission gate. Any justified violation is recorded in the plan's Complexity
  Tracking table.

**Version**: 1.0.0 | **Ratified**: 2026-10-17 | **Last Amended**: 2026-10-17
