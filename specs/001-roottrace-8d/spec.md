# Feature Specification: RootTrace 8D (complaint to evidence-backed 8D draft)

**Feature Branch**: `001-roottrace-8d`
**Created**: 2026-10-17
**Status**: Draft
**Input**: User description: "RootTrace 8D: an AI copilot for supplier quality engineers that turns a customer quality complaint into an evidence-backed 8D report draft in minutes instead of days. Inputs: complaint text (email), one or more defect photos, production process data (CSV of timestamped part measurements and machine parameters per lot), and a maintenance/shift log. Flow: extract complaint facts (part, lot, defect, quantity, customer deadline) -> describe and classify the defect photo with an AMD-hosted vision model -> deterministic statistical process control analysis of the affected window (control limits, Western Electric run rules, capability Cpk, change-point time) -> correlate the change point with maintenance/shift events -> ranked root-cause hypotheses across the 6M categories with cited evidence and confidence -> 8D draft (D1-D8) including D3 containment with the exact suspect lots/time range to quarantine -> engineer reviews, edits and approves each section -> printable report export with unapproved sections marked DRAFT. A preloaded sample case (CNC-machined aluminium housing, bore diameter drifting out of tolerance after a tool change) runs with one click, and a cached AMD run is served if live inference fails. Every AI step shows provider, model, latency and tokens (AMD inference trace). Users: supplier quality engineers in automotive and industrial manufacturing. Measurable outcome: time to first 8D draft and to containment decision. Track: AMD Developer Hackathon ACT III, Track 1 Intelligent Industry."

## Context

A supplier quality engineer who receives a customer complaint must answer quickly. Automotive and
industrial customers usually expect containment within about 24 hours and a structured 8D report
soon after. Today the engineer collects the complaint email, the defect photos, the production
measurements and the maintenance log by hand, looks for the moment the process changed, and writes
the eight report sections from scratch. That takes hours to days and depends on the engineer's
experience.

RootTrace 8D does the evidence work in minutes. It computes the statistics deterministically, uses
AI hosted on AMD infrastructure to read the text and images and to draft the report, cites the
evidence behind every claim, and leaves the final decision on each section to the engineer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-click analysis of the sample complaint (Priority: P1) 🎯 MVP

A supplier quality engineer, or a hackathon judge, opens the app and sees a complaint case already
loaded. The case contains:

- an email from an automotive customer reporting housings whose bore does not fit
- a photo of a rejected part
- two weeks of bore-diameter measurements per part, with machine parameters and lot numbers
- the machine's maintenance and shift log

They press one button. Within two minutes the app shows, step by step:

- the key facts of the complaint
- a description and classification of the visible defect
- a control chart that highlights where the process went out of control and when it shifted
- the maintenance event that lines up with the shift (a tool change)
- a ranked list of root-cause hypotheses with their evidence and confidence
- a complete 8D draft whose containment section names the exact lots and time range to quarantine

Each AI step shows which AMD-hosted model served it, how long it took, and how many tokens it used.

**Why this priority**: This is the golden path that judges and buyers will see. On its own it shows
the whole value: an evidence-backed first draft and a containment decision in minutes.

**Independent Test**: On a fresh visit, press "Analyze" on the preloaded case. Confirm that every
step completes and that the 8D draft, the chart, the hypotheses and the AI trace all appear. Confirm
that the suspect range covers every out-of-tolerance part in the sample data.

**Acceptance Scenarios**:

1. **Given** the app is opened for the first time, **When** the page loads, **Then** the sample case
   inputs (complaint, photo, process data summary, maintenance log) are visible and no login or setup
   is required.
2. **Given** the sample case is loaded, **When** the user presses "Analyze", **Then** each analysis
   step shows its status (waiting, running, done, failed) and its result as soon as it completes.
3. **Given** the analysis has finished, **When** the user views the statistics panel, **Then** a
   control chart shows the baseline centre line and control limits, the specification limits, the
   points that violate run rules, the detected shift time, and every number with a one-line
   explanation of how it was calculated.
4. **Given** the analysis has finished, **When** the user views the hypotheses, **Then** each one has
   a 6M category, at least one evidence reference, any contradicting evidence, a confidence level and
   a suggested verification step, and the list is ranked.
5. **Given** the analysis has finished, **When** the user views the 8D draft, **Then** all eight
   sections D1 to D8 are present, and D3 names the suspect lots and the start and end of the time
   range to quarantine. That range comes from the computed statistics.
