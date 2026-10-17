# Data Model: RootTrace 8D

All entities are Pydantic models in `app/models.py`. Nothing is persisted. A `Case` lives in the
in-memory store (TTL 2 h, at most 300 cases, least recently used evicted first).

## Case

| Field | Type | Notes |
|-------|------|-------|
| id | str | Random URL-safe token, 16 bytes, unguessable |
| created_at | datetime (UTC) | |
| is_sample | bool | |
| title | str | For example "AH-2207 bore oversize, Ardena Motors" |
| spec | SpecLimits | |
| columns | ColumnMap | Maps the CSV columns |
| baseline_end | datetime \| None | Overrides the default baseline window |
| complaint_text | str | At most 20,000 characters |
| images | list[ImageInput] | At most 3 |
| dataset_summary | DatasetSummary | Rows, time range, lots and characteristic name |
| events | list[MaintenanceEvent] | May be empty |
| analysis | Analysis \| None | The latest run |
| report | Report \| None | Created when the `draft_8d` step finishes |

## SpecLimits

`characteristic` (str), `unit` (str, default "mm"), `lsl` (float | None), `usl` (float | None),
`target` (float | None).

Validation: when both are present, `lsl < usl`. At least one limit is required for capability.

## ColumnMap

`timestamp` (default "timestamp"), `lot` (default "lot"), `value` (required; for example
"bore_diameter_mm"), `parameters` (list[str], defaulting to the other numeric columns).

## ImageInput

`index` (int), `filename` (str), `content_type` ("image/jpeg" or "image/png"), `data` (bytes,
stored in memory and normalized to JPEG with the longest side ≤ 1024 px).

## MaintenanceEvent

`id` (for example "L3"), `timestamp` (datetime), `type` (str, for example TOOL_CHANGE), `machine`,
`description`, `shift`, `author`.

## SPCResult

| Field | Type |
|-------|------|
| n_points / n_dropped | int |
| baseline | {start, end, n, mean, sigma, mr_bar} |
| limits | {cl, ucl, lcl, sigma, zones: {pos1, pos2, neg1, neg2}} |
| violations | list[{rule: 1–4, index, timestamp, value, explanation}] (deduplicated per point, keeping the lowest rule number) |
| capability | {baseline: {cp, cpk, mean, sigma}, after: {cp, cpk, mean, sigma}} or None per window when the limits are missing |
| change_point | {detected: bool, index, timestamp, mean_before, mean_after, delta, t_stat, explanation} |
| out_of_spec | {count, first, last, lots: list[str], max_value, min_value} |
| containment | {start, end, lots: list[str], n_samples, n_out_of_spec, rationale} |
| series | {t: list[str ISO], v: list[float], lot: list[str], flags: list[int]} (downsampled if longer than 3,000 points) |
| warnings | list[str] |

## ParameterShift

`name`, `detected` (bool), `change_time`, `mean_before`, `mean_after`, `delta`, `hours_from_cp`
(the signed number of hours between this shift and the measurement change point).

## CorrelatedEvent

`event_id` (L*), `timestamp`, `type`, `description`, `delta_minutes` (event time minus change
point).

## EvidenceItem

`id` (str, C1, I1, S1, P1, L1 ...), `kind` ("complaint", "image", "spc", "parameter" or "log"),
`text` (str, the human-readable fact, including its numbers).

## ComplaintFacts (AI, step `complaint_facts`)

`facts`: a list of {name ∈ [customer, part_number, part_name, lots, defect_description,
quantity_affected, date_received, response_deadline, customer_measurement], value (str |
"not stated"), quote (str | "")}. `language` (str). `summary` (str, 2 sentences or fewer).

## DefectFinding (AI, step `defect_vision`)

Per image: `image_index`, `defect_class` (one of the taxonomy values in FR-006), `confidence`
(high, medium or low), `observations` (list[str], 1 to 6), `description` (str),
`retake_suggestion` (str | None).

## Hypothesis (AI, step `hypotheses`)

`rank` (1 to 6), `category` (Man, Machine, Method, Material, Measurement or Environment),
`statement`, `supporting` (list[evidence id]), `contradicting` (list[evidence id]), `confidence`
(high, medium or low), `verification` (str), `unsupported` (bool, set by the server when no valid
supporting IDs remain).

## Report and ReportSection (AI draft plus engineer state)

ReportSection:

| Field | Type |
|-------|------|
| id | "D1" … "D8" |
| title | str |
| content | str (plain text with "- " bullets) |
| evidence | list[evidence id] |
| status | "ai_draft", "edited", "approved" or "needs_reapproval" |
| approved_by / approved_at | str \| None / datetime \| None |
| untraceable_numbers | list[str] (from `trace_check`) |

State transitions:

```text
ai_draft --edit--> edited --approve--> approved --edit--> needs_reapproval --approve--> approved
ai_draft --approve--> approved          approved --unapprove--> edited (or ai_draft if never edited)
```

Report: `sections` (list[ReportSection], 8 items), `reviewer` (str | None),
`approved_count` (derived).

## Analysis

| Field | Type |
|-------|------|
| run_id | str |
| mode | "live", "cached" or "mock" |
| status | "running", "done" or "failed" |
| started_at / finished_at | datetime |
| steps | list[StepState] (8 steps in pipeline order) |
| spc | SPCResult \| None |
| parameter_shifts | list[ParameterShift] |
| correlated_events | list[CorrelatedEvent] |
| evidence | list[EvidenceItem] |
| complaint_facts | ComplaintFacts \| None |
| defect_findings | list[DefectFinding] |
| hypotheses | list[Hypothesis] |
| trace | list[TraceEntry] |
| elapsed_seconds | float \| None |

StepState: `name`, `kind` ("deterministic" or "ai"), `status` (pending, running, done, failed or
skipped), `source` ("live", "cached", "mock" or "computed"), `message` (str | None),
`started_at`, `finished_at`.

## TraceEntry

`step`, `provider` (a label from config, for example "AMD TokenFactory · AMD Instinct GPU"),
`model`, `source` (live, cached or mock), `started_at`, `latency_ms`, `prompt_tokens`,
`completion_tokens`, `attempts`, `status` (ok or error), `error` (str | None).

## Cached run file (`sample_case/cached_run.json`)

`{ "recorded_at", "provider", "models": {"text","vision"}, "steps": { "complaint_facts": {result, trace},
"defect_vision": {...}, "hypotheses": {...}, "draft_8d": {...} } }`

It stores only the AI step outputs plus their trace entries. Deterministic steps are always
recomputed.
