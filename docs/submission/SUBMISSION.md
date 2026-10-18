# lablab.ai submission text: RootTrace 8D

> Copy these fields into the lablab submission form. Check the lengths with
> `python scripts/check_submission.py`.

## Title
RootTrace 8D: Complaint to 8D Report on AMD

## Short description
RootTrace 8D turns a customer quality complaint into an evidence-backed 8D report in minutes. Deterministic SPC finds the process shift and the suspect lots, AI on AMD drafts D1-D8 citing every fact, and the engineer approves.

## Long description
When an automotive customer rejects parts, the supplier's quality engineer must contain suspect stock within 24 hours and deliver an 8D report. Today that means hours to days of collecting the complaint, photos, SPC data and maintenance logs by hand. Containment is often a guess based on the lots the customer happened to name.

RootTrace 8D does the evidence work in one click. Deterministic statistics compute control limits, Western Electric rules, Cp/Cpk and the exact moment the process shifted, then turn that into a containment range and the suspect lots. AI models served on AMD GPUs through AMD Token Factory read the complaint, classify the defect photo, rank root-cause hypotheses across the 6M categories and draft all eight 8D sections. Every claim cites an evidence ID, and a number-trace check flags any figure the AI did not get from the data. The engineer edits and approves each section and exports a printable report with unapproved sections marked DRAFT.

In the sample case the customer names 2 lots. RootTrace finds the shift 10 minutes after a boring-bar change with a visual-only first-piece check, and asks the engineer to contain 11 lots, 9 of which the customer has not reported yet. It is built for supplier quality engineers in automotive and industrial manufacturing. Every AI step shows its AMD provider, model, latency and tokens.

## Track
Intelligent Industry

## Technology tags
AMD Token Factory, AMD Developer Cloud, AMD ROCm, Gemma 4 (Gemma-4-31B-IT), DeepSeek V4, Python, FastAPI, Docker

## Participation mode
Online

## Additional information (scaling)
- RootTrace runs as a single container. For plants with strict data rules it can run fully on-premises against a customer-owned AMD Instinct or Ryzen AI endpoint.
- The next connectors are MES/QMS SPC feeds and customer supplier portals.
- Planned analysis features are multi-characteristic SPC and a library of past 8Ds for recurring-cause detection.
- Pricing: SaaS per plant per month.