6. **Given** any AI step completed, **When** the user views the AI trace, **Then** the step shows the
   provider, the model, whether the result was live or cached, its latency, and its input and output
   tokens.
7. **Given** live AI inference is unavailable or rate-limited, **When** the user analyzes the sample
   case, **Then** the stored results of an earlier AMD run appear within 5 seconds, clearly labeled
   "cached AMD run" with its timestamp and model.

---

### User Story 2 - Review, approve and export the 8D report (Priority: P2)

The engineer reads each 8D section, edits any wording that is wrong or incomplete, and marks each
section approved. They enter their name once. They then open a printable report that they can save
as a PDF and send to the customer or attach to the QMS. Any section they have not approved is
clearly watermarked DRAFT.

**Why this priority**: Accountability is what makes an AI draft usable. The engineer signs the
report, not the AI. Without review and export, the output cannot leave the app.

**Independent Test**: After a completed analysis (live or cached), edit D4, approve D1 to D3 and D4,
leave D5 to D8 unapproved, and open the printable report. Confirm that the edits appear and that
D5 to D8 carry the DRAFT mark. Confirm that the approval summary shows 4 of 8 approved, with the
approver's name and time.

**Acceptance Scenarios**:

1. **Given** a completed 8D draft, **When** the engineer edits a section's text, **Then** the edit is
   kept and the section is marked "edited by engineer".
2. **Given** a section has been approved, **When** the engineer edits it again, **Then** its status
   returns to "needs re-approval".
3. **Given** some sections are unapproved, **When** the engineer opens the printable report,
   **Then** every unapproved section is marked DRAFT and the header shows the approval summary
   (for example "4/8 sections approved").
4. **Given** the printable report is open, **When** the engineer saves or prints it, **Then** it
   contains the complaint facts, the control chart, the evidence table, all eight sections and an
   appendix with the AI trace.

---

### User Story 3 - Analyze my own complaint case (Priority: P3)

The engineer replaces the sample with their own case. They paste or upload the complaint text,
upload up to three defect photos, upload the process measurement file, map or confirm the
measurement column and the specification limits, and optionally upload the maintenance log. Then
they run the same analysis.

**Why this priority**: This proves the product is not a canned demo and works on real customer
data. It is the bridge to a paid pilot. It comes after P1 and P2 because the judged golden path
depends on those.

**Independent Test**: Upload a different valid measurement file with a known shift and a complaint
text. Confirm that the analysis runs, finds the shift and produces a draft. Then upload a file that
lacks a timestamp column and confirm that a specific, actionable error appears.

**Acceptance Scenarios**:

1. **Given** the user chooses "New case", **When** they provide the complaint text and a valid
   measurement file with specification limits, **Then** the analysis can be run. Photos and the
   maintenance log are optional.
2. **Given** an uploaded measurement file, **When** it lacks a required field (timestamp, lot or a
   numeric measurement), **Then** the app names the missing field and the expected format, and does
   not start the analysis.
3. **Given** a file or photo larger than the allowed size or of an unsupported type, **When** the user
   uploads it, **Then** the app rejects it with a clear message.
4. **Given** live AI is unavailable for a custom case, **When** the user runs the analysis, **Then**
   the deterministic statistics still appear, the AI sections show "AI unavailable, retry", and
   nothing is invented.

---

### Edge Cases

- **Too little data**: fewer than 20 measurements in the baseline window. Control limits are not
  computed, and the app warns "insufficient data for control limits" and continues with the other
  steps.
- **No specification limits**: capability indices are skipped, and the app says so.
- **No significant shift**: the app states "no statistically significant shift detected". The
  hypotheses then rely on the complaint and image evidence, and containment falls back to the lots
  named in the complaint.
- **Several shifts**: the most significant one is used for containment, and the others are listed.
- **Complaint without a lot number**: containment is derived from the shift time range alone, and
  "lot not stated in complaint" is flagged.
- **Unclear or irrelevant photo**: the defect finding is low confidence and suggests retaking the
  photo. It does not invent a defect type.
- **Empty or missing maintenance log**: the correlation step is skipped with a note.
- **Malformed AI output**: retried once. If it fails again, the step is marked failed with a reason,
  and the other steps continue.
- **Rate limiting**: the step shows "waiting for AMD capacity" while it retries. If the wait runs out,
  the sample case uses the cached run and a custom case shows a retry option.
- **Non-English complaint**: facts are extracted and reported in English, with the original quote
  kept as evidence.
