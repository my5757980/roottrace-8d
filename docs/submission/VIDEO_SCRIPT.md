# Demo video script: RootTrace 8D (target 4:00, MP4, ≤ 300 MB)

Rules from the lablab rubric:
- under 5 min, but **over 3 min**
- problem → live demo → business case → competition and roadmap

Record the screen at 1920×1080. Open the Space URL in a clean browser window, with the zoom at
90%.

| Time | Screen | Narration (read calmly) |
|------|--------|-------------------------|
| 0:00–0:25 | Title slide, then the app home page | "When a carmaker rejects parts, the supplier's quality engineer has 24 hours to contain the problem and days to write an 8D report. Today that is manual detective work across emails, photos, SPC sheets and maintenance logs. RootTrace 8D does that evidence work in minutes, with AI running on AMD." |
| 0:25–0:45 | Case panel: complaint email, photo, data summary, AMD badge in the header | "Here is a real-world style case. Ardena Motors rejected 37 water-pump housings: the bearing bore is oversize. They name two lots. We have the complaint, a photo, two weeks of bore measurements from CNC-07, and the machine's maintenance log." |
| 0:45–1:05 | Click **Analyze complaint on AMD**. The steps tick through and the badges show LIVE | "One click. Deterministic statistics run first. No AI computes a single number. Then four AI steps run on AMD GPUs (AMD Token Factory): complaint facts, defect photo, root-cause hypotheses, and the 8D draft." |
| 1:05–1:35 | SPC card: hover the chart, the shift line, the red suspect range, the stats tiles | "The control chart shows the process was capable at Cpk 2.12, then it stepped up by 13 microns at 14:30 on October 8th. That is Western Electric rule 1, again and again. Capability after the shift is negative. RootTrace computes the containment window from the last known-good sample. Look at the lots: the customer named 2, but 11 lots are suspect, and 9 of them have not reached the customer yet." |
| 1:35–1:55 | "What changed" card: the TOOL_CHANGE (−10 min) and FIRST_PIECE (+15 min) rows, then the parameter table | "What changed? Ten minutes before the shift, the boring bar was replaced. Fifteen minutes after it, the first-piece check was done visually only. The tool-life counter confirms it, while the coolant dip happened 32 hours later, so it can't explain the shift." |
| 1:55–2:20 | Hypotheses card: hover the evidence chips S4 and L6, and the red 'against' chip | "The AI ranks root causes across the 6M. Every claim cites evidence IDs you can hover. Contradicting evidence is shown too, and confidence is explicit." |
| 2:20–2:45 | 8D card: D3 with the computed block, the flags, then type a reviewer name, approve D1–D4 and edit one line | "The 8D draft covers D1 to D8. Containment is copied from the computed facts, not invented. A number-trace check flags any figure that is not in the evidence. The engineer stays in charge: edit, approve, and every edit after approval needs re-approval." |
| 2:45–3:00 | Printable report: the DRAFT watermark on D5–D8, the trace appendix | "Export a customer-ready report. Unapproved sections are clearly marked DRAFT. The appendix lists every AI call: AMD provider, model, latency and tokens." |
| 3:00–3:30 | Slides: market and business model | "Who pays? Automotive and industrial suppliers. Every IATF 16949 plant writes 8Ds. We sell RootTrace per plant per month, with an on-premises option on the plant's own AMD hardware for data-sensitive customers." |
| 3:30–3:50 | Slides: competition and USP | "Quality-management suites store 8D forms but don't find the root cause. Generic chatbots invent numbers. RootTrace combines deterministic SPC, evidence-cited AI on AMD, and human sign-off." |
| 3:50–4:10 | Slides: roadmap, then end card | "Next: live MES and QMS connectors, multi-characteristic analysis, and learning from past 8Ds. RootTrace 8D: from complaint to evidence-backed containment in minutes. Thank you." |

**Before recording:**
- Run the sample live once to warm up the endpoint.
- If live is slow, use **Replay recorded AMD run** and say "this is the recorded AMD run".

**Export:** MP4, H.264, 1080p, under 300 MB.
