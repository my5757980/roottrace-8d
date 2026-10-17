# AMD Developer Hackathon: ACT III: Requirements Brief

> **Purpose:** One place that records every requirement of the event. The SDD phases (constitution, specify, plan, tasks, implement) build on it.
> **Scanned:** 2026-10-16, about 11:20 UTC (the live dashboard reported `fetchedAt 2026-10-16T11:18Z`).
> **Official page:** https://lablab.ai/event/amd-developer-hackathon-act-iii (canonical: `https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii`)
> The URL in the original request (`lablab.ai/ai-hackathone/amd-developer-hackathone-act-iii`) returns **404**. It has typos.
> **Priority rule:** the event page and the submission form override this brief and lablab's generic guides. Re-check the live page before submitting.

---

## 0. Summary: what decides a win

| # | Must-know | Detail |
|---|-----------|--------|
| 1 | **Deadline** | **Sun 18 Oct 2026, 12:00 CEST = 10:00 UTC = 15:00 PKT**, plus a 5-minute grace period. The platform timeline also has an **"End" marker at Sat 17 Oct 17:00 UTC (22:00 PKT)**, so we treat that as our **internal hard stop**. |
| 2 | **AMD is mandatory** | A meaningful part of the workload must run on AMD, and the judges must see it in the working product. Without it the project cannot win a prize. |
| 3 | **Working product** | It must solve a real problem for a real user. A dashboard or a slide deck alone does not count. |
| 4 | **Submission package** | Title, short and long description, track, tech tags, **public GitHub repo (MIT, open source)**, **live demo URL**, **video (MP4/MOV, ≤300 MB, 3 to 5 min)**, **slides (PDF)**, cover image (16:9). |
| 5 | **Judging** | Four criteria, each scored 1 to 5: Application of Technology, Presentation, Business Value, Originality. **Weights are not published.** |
| 6 | **Extra prize hooks** | Use **Gemma** to compete for the **Google prize ($5,000)**. Evolus track: €1,011.50 in plan value. Vibe Generation special prize: AirPods 5 for every team member. Imment incubation: Italian teams only. |

Time left at scan time: about **29.7 h** to the 17 Oct 17:00 UTC marker and about **46.7 h** to the official 18 Oct 10:00 UTC deadline.

---

## 1. Event identity

- **Name:** AMD Developer Hackathon: ACT III (AMD × lablab.ai). Third edition. ACT II ran in July 2026.
- **Tagline:** "Build AI agents and high-performance AI applications on AMD GPUs in the cloud."
- **Prize pool:** $17,000+ (third-party listings say $12,000+ or $5,000+, but the official page says $17,000+).
- **Type:** HYBRID. It runs online the whole time, and an optional on-site phase is open to approved participants.
- **Audience:** developers, founders, engineers and builders. Open to everyone, whatever their AI or coding experience.
- **Stack promise:** AMD GPUs in the cloud with the **ROCm** software stack. Everything runs in the cloud, with no local hardware to set up.
- **Live stats at scan time:** 5,978 participants, 1,291 teams, 33 submissions, 39 drafts.

## 2. Dates and timeline (all verified from the page payload)

| Event | CEST (Italy) | UTC | PKT (UTC+5) |
|-------|--------------|-----|-------------|
| Event `startAt` | Mon 12 Oct 17:00 | 12 Oct 15:00 | 12 Oct 20:00 |
| Hackathon kick-off | Mon 12 Oct 17:00 | 12 Oct 15:00 | 12 Oct 20:00 |
| Discord Q&A session | Mon 12 Oct 18:00 | 12 Oct 16:00 | 12 Oct 21:00 |
| Platform timeline "End" marker | Sat 17 Oct 19:00 | 17 Oct 17:00 | 17 Oct 22:00 |
| **Submission deadline** (schedule, and event `endAt`) | **Sun 18 Oct 12:00** | **18 Oct 10:00** | **18 Oct 15:00** |
| Demo showcase / live pitches (on-site) | Sun 18 Oct 14:00 to 16:00 | 12:00 to 14:00 | 17:00 to 19:00 |

- The online build window is stated as "12–18 October 2026" on the main page and "12–17 October 2026" on the live dashboard. **Conflict:** plan for 17 Oct.
- **Grace period:** submissions close at the deadline plus 5 minutes. If a technical problem blocks submission, contact the organizers **before** the deadline, because only they can extend it.
- The team can keep editing the submission until the deadline.