- **Timestamps out of order or in mixed formats**: they are parsed and sorted, and rows that cannot
  be parsed are counted and reported.
- **Many visitors at once**: each analysis runs independently, and one person's run does not change
  another's results.

## Requirements *(mandatory)*

### Functional Requirements

**Case and inputs**

- **FR-001**: The system MUST open with a preloaded sample case and need no login, account or
  configuration from the visitor.
- **FR-002**: The system MUST let the user start a new case by providing:
  - complaint text (pasted, or a text or email file)
  - up to 3 defect photos
  - a process measurement file
  - specification limits
  - an optional maintenance and shift log
- **FR-003**: The system MUST validate inputs before analysis: required fields, numeric values,
  parseable timestamps, file types, and a maximum size of 10 MB per file. It MUST report each
  problem with a specific, actionable message.

**Analysis**

- **FR-004**: The system MUST run the whole analysis from a single user action and show each step's
  status and result as soon as that step completes.
- **FR-005**: The system MUST extract these complaint facts:
  - customer
  - part number and name
  - affected lots
  - defect description
  - quantity affected
  - date received
  - customer response deadline

  Each fact MUST show the source quote it came from. Facts that are not present MUST be marked
  "not stated".
- **FR-006**: The system MUST describe each defect photo, classify it into a fixed defect taxonomy
  with a confidence level, and list the visual observations that support the classification. The
  taxonomy is: dimensional (not visually assessable), scratch, burr, porosity, crack,
  discoloration or corrosion, chatter or tool marks, contamination, other.
- **FR-007**: The system MUST compute statistical process control facts with deterministic,
  reproducible methods (identical inputs always give identical numbers):
  - baseline centre line and control limits for the measured characteristic
  - violations of Western Electric run rules 1 to 4
  - process capability (Cp and Cpk) for the baseline window and the affected window
  - the most significant shift time
  - the count, lots and time range of out-of-specification parts
- **FR-008**: The system MUST list the maintenance and shift events within a set window around the
  detected shift (default ±2 hours), with the time difference to the shift.
- **FR-009**: The system MUST produce 3 to 6 ranked root-cause hypotheses. Each one has:
  - one 6M category (Man, Machine, Method, Material, Measurement, Environment)
  - its supporting evidence references
  - any contradicting evidence
  - a confidence level (high, medium or low)
  - one suggested verification step
- **FR-010**: The system MUST produce an 8D draft with all eight sections:
  - D1: team roles
  - D2: problem description in 5W2H form
  - D3: interim containment, naming the suspect lots and time range derived from the computed
    statistics, the sort or quarantine actions, and the customer notification
  - D4: root cause, with occurrence and escape points and a verification plan
  - D5: permanent corrective actions
  - D6: implementation and validation, with measurable acceptance checks
  - D7: prevention, with control plan and FMEA updates and lessons learned
  - D8: closure
- **FR-011**: Every number in the AI-written narrative MUST match a computed value or an input
  record. The system MUST flag any number in the draft that it cannot trace.
- **FR-012**: The system MUST make uncertainty visible. Low-confidence findings are visibly marked,
  and where evidence is insufficient the system MUST say so rather than guess.
- **FR-013**: Each number on the statistics panel MUST carry a one-line plain-language explanation
  of how it was calculated.

**Transparency and resilience**

- **FR-014**: For each AI step, the system MUST record and display:
  - provider
  - model
  - live or cached
  - latency
  - input and output tokens

  It MUST also display the total analysis time.
- **FR-015**: All AI inference in the judged product MUST run on AMD-hosted infrastructure. The
  provider and model shown MUST reflect what actually served the step.
- **FR-016**: When live AI is unavailable, failing or rate-limited, the system MUST serve the stored
  results of an earlier AMD run for the sample case, labeled "cached AMD run" with its timestamp and
  model. For custom cases it MUST still show the deterministic statistics and offer a retry for the
  AI steps.
- **FR-017**: Invalid AI output MUST be retried once. If it fails again, the step is marked failed
  with a reason, and no content is fabricated.

**Review and export**

- **FR-018**: The engineer MUST be able to edit the text of each 8D section and to approve or
  unapprove each section. The section states are AI draft, edited by engineer, approved, and needs
  re-approval (after an edit that follows approval).
- **FR-019**: The engineer MUST be able to enter a reviewer name that is shown with each approval
  and its time.