### On-site phase (optional, Italy, 17–18 Oct)

Approved participants pick one city. **Travel and accommodation are not covered.**

| City | Venue | Address | Hours |
|------|-------|---------|-------|
| Rome | Link Campus University (unilink.it) | Via del Casale di San Pio V, 44, 00165 Roma | 17 Oct 10:00–18:00 · 18 Oct 10:00–17:00 |
| Milan | SmartCityLab Milano | Via Giuseppe Ripamonti, 88, 20141 Milano MI | 17 Oct 09:00–18:00 · 18 Oct 09:00–17:00 |
| Imperia | IMPERIAWARE | Via Antonio Delbecchi, 22, 18100 Imperia (IM) | 17 Oct 09:00–18:00 · 18 Oct 09:00–17:00 |

On-site schedule: doors open 09:00 (10:00 in Rome), breakfast, opening words and process explanation 10:30 (17 Oct), lunch 12:30, doors close 18:00. On 18 Oct: doors open 09:00, **submission deadline 12:00**, lunch 12:30, live pitches 14:00–16:00, doors close 17:00.

## 3. Registration and eligibility (manual steps for the human team)

1. Create a lablab.ai account and complete the profile.
2. Enroll through **"Sign up with AMD"** on the event page.
3. **Join the AMD AI Developer Program (ADP).** Approval for the hackathon requires it. New ADP members get **$100 in AMD credits**.
4. Join the **lablab.ai Discord** (discord.gg/lablabai) and connect it to the lablab profile. Team creation requires the connection.
5. **Create or join a team of 1 to 6 people.** Teammates can be found on the dashboard or in Discord `#looking-for-team`.
6. Read the Hackathon Guidelines, the Getting Started Guide and the Rule Book (summarized in §9 and §10).
7. On the submission form, set **Participation Mode** to online or onsite (this is a hybrid event).

## 4. Mandatory technology: build on AMD

> "Every project must run a meaningful part of its workload on AMD infrastructure or AMD hardware... **The AMD component must be part of the working product shown to the judges.** AMD is a required technology to be eligible for prizes."

Allowed options:
- AMD Developer Cloud
- AMD Instinct accelerators (for example, MI300X)
- AMD ROCm
- AMD Ryzen AI
- AMD Radeon hardware
- Other approved AMD-powered infrastructure provided during the event

Teams choose their own compatible models, frameworks and tools.

**Event FAQ (verbatim intent):**
1. "The event is hosted on **notebooks.amd.com/tokenfactory**. There is no billing or credit card info needed."
2. "Developers **don't need the $100 credit** to participate in the event. **Just the API from the tokenfactory.**"

### 4.1 AMD TokenFactory (primary path, no credits needed)