- **FR-020**: The system MUST produce a printable report that can be saved as a PDF. It contains:
  - a header with the case ID, date and approval summary
  - the complaint facts
  - the control chart
  - an evidence table
  - the hypotheses
  - all eight sections, with every unapproved section watermarked DRAFT
  - an AI trace appendix

**Data handling**

- **FR-021**: The system MUST NOT keep uploaded files or case data after the visitor's session ends.
  Keys used to reach AI services MUST never be exposed to the visitor's browser.

### Key Entities

- **Case**: one complaint investigation. It has an ID, a creation time, whether it is the sample
  case, and links to all inputs and results.
- **Complaint**: the raw complaint text and the list of extracted facts. Each fact has a name, a
  value or "not stated", and a source quote.
- **Defect Image**: an uploaded or sample photo with its defect finding (taxonomy class, confidence,
  observations, description).
- **Process Dataset**: the measurement records (timestamp, lot, part serial if any, measured value,
  machine parameters) and the specification limits (target, lower, upper, unit).
- **Maintenance Event**: one time-stamped entry of the maintenance or shift log (time, type,
  machine, description, author or shift).
- **SPC Result**: the baseline window, centre line and limits, run-rule violations (rule, points,
  explanation), capability per window, shift time and magnitude, and the out-of-spec summary
  (count, lots, first and last time).
- **Correlated Event**: a maintenance event matched to a detected shift, with its time difference.
- **Hypothesis**: a 6M category, a statement, supporting and contradicting evidence references, a
  confidence level, a verification step and a rank.
- **Evidence Reference**: a pointer to a source item: a complaint quote, an image observation, an
  SPC fact or a log entry.
- **8D Report**: eight sections. Each section has its content, status, edit history flag, approver
  and approval time.
- **AI Trace Entry**: the step name, provider, model, live or cached, start time, latency and token
  counts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time visitor gets a complete 8D draft for the sample case in under 3 minutes
  from opening the app, with no instructions.
- **SC-002**: On the sample case, the detected shift time falls within 15 minutes of the tool change
  recorded in the maintenance log. The suspect range in D3 covers 100% of the out-of-specification
  parts in the data, and it starts at the last known-good sample, no more than 1 hour before the
  detected shift.
- **SC-003**: In the sample case output, 100% of numbers in the 8D narrative trace to computed values
  or input records, with zero untraceable numbers.
- **SC-004**: 100% of root-cause hypotheses show at least one evidence reference and a confidence
  level.
- **SC-005**: When live AI is unavailable, the sample case still shows complete results within
  5 seconds, labeled as cached.
- **SC-006**: 100% of AI steps show the provider, model, latency and token usage.
- **SC-007**: 100% of invalid uploads tested (missing fields, wrong types, oversize files) produce a
  specific error message, and the app never crashes.
- **SC-008**: The time to first 8D draft and containment decision drops from the typical manual
  effort of hours to days to under 5 minutes, measured on the sample case.
- **SC-009**: A reviewer can approve all eight sections and export the report in under 2 minutes
  after the analysis completes.

## Assumptions

- **Single characteristic**: each analysis covers one measured characteristic at a time, for
  example bore diameter, with one measurement per part. Multivariate and subgrouped charts are out
  of scope.
- **Baseline window**: by default the earliest stable part of the data (at least 20 points) before
  the complaint period. The user can accept it or adjust it.
- **Specification limits**: they come from the case form or the sample case configuration and are
  not inferred.
- **One role**: the only user role is the quality engineer. There is no authentication, and
  approval is identified by a typed reviewer name.
- **Language**: the UI and report are in English. The complaint may arrive in another language
  that the AI supports, best effort.
- **Sample data**: the sample case data (measurements, photo, emails, logs) is synthetic but
  realistic, and created by the team.
- **AMD inference**: AI inference runs on AMD-hosted infrastructure, as the hackathon requires.
  The specific models can be configured. Where a Gemma model is offered on that infrastructure, it
  is preferred for at least one step.
- **Session state**: case state lives only for the visitor's session. Refreshing the page may
  reset a custom case. The sample case is always available.

## Dependencies

- Access to an AMD-hosted AI inference endpoint (API key and model IDs) for live runs, and to
  record the cached AMD run of the sample case before the public demo goes live.
- A public hosting location for the demo, reachable by judges without login.

## Out of Scope

- Integration with QMS, ERP or MES systems, and submission to customer supplier portals.
- Multi-user collaboration, user accounts, permissions and persistent case storage.
- Multivariate SPC, subgrouped charts and gauge R&R studies.
- The Evolus partner-track integration.
- Native mobile apps.