- **Portal:** https://notebooks.amd.com/tokenfactory ("AMD AI Notebooks": GPU-powered JupyterLab, AMD ROCm environment, on demand). Sign-in uses an **AMD AI Developer Program (Global) login** (SAML), with a separate China login.
- **Global API base URL and model list are not publicly documented.** They are visible only after login. **Action:** a team member logs in and records the base URL, the API key and the output of `GET /v1/models`.
- **Reference documentation** for the same AMD product family (the China-region "Radeon Cloud Token Factory", https://amd-aim.github.io/radeon-cloud-docs/) has not been verified against the global portal:
  - OpenAI-compatible `POST /v1/chat/completions`, `GET /v1/models`, plus Anthropic-compatible `POST /v1/messages`. Auth is `Authorization: Bearer <key>`.
  - Accepted fields: `model`, `messages` (system/user/assistant/tool), `stream`, `temperature`, `top_p`, `max_tokens`, presence and frequency penalties, `response_format` (JSON mode), `tools`, `tool_choice`, `reasoning_effort`. **Other fields are silently dropped.**
  - Embeddings, images, audio, rerank and `/v1/responses` return **404** on the free API.
  - Models there include DeepSeek-V4-Flash, DeepSeek-V4-Flash-Vision-Exp, DeepSeek-V4.1-Flash, Qwen3.8-Flash-Next, Qwen3.8-27B, GLM-5.3-Flash, MiMo-V2.6-Flash and MiniCPM5-2B, plus the OCR model MinerU2.5-Pro. Several accept image input, and all chat models support tools and JSON mode.
  - **Rate limits there:** about **20 requests/min per account**, 30 RPM per key, **8 concurrent requests per key**, and a rolling spend cap. A 429 response carries `Retry-After`.
- **Design consequence:** the LLM provider must be **configurable** through environment variables (base URL, key, model IDs). Every call goes through rate-limit-aware retries. Golden-path results must be cacheable.

### 4.2 AMD Developer Cloud (optional and needs credits): self-hosted model on MI300X

- 1× **AMD Instinct MI300X** (192 GB HBM3) costs about **$1.99/hr**, and 8× costs about $15.92/hr. Image: "vLLM Quick Start" (vLLM + ROCm + Docker, Ubuntu 24.04). Region ATL1 has consistent stock. SSH-key access only. Provisioning takes 2 to 4 min.
- Credits: $100 for new ADP members (about 50 GPU-hours). They expire 30 days after they are applied. The tutorial says a card is needed before a droplet can be created. **The Evolus page says credit approval takes 2–3 business days**, which is risky this close to the deadline.
- A powered-off droplet still bills, so it must be **destroyed**.
- Serving: `python -m vllm.entrypoints.openai.api_server --model <hf-model> --host 0.0.0.0 --port 8000 --dtype float16 --api-key <secret>`. Use `--tool-call-parser hermes` (with `--enable-auto-tool-choice`) for Qwen tool calling. **Always set `--api-key`.** Docker port mapping bypasses UFW.

### 4.3 Other AMD learning resources linked

AMD AI Developer Program (developer.amd.com/ai-developer-program), AMD cloud development hub, ROCm AI Developer Hub, ROCm docs, ROCm install guide, github.com/ROCm/ROCm, AMD AI Academy, hands-on labs with real GPU access.

## 5. Tracks: choose one or more

Common framing: "Solve a real business problem with AMD technology. **The product should work**, and AMD technology should power a meaningful part of it." Teams can combine LLMs, computer vision, audio, agents and predictive models.

### Track 1: Intelligent Industry (partner: Vibe Generation)

*"Help factories spot problems earlier and operate better."* Factories already have machine, camera, sensor, maintenance and manual data. The hard part is knowing what matters and what to do next. The product should reduce downtime and improve quality, safety or resource efficiency.

- **Ideas:** predict equipment failures · detect defects from images or video · explain production anomalies · help technicians search manuals and maintenance records · recommend maintenance actions · monitor safety conditions · reduce energy or material waste.
- **Demo:** the product processes **realistic industrial data** and produces a useful **alert, explanation, recommendation or action**. It must be clear **who uses it** and **what result it improves**.
- **Good projects show:** a real manufacturing problem · a working product, not only a dashboard or presentation · results operators can understand · **measurable improvement** in time, cost, safety, quality or efficiency.

### Track 2: Health and Wellbeing (partner: Vibe Generation)

*"Make a part of the patient journey safer, clearer, or easier."* The pain points are long documents, scattered information, repetitive admin, language barriers and limited time.

- **Ideas:** patient intake · medical record summaries · appointment preparation · care navigation · clearer discharge instructions · multilingual patient communication · healthcare document processing · admin workflow automation · wellbeing and prevention support.
- **Demo:** a realistic case **from first input to final result**. **Uncertainty must be visible**, and the product must **know when a person must review or take over**.
- **Safety rules (mandatory):** the product must **not present autonomous diagnosis or treatment as medical advice**. The team must explain how it handles incorrect or unsupported responses, sensitive information, uncertain results, high-risk decisions and human review.
- **Good projects show:** a clearly defined patient or staff need · responsible handling of health info · useful, understandable results · measurable improvement in time, accuracy, accessibility or workload.

### Track 3: Reinvent Commerce (partner: Vibe Generation)

*"Help a business understand its customers and take better action."* Product, transaction, inventory, review, support and marketing data are often disconnected. The product should help a business attract, serve, convert or retain customers.

- **Ideas:** shopping assistants · product discovery and recommendations · customer support · demand and inventory planning · catalogue enrichment · review and sentiment analysis · promotion planning · churn prevention · accessible and multilingual shopping · in-store computer vision.
- **Demo:** customer or business data turns into a useful **recommendation or action**.
- **Forecasting rule:** if the product predicts demand, sales or behavior, it must **explain how the prediction was calculated**. **An LLM must not be the only forecasting method.**
- **Good projects show:** a real customer or merchant problem · a useful commercial action · relevant personalization · a measurable effect on revenue, margin, conversion, retention, inventory or service quality.

### Track 4: Create a New Kind of Experience (partner: Vibe Generation)

*"Build a media, marketing, or entertainment experience that was not practical before generative AI."* It should do more than generate an image, ad or chatbot. It should respond to its audience, change with context, or give each person a different experience.

- **Ideas:** personalized video · interactive stories · audience-driven entertainment · adaptive campaigns · multilingual creative content · generative brand experiences · responsive sound or visual environments · new social formats · accessible media · creative quality control.
- **Demo:** the experience **changes for at least two different audiences, situations or inputs**. The team must explain what it created, what the models generated or decided, **how quality and consistency were controlled**, **the cost of each generated experience**, and **who would pay and why**.
- **Good projects show:** an original concept · strong UX · a thoughtful mix of human creativity and technology · a realistic cost.

### Partner track: Evolus Business Agents on AMD (partner: Evolus AI)

*"Build an AI agent that runs a real business process end to end, on Evolus, powered by an open model served on AMD."* Input arrives as an email, PDF, recording, web form or chat. The agent reasons with an open model on AMD and then acts: it runs a workflow, extracts data, uses AI Tools, updates a system, or hands off to a human.

**Hard requirements:**
1. Build in a free **Evolus event workspace** created at app.evolus.ai with the **event code shared at kickoff** (link published on evolus.ai/en/hackathon). A workspace created before kickoff is not an event workspace.
2. **Bring your own model:** the main agent must use an **open model served on AMD through your own vLLM endpoint on AMD Developer Cloud**.
3. Use **at least two Evolus building blocks**: workflows, document extractors, AI Tools, knowledge libraries, MCP connectors, sub-agents, chat widget.
4. **Drive Evolus from your app through its APIs**: the REST API for workflows, extractors, AI Tools and libraries, and agent chat through REST or the OpenAI-compatible endpoint.
5. Follow the general rules: **containerized app, public GitHub repo, a README that runs, no committed API keys** (use environment variables).

**Verification:** Evolus reviews each workspace's configuration and usage stats (model endpoint, building blocks used, API calls).

**Sample use cases:** invoice and order intake (PDF email → JSON → match → flag) · support desk over company knowledge with sources and escalation · lead qualification through a chat widget → CRM over MCP · contract review (clauses vs standard terms + redaction) · multilingual document translation that keeps layout · meeting follow-up (recording → minutes → action items).

**Track judging** (the four criteria applied to Evolus):
- Application of Technology: how deeply the solution uses Evolus blocks and how well the AMD-hosted model is integrated.
- Business Value: a real process, a clear user, a measurable gain.
- Originality: a new approach, or a process nobody has automated this way.
- Presentation: a clear demo and pitch.

**Evolus technical summary** (from evolus.ai/en/developers):
- Workspace: free until **15 Nov 2026 23:59 Italian time** (the lablab page says 31 Oct). Up to 6 members, **50,000 platform credits**, **60 API requests/min**, no card. Sign-in with GitHub, Google, Apple or Microsoft. 500 coupons are first come, first served (claim link on the event page).
- Model routes: **vLLM on AMD Developer Cloud** (`http://<droplet-ip>:8000/v1`) or Fireworks AI. Pick a model that supports function calling. Calls to your own model do not use Evolus credits.
- REST `https://api.evolus.ai/api/v1` with headers `X-ApiKey` and `X-Application-Id` (or `X-User-ApiKey`).
  - Workflows: `POST /workflows/{id}/execute` (multipart: `input`, files, `parameters`, `callbackUrl`) returns 202 with `executionId`. Poll `GET /workflows/{id}/executions/{executionId}` for Pending, Running, Completed or Failed. A workflow that is switched off returns 409.
  - Extractors: `POST /agents/{agentId}/json/{extractorId}/ask-file` (also `csv` or `text`, and `ask-files`; add `?useWebhook=false` to get the result in the response).
  - AI Tools (11): `doc-structure`, `tables`, `translate`, `anonymize`, `summarize`, `minutes`, `email`, `rewrite`, `simplify`, `sentiment`, `compare`. Endpoints: `POST /ai-tools/{tool}/run`, `/run-media`, `/run-file`, and `GET /ai-tools` for the catalog. Limits: 20 MB documents, 100 MB media, 120k characters.
  - Libraries (RAG): `POST /memories/{libraryId}/documents?language=en`, `/documents/import-url`.
- OpenAI-compatible agent chat: base `https://api.evolus.ai/v1`, `model = <applicationId>:<agentId>`, Bearer key. To continue a conversation, send `X-Conversation-Id` back. Temperature and similar parameters are ignored because the agent's settings apply.
- MCP server: `https://api.evolus.ai/mcp` (same headers). Evolus Studio is a coding agent built on OpenCode.
- When credits run out, Evolus returns 402.

## 6. Partners

- **AMD:** lead partner and **mandatory for all challenges**.
- **Google DeepMind (Gemma):** Gemma open models running on AMD GPUs through AMD Developer Cloud and ROCm. "Use Gemma in your project for a chance to win the Google prize." Docs: ai.google.dev/gemma/docs.
- **Vibe Generation:** founded by Paolo Bonetti. It builds hybrid human-plus-AI teams and processes and sponsors the four main tracks and a special prize.
- **Evolus AI** (Codedesign SRL, Taggia, Imperia, Italy): an agent platform for business processes.
- **PwC Italy**, **IMMENT** (startup creation, funding and management), **BAC Network** (outreach and co-investment): ecosystem partners.
- **NativelyAI:** lablab's parent company.

## 7. Prizes

| Prize | Value | Condition |
|-------|-------|-----------|
| AMD prizes | **$5,000** | Main challenge. The split across tracks and places is **not published**. |
| Google prizes | **$5,000** | Projects that **use Gemma** |
| Evolus track | 1st €578 (12 months Developer plan + 1M credits + showcase) · 2nd €289 (6 months + 500k) · 3rd €144.50 (3 months + 250k). Total €1,011.50 at list price. | Evolus track requirements |
| Vibe Generation special prize | AirPods 5 for **every** team member | Best solution, judged on three lenses: **Hybrid** (strategic thinking, quantified value, commercial attitude) · **Becreatives** (quality of technical execution, AI tool orchestration, ability to ship) · **Vibe Generation** (taste, originality, design of the human-plus-AI creative workflow) |
| Imment incubation | 3 × startup award program worth €1,599 + incubation | **Best Italian teams** |

- "Google and Evolus technologies are optional. A single project may qualify for the **main challenge prize, one partner prize, or both partner prizes**."
- Prizes can take **up to 90 days** to arrive. They are paid to **individuals** in USD. Non-US winners need a W-8BEN form, and 30% US withholding applies unless a tax treaty covers the winner.
- Rules, prizes and terms can change at lablab's discretion. Submissions must be **original work, open source, and MIT-License compliant**.

## 8. Judging criteria

The event's own wording:
1. **Application of Technology:** "How effectively the chosen model(s) are integrated into the solution."
2. **Presentation:** "The clarity and effectiveness of the project presentation."
3. **Business Value:** "The impact and practical value, considering how well it fits into business areas."
4. **Originality:** "The uniqueness and creativity of the solution, highlighting approaches and ability to demonstrate behaviors."

The lablab Rule Book scores each criterion **from 1 to 5**. Events can override this, but this event publishes no weights.

| Score | Presentation (PDF + video) | Business value | Application of technology | Originality |
|-------|----------------------------|----------------|---------------------------|-------------|
| 1 | No description of the problem | Little or no viability | **No demo video, no demo link, no GitHub** | Exact copy of an existing solution |
| 2 | Hard to understand. **Video shorter than 3 min** | Niche market, uncertain feasibility | Demo lacks full features, framework unclear, demo link or GitHub missing | Common idea |
| 3 | Problem, solution and value shown in **< 5 min**, but no market analysis, revenue model or future plans | Real need, revenue potential | All features shown, demo link works, GitHub partial | Some unique angle vs non-AI solutions (cost or time) |
| 4 | Same as 3, plus **market analysis, marketing and revenue, future goals and plans** | Clear market, large customer base, scalable | All features shown, **demo works smoothly, GitHub available and well thought out** | Unconventional methods, novel combinations |
| 5 | Flawless, with **competitive analysis** showing strengths and uniqueness | Disruptive, sustainable revenue | **Exceptional AI use** across demo, video and GitHub. Flawless implementation | Transformative, unprecedented approach |

**How-to-win guidance (lablab guide):**
- Video structure: 0:00–0:30 problem · 0:30–2:30 **live demo** · 2:30–4:00 business case, market size and revenue model · 4:00–5:00 team and roadmap.
- Business value: a specific user (not "everyone"), a rough TAM, at least one revenue model, and why this could not be built without AI.
- Application of technology: a **deployed, accessible demo URL** · a **GitHub repo with real commits spread across the event window** · AI that does more than wrap a chatbot.
- Originality: a fresh angle that only this generation of AI makes possible.
- Common ways to lose points: pivoting after hour 12 · a single final commit · a local-only demo (scored as not working) · over-engineering the LLM layer (five calls where one would do).
- Slides: 8 to 10 pages covering problem, solution, demo screenshot, market, revenue, team and next steps, with 2 or 3 sentences per slide. Include TAM/SAM, revenue streams, competitors with strengths, weaknesses and USP, and future prospects.

## 9. Submission requirements (exact limits)

| Field | Requirement |
|-------|-------------|
| Submission title | 5–50 characters, clear and descriptive |
| Short description | 50–255 characters |
| Long description | 600–2,000 characters covering the problem, the solution, who it is for and what makes it stand out (one guide says at least 100 words) |
| Track(s) | Select one or more of the event tracks |
| Technology and category tags | Choose from lablab.ai/tech (for example: AMD Developer Cloud, AMD ROCm, Gemma, Qwen, ...) |
| Participation mode | Online or onsite (hybrid event) |
| Cover image | 16:9. Optional in the generic rules, but listed by this event |
| Video presentation | **MP4 or MOV, ≤300 MB, under 5 min** (and over 3 min to avoid a score of 2). Introduce the problem, walk through the slides, then show the project working |
| Slide presentation | **PDF** |
| GitHub repository | **Public** (MIT, open source). If there are several repos, list them in README.md |
| Demo application platform | For example Streamlit, Replit, Vercel, Hugging Face Spaces |
| Demo application URL | **Required for interactive evaluation**. Must be live and reachable by judges |
| Additional info | For example, how the solution could scale beyond the hackathon |

Event-specific "What to submit" list: project title, short and long descriptions, selected challenge, technology tags, **working prototype**, cover image, demo video, pitch presentation, **clear explanation of the problem and intended user**.

## 10. Rules and conduct

- Failing to follow the submission guidelines can lower the score or lead to exclusion.
- Plagiarism, gaming the vote, tampering, unauthorized automation or fraud leads to disqualification.
- Organizers can participate but cannot win prizes. Mentors or organizers who participate cannot judge.
- Judges keep submissions confidential, declare conflicts and do not copy entry materials.
- Participation is voluntary, and no prize is guaranteed.

## 11. People

- **Speakers:** Andrea Marazzi · Maharshi Trivedi · Emmanuel Iriarte (RnD AI Lead).
- **Mentor:** Riccardo Benedetti.
- **Judges (40):** Vishal Punjabi, Piyush Dhar Diwan, Mohamed Ally Iddi, Vasu Raj Jain, Shalabh Gupta, Adarsh Naidu, Amit Gupta, Omer Shmarak, Anil Mandloi, Sriharsha Makineni, Arjun Gopichander Ravichander, Goutham Manian Subramanian, Sandeep Vattikuti, Shaktesh Pandey, Tingting Lin, Subhasis Kundu, Mahati Kumar, Rishabh Mehan, Suresh Kumar Gunasekaran, Kishore Dara, Urvi Bhanushali, Viresh Jivane, Victor Martins, Manasa Kumar, Ali Amjad, Ansh Bilimoria, Udit Gupta, Oscar Hong, Suneeth Maraboina, Nalini Garg, Ashish Garg, Ramachandra Nalam, Bhargavi Vepuri, Satish Kumar Madasamy, Antoine Balliet, Sachidananda Singh, Harshit Gupta, Mehul Vani, Neeharika Kompala, Yadla Niranjan.
- The judges are mostly industry engineers. Each one reviews many projects in a few minutes, so **the first 30 seconds of the video and the demo's opening screen matter most.**

## 12. Competitive landscape (live dashboard snapshot)

- Submissions by track: Intelligent Industry 5 · Reinvent Commerce 2 · New Kind of Experience 1 · Evolus 1 · Health 1. Most of the 1,291 teams will submit near the deadline.
- Technologies in use: AMD Developer Cloud (39), AMD ROCm (33), Qwen3 (15), Claude Code (12), AI/ML API (11), ChatGPT (11), Gemma (10), Codex (10), AgentOps (8), HuggingFace Hub (7), OpenAI (7), Gemini (6), Streamlit (6), DeepSeek V3 (5), Vercel (5).
- Existing submission titles: T2V · Text to Vision; DocuSwarm (parallel due diligence); Vyson FiscalRAG (cited tax answers); **LineGuard (predictive maintenance copilot)**; CertGate (steel certificates); Super Secure SYST (gas guardian); ClearCare; TestTrace Guard (RF test fault triage); **Compressor Maintenance Copilot**; SayAgain (radio read-backs); PROMETHEUS FORGE; Culltron CivicOps; Trycanari; KeyShield; **MachineSage (maintenance copilot)**; jarvis automations; **Industrial Fault Copilot**; PatientKeeper Retorno; ForgeSight AI; Why They Return; DossierMind; SortSmart Business Advisor; **FactoryPilot (maintenance agent on MI300X)**; NOAI+ (confidential files); IncidentLens; SupplyWatch; QuestBridge (quest localisation); MURPHY (procedure fuzzing); Chirak; OpenForge AI; **Clearsheet (discharge sheets)**; **DischargeDost (discharge)**; AuditPro Agent.
- **Saturated angles to avoid:** generic predictive-maintenance and maintenance copilots, and discharge-instruction simplifiers.

## 13. Conflicts and unknowns (resolve before relying on them)

| # | Item | Status |
|---|------|--------|
| U1 | Final deadline: 17 Oct 17:00 UTC timeline marker vs **18 Oct 10:00 UTC** schedule and `endAt` | Treat 17 Oct 17:00 UTC as the internal stop. Confirm on Discord |
| U2 | Global TokenFactory base URL, model catalog (is Gemma there?) and quotas | **Unknown.** Requires login at notebooks.amd.com/tokenfactory |
| U3 | How the AMD $5,000 is split (per track or overall) | Not published |
| U4 | Judging weights | Not published, so assume equal |
| U5 | Evolus workspace end date: 31 Oct (lablab) vs 15 Nov (evolus.ai) | Irrelevant for the hackathon window |
| U6 | AMD Developer Cloud credit approval time ("2–3 business days" on Evolus vs "no approval" in the lablab tutorial) | Do not depend on credits for the MVP |
| U7 | Evolus coupon link uses the `...act-ii` slug | Probably reused from ACT II. Verify before claiming |

## 14. Constraints derived for the constitution and spec

1. **Hard time box:** aim for a deployed MVP well before 17 Oct 17:00 UTC. Freeze features before recording the video. Do not pivot after the idea is locked.
2. **AMD visible and meaningful:** core inference runs on AMD (TokenFactory and/or vLLM on MI300X). The UI shows which model and hardware served each step, with latency and tokens.
3. **Provider-agnostic, OpenAI-compatible client:** base URL, key and model IDs come from environment variables. Use only the fields the gateway accepts. No secrets in the repo.
4. **Rate-limit resilience:** at most 8 concurrent calls and at most about 20 RPM. Honor `Retry-After` with exponential backoff and jitter. Cache golden-path results and serve them labeled as cached when the quota runs out.
5. **Judge-proof demo:** no login. Sample data preloaded with a one-click golden path. Deployed publicly and containerized (Dockerfile). A README that runs end to end.
6. **Open source:** MIT LICENSE. Dependencies under permissive licenses. Sample data and images are self-made or MIT-compatible.
7. **Trust by design:** cite evidence for every AI claim, show uncertainty and confidence, keep a human in the loop for high-risk outputs, and keep deterministic, explainable math for any prediction (the Commerce rule, applied everywhere).
8. **Gemma hook:** use a Gemma model served on AMD in at least one meaningful step if the catalog offers it (Google prize).
9. **Git hygiene:** small commits spread across the remaining window. Never commit `.env`.
10. **Presentation assets are deliverables:** a 3 to 5 min video, an 8 to 10 slide PDF, a 16:9 cover image, and a title, short description and long description within the character limits.

---
*Sources: lablab.ai event page and live dashboard, lablab Hackathon Rule Book, Submission Guide, Hackathon Guidelines, How to Win guide, lablab Terms §16–17, evolus.ai/en/developers, notebooks.amd.com/tokenfactory, the AMD Radeon Cloud docs (amd-aim.github.io/radeon-cloud-docs), and the lablab AMD Developer Cloud + vLLM tutorial.*
