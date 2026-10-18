// Rendering of the result panels. Pure functions over API data; app.js owns the state.
import { autoResizeChart, renderControlChart, RULE_COLORS } from "./chart.js";

export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const fmtT = (iso) => (iso ? String(iso).replace("T", " ").slice(0, 16) : "n/a");
export const decimalsFor = (sigma) => (sigma > 0 ? Math.min(6, Math.max(1, -Math.floor(Math.log10(sigma)) + 1)) : 4);
export const icon = (name, cls = "") => `<svg class="icon ${cls}" aria-hidden="true"><use href="#i-${name}"/></svg>`;

const specDecimals = (spec) => {
  const vals = [spec.lsl, spec.usl, spec.target].filter((v) => v != null);
  const d = Math.max(0, ...vals.map((v) => (String(v).split(".")[1] || "").length));
  return Math.min(4, Math.max(d, vals.length ? 3 : 0));
};

export function evidenceMap(a) {
  const m = {};
  (a?.evidence || []).forEach((e) => { m[e.id] = e.text; });
  return m;
}

export function chips(ids, map, cls = "") {
  return (ids || []).map((id) => `<span class="ev ${cls}" tabindex="0" title="${esc(map[id] || "unknown evidence")}">${esc(id)}</span>`).join("");
}

export function bullets(text) {
  const lines = String(text || "").split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return "";
  if (lines.every((l) => /^[-•*]\s/.test(l))) {
    return `<ul>${lines.map((l) => `<li>${esc(l.replace(/^[-•*]\s+/, ""))}</li>`).join("")}</ul>`;
  }
  return lines.map((l) => `<p style="margin:0 0 6px">${esc(l.replace(/^[-•*]\s*/, ""))}</p>`).join("");
}

function head(iconName, title, sub = "", meta = "", amd = false) {
  return `<div class="card-head">
    <span class="card-ico ${amd ? "amd-ico" : ""}">${icon(iconName)}</span>
    <div class="card-title"><h2>${title}</h2>${sub ? `<p>${sub}</p>` : ""}</div>
    ${meta ? `<div class="card-meta">${meta}</div>` : ""}
  </div>`;
}

function empty(iconName, text) {
  return `<div class="empty">${icon(iconName)}<span>${esc(text)}</span></div>`;
}

function stepFor(a, name) {
  return (a?.steps || []).find((s) => s.name === name);
}

function stepNote(a, name) {
  const st = stepFor(a, name);
  if (!st) return "";
  if (st.status === "failed") return `<div class="notice bad">${icon("alert")}<span>${esc(st.message || "Step failed")}</span></div>`;
  if (st.status === "skipped") return empty("info", st.message || "Skipped");
  if (st.status === "running" || st.status === "pending") {
    return `<div class="working">${icon("loader", "spin")}<span>${st.status === "running" ? "Running on AMD…" : "Waiting for earlier steps…"}</span></div>`;
  }
  return "";
}

export function srcBadge(source) {
  return source ? `<span class="src ${esc(source)}">${esc(source)}</span>` : "";
}

const td = (label, html, cls = "") => `<td data-label="${esc(label)}"${cls ? ` class="${cls}"` : ""}><span class="cell">${html}</span></td>`;
const UNIT_SUFFIX = [["_c", " (°C)"], ["_pct", " (%)"], ["_mm", " (mm)"], ["_count", " (count)"], ["_bar", " (bar)"], ["_rpm", " (rpm)"]];
export const prettyName = (n) => {
  for (const [suf, unit] of UNIT_SUFFIX) if (n.endsWith(suf)) return n.slice(0, -suf.length).replaceAll("_", " ") + unit;
  return n.replaceAll("_", " ");
};

// ------------------------------------------------------------------ case panel
export function renderCase(el, c, opts = {}) {
  const ds = c.dataset_summary;
  const m = c.meta || {};
  const spec = c.spec;
  const d = specDecimals(spec);
  const f = (v) => Number(v).toFixed(d);
  const lim = [spec.lsl != null ? `LSL ${f(spec.lsl)}` : "", spec.usl != null ? `USL ${f(spec.usl)}` : ""].filter(Boolean).join(" · ");
  const wide = window.innerWidth >= 1024;
  el.innerHTML = `
    <div class="case-head"><span class="eyebrow">Complaint case</span>${c.is_sample ? '<span class="chip">Sample</span>' : '<span class="chip">Your upload</span>'}</div>
    <h2 class="case-title">${esc(c.title)}</h2>
    <dl class="kv">
      ${m.customer ? `<dt>Customer</dt><dd>${esc(m.customer)}</dd>` : ""}
      ${m.part_number ? `<dt>Part</dt><dd>${esc(m.part_number)} · ${esc(m.part_name || "")}</dd>` : ""}
      ${m.machine ? `<dt>Machine</dt><dd>${esc(m.machine)}</dd>` : ""}
      <dt>Characteristic</dt><dd>${esc(spec.characteristic)} [${esc(spec.unit)}]</dd>
      <dt>Specification</dt><dd>${esc(lim || "not given")}${spec.target != null ? ` · target ${f(spec.target)}` : ""}</dd>
      <dt>Process data</dt><dd>${ds.rows} samples · ${ds.lots} lots<br><span class="mono">${fmtT(ds.start)} → ${fmtT(ds.end)}</span></dd>
      <dt>Shift log</dt><dd>${c.events.length} maintenance / shift events</dd>
    </dl>
    ${c.images.length ? `<div class="case-media">${c.images.map((im) =>
      `<button class="thumb" type="button" data-zoom="${esc(im.url)}" aria-label="Enlarge defect photo ${im.index + 1}"><img src="${esc(im.url)}" alt="Defect photo ${im.index + 1}" loading="lazy"></button>`).join("")}</div>` : ""}
    <details class="complaint-box" ${wide ? "open" : ""}>
      <summary>Customer complaint ${icon("chevron")}</summary>
      <pre>${esc(c.complaint_text)}</pre>
    </details>
    ${(c.ingest_warnings || []).length ? `<div class="chips">${c.ingest_warnings.map((w) => `<span class="chip">${esc(w)}</span>`).join("")}</div>` : ""}
  `;
  if (opts.onZoom) el.querySelectorAll("[data-zoom]").forEach((b) => b.addEventListener("click", () => opts.onZoom(b.dataset.zoom)));
}

// ------------------------------------------------------------------ steps, progress, KPIs
const STEP_ICON = { pending: "clock", running: "loader", done: "check", failed: "x", skipped: "info" };
export function renderSteps(el, a) {
  if (!a) { el.innerHTML = ""; return; }
  el.innerHTML = a.steps.map((s) => `
    <li class="step ${s.status}">
      <span class="ico">${icon(STEP_ICON[s.status] || "clock")}</span>
      <span class="step-body"><span class="step-name">${esc(s.label)}</span>${s.kind === "ai" ? '<span class="tag-ai">AI</span>' : ""}
        ${s.message ? `<span class="msg">${esc(s.message)}</span>` : ""}</span>
      <span>${srcBadge(s.source)}</span>
    </li>`).join("");
}

export function renderProgress(wrap, fill, label, a) {
  if (!a) { wrap.hidden = true; return; }
  const total = a.steps.length;
  const done = a.steps.filter((s) => ["done", "failed", "skipped"].includes(s.status)).length;
  wrap.hidden = false;
  fill.style.width = `${Math.round((done / total) * 100)}%`;
  label.textContent = a.status === "running" ? `${done} / ${total} steps` : (a.elapsed_seconds != null ? `Done in ${a.elapsed_seconds}s` : "Done");
}

export function renderKpis(el, a) {
  if (!a || (a.status === "running" && !a.spc)) { el.innerHTML = ""; return; }
  const spc = a.spc;
  const ai = (a.trace || []).filter((t) => t.status === "ok");
  const live = ai.filter((t) => t.source === "live").length;
  const cached = ai.filter((t) => t.source === "cached").length;
  const kpi = (v, l, cls = "") => `<div class="kpi ${cls}"><div class="v" title="${esc(v)}">${v}</div><div class="l">${l}</div></div>`;
  el.innerHTML = [
    kpi(a.first_draft_seconds != null ? `${a.first_draft_seconds}s` : "…", "time to first 8D draft", "accent"),
    kpi(spc?.containment?.lots?.length ?? "…", "suspect lots to contain", "alert"),
    kpi(spc ? `${spc.out_of_spec.count}` : "…", "samples out of spec"),
    kpi(a.mode === "mock" ? "Mock" : `${live + cached}/4`, a.mode === "mock" ? "AI steps (not AMD)" : `AI steps on AMD${cached ? ` · ${cached} cached` : ""}`),
  ].join("");
}

// ------------------------------------------------------------------ facts
export function renderFacts(el, a) {
  const h = (meta = "") => head("file", "Complaint facts", "Extracted with the verbatim source quote", meta, true);
  if (!a) { el.innerHTML = h() + empty("file", "Run the analysis to extract the facts of the complaint, each with its source quote."); return; }
  const f = a.complaint_facts;
  if (!f) { el.innerHTML = h() + stepNote(a, "complaint_facts"); return; }
  el.innerHTML = h(srcBadge(stepFor(a, "complaint_facts")?.source)) + `
    ${f.summary ? `<p class="summary">${esc(f.summary)}</p>` : ""}
    <div class="table-wrap rwrap"><table class="rtable"><thead><tr><th>Fact</th><th>Value</th><th>Source quote</th></tr></thead><tbody>
    ${f.facts.map((x) => `<tr>${td("Fact", `<b>${esc(x.name.replaceAll("_", " "))}</b>`)}
      ${td("Value", esc(x.value), x.value === "not stated" ? "not-stated" : "")}
      ${td("Quote", x.quote ? "“" + esc(x.quote) + "”" : "–", "q")}</tr>`).join("")}
    </tbody></table></div>`;
}

// ------------------------------------------------------------------ defect
export function renderDefect(el, a, c, opts = {}) {
  const h = (meta = "") => head("image", "Defect photo", "Classified by a vision model on AMD", meta, true);
  if (!a) { el.innerHTML = h() + empty("image", "The AMD-hosted vision model describes and classifies what is visible in the photo."); return; }
  const list = a.defect_findings || [];
  if (!list.length) { el.innerHTML = h() + stepNote(a, "defect_vision"); return; }
  el.innerHTML = h(srcBadge(stepFor(a, "defect_vision")?.source)) + list.map((d) => {
    const img = c.images[d.image_index];
    return `<div class="defect">
      ${img ? `<button class="defect-media" type="button" data-zoom="${esc(img.url)}" aria-label="Enlarge photo"><img src="${esc(img.url)}" alt="Defect photo ${d.image_index + 1}" loading="lazy"></button>` : "<div></div>"}
      <div>
        <div class="cls">${esc(d.defect_class.replaceAll("_", " "))} <span class="conf ${d.confidence}">${d.confidence} confidence</span></div>
        <p>${esc(d.description)}</p>
        <ul class="obs">${(d.observations || []).map((o) => `<li>${icon("check")}<span>${esc(o)}</span></li>`).join("")}</ul>
        ${d.retake_suggestion ? `<div class="flag" style="margin-top:8px">${icon("info")} Retake: ${esc(d.retake_suggestion)}</div>` : ""}
      </div>
    </div>`;
  }).join("");
  if (opts.onZoom) el.querySelectorAll("[data-zoom]").forEach((b) => b.addEventListener("click", () => opts.onZoom(b.dataset.zoom)));
}

// ------------------------------------------------------------------ SPC
function customerLots(a, c) {
  const fact = a?.complaint_facts?.facts?.find((f) => f.name === "lots");
  const text = `${fact?.value || ""} ${c?.complaint_text || ""}`;
  return new Set(text.match(/\b[A-Z]\d{6}-[A-Z]\b/g) || []);
}

let disposeChart = () => {};

export function renderSpc(el, a, c) {
  const h = head("activity", "Statistical process control", "Deterministic: no AI computes these numbers");
  disposeChart();
  if (!a || !a.spc) {
    el.innerHTML = h + empty("activity", "The control chart, Western Electric rules, Cp/Cpk, the detected shift and the containment range appear here.");
    return;
  }
  const spc = a.spc, spec = c.spec, L = spc.limits, cp = spc.change_point, o = spc.out_of_spec, ct = spc.containment;
  const d = decimalsFor(L?.sigma);
  const f = (x) => (x == null ? "n/a" : Number(x).toFixed(d));
  const capB = spc.capability.find((w) => w.label === "baseline");
  const capA = spc.capability.find((w) => w.label !== "baseline");
  const after = cp.detected ? spc.violations.filter((v) => v.index >= cp.index).length : spc.violations.length;
  const stat = (v, l, how, cls = "") => `<div class="stat"><div class="v ${cls}">${v}</div><div class="l">${l}</div>
    ${how ? `<details class="how"><summary>${icon("info")} How it's computed</summary><p>${esc(how)}</p></details>` : ""}</div>`;
  const claimed = customerLots(a, c);
  const unclaimed = ct.lots.filter((l) => !claimed.has(l)).length;
  el.innerHTML = h + `
    <div class="legend" aria-hidden="true">
      <span><i style="background:#475569"></i>${esc(spec.characteristic)}</span>
      <span><i style="background:#1d4ed8"></i>CL / UCL / LCL</span>
      <span><i style="background:#b91c1c"></i>USL / LSL</span>
      ${[1, 2, 3, 4].map((r) => `<span><i class="dotk" style="background:${RULE_COLORS[r]}"></i>WE rule ${r}</span>`).join("")}
      <span><i style="background:#fecaca;height:10px"></i>Suspect range</span>
      <span>▼ Log event</span>
    </div>
    <div class="chart-wrap" id="spcChart"></div>
    <div class="chart-hint">Hover or tap the points and ▼ markers for details.</div>
    <div class="stats">
      ${stat(L ? f(L.cl) : "n/a", `Centre line [${esc(spec.unit)}]`, spc.explanations.cl)}
      ${stat(L ? `${f(L.lcl)} – ${f(L.ucl)}` : "n/a", "Control limits (±3σ̂)", spc.explanations.sigma)}
      ${stat(cp.detected ? fmtT(cp.timestamp) : "None", "Detected process shift", cp.explanation, cp.detected ? "bad" : "ok")}
      ${stat(cp.detected ? `${cp.delta > 0 ? "+" : ""}${f(cp.delta)}` : "–", `Shift size [${esc(spec.unit)}]`, cp.detected ? `Mean ${f(cp.mean_before)} before → ${f(cp.mean_after)} after the shift.` : "")}
      ${stat(capB?.cpk != null ? capB.cpk.toFixed(2) : "n/a", "Cpk baseline", spc.explanations.capability, capB?.cpk >= 1.33 ? "ok" : "bad")}
      ${stat(capA?.cpk != null ? capA.cpk.toFixed(2) : "n/a", `Cpk ${esc(capA?.label || "after")}`, "Capability target is Cpk ≥ 1.33 for ongoing production.", capA?.cpk >= 1.33 ? "ok" : "bad")}
      ${stat(`${o.count} / ${spc.n_points}`, "Samples out of spec", o.count ? `Maximum ${f(o.max_value)}; first ${fmtT(o.first)}, last ${fmtT(o.last)}. ${spc.explanations.out_of_spec}` : spc.explanations.out_of_spec, o.count ? "bad" : "ok")}
      ${stat(`${after}`, cp.detected ? "Run-rule violations since the shift" : "Run-rule violations", spc.explanations.rules)}
    </div>
    ${ct.start ? `<div class="containment">
        <div class="containment-head">${icon("alert")}<div><b>Containment (computed):</b> quarantine and sort everything made from
        <span class="mono">${fmtT(ct.start)}</span> to <span class="mono">${fmtT(ct.end)}</span>, which is ${ct.n_samples} samples, ${ct.n_out_of_spec} of them out of spec.</div></div>
        <div class="lots">${ct.lots.map((l) => `<span class="lot ${claimed.has(l) ? "claimed" : ""}" title="${claimed.has(l) ? "Named by the customer" : "Suspect: not reported by the customer yet"}">${esc(l)}</span>`).join("")}</div>
        <div class="note">${esc(ct.rationale)}${claimed.size ? ` Filled lots were named by the customer. The other <b>${unclaimed}</b> are suspect and not reported yet.` : ""}</div>
      </div>`
      : `<div class="containment"><div class="containment-head">${icon("info")}<div>${esc(ct.rationale)}</div></div></div>`}
    ${(spc.warnings || []).map((w) => `<div class="notice warn" style="margin-top:10px">${icon("alert")}<span>${esc(w)}</span></div>`).join("")}
  `;
  const box = el.querySelector("#spcChart");
  const correlatedIds = (a.correlated_events || []).map((e) => e.event_id);
  const draw = (w) => renderControlChart(box, spc, spec, c.events, { correlatedIds, width: w - 8 });
  draw(box.clientWidth || 900);
  disposeChart = autoResizeChart(box, draw);
}

// ------------------------------------------------------------------ events
export function renderEvents(el, a) {
  const h = head("clock", "What changed at the shift?", "Maintenance log and machine parameters");
  if (!a || !a.spc) { el.innerHTML = h + empty("clock", "Log events around the detected shift and machine-parameter shifts appear here."); return; }
  const ev = a.correlated_events || [];
  const ps = a.parameter_shifts || [];
  el.innerHTML = h + `
    <h3>Log events within ±2 h of the shift</h3>
    ${ev.length ? `<div class="table-wrap rwrap"><table class="rtable"><thead><tr><th>ID</th><th>Time</th><th>Type</th><th>Event</th><th class="num">Δ vs shift</th></tr></thead><tbody>
      ${ev.map((e) => `<tr>${td("ID", `<span class="ev">${esc(e.event_id)}</span>`)}${td("Time", fmtT(e.timestamp), "nowrap mono")}
        ${td("Type", `<b>${esc(e.type)}</b>`)}${td("Event", esc(e.description))}
        ${td("Δ vs shift", `${e.delta_minutes > 0 ? "+" : ""}${e.delta_minutes} min`, "num")}</tr>`).join("")}
      </tbody></table></div>` : empty("info", "No log events close to the shift.")}
    <h3>Machine parameters</h3>
    ${ps.length ? `<div class="table-wrap rwrap"><table class="rtable"><thead><tr><th>Parameter</th><th>Own shift</th><th class="num">Mean before → after</th></tr></thead><tbody>
      ${ps.map((p) => `<tr>${td("Parameter", `<b>${esc(prettyName(p.name))}</b>`)}
        ${td("Own shift", p.detected ? `${fmtT(p.change_time)} <span class="chip">${p.hours_from_cp > 0 ? "+" : ""}${p.hours_from_cp} h</span>` : "None")}
        ${td("Before → after", p.mean_before_cp != null ? `${p.mean_before_cp.toFixed(2)} → ${p.mean_after_cp.toFixed(2)}` : "–", "num")}</tr>`).join("")}
      </tbody></table></div>` : empty("info", "No machine-parameter columns in the data.")}`;
}

// ------------------------------------------------------------------ hypotheses
export function renderHypotheses(el, a) {
  const h = (meta = "") => head("target", "Root-cause hypotheses (6M)", "Ranked; every claim cites its evidence", meta, true);
  if (!a) { el.innerHTML = h() + empty("target", "Ranked hypotheses across Man, Machine, Method, Material, Measurement and Environment appear here."); return; }
  const hs = a.hypotheses || [];
  if (!hs.length) { el.innerHTML = h() + stepNote(a, "hypotheses"); return; }
  const map = evidenceMap(a);
  el.innerHTML = h(srcBadge(stepFor(a, "hypotheses")?.source)) + hs.map((x) => `
    <div class="hyp ${x.unsupported ? "unsupported" : ""}">
      <div class="hyp-head"><span class="rank">${x.rank}</span><span class="cat">${esc(x.category)}</span>
        <span class="conf ${x.confidence}">${x.confidence}</span>${x.unsupported ? `<span class="flag">${icon("alert")} no valid evidence</span>` : ""}</div>
      <div class="stmt">${esc(x.statement)}</div>
      <div class="meta"><span>Supported by</span> ${chips(x.supporting, map) || "–"}${x.contradicting?.length ? `<span>· against</span> ${chips(x.contradicting, map, "contra")}` : ""}</div>
      ${x.verification ? `<div class="verify">${icon("shield")}<span>Verify: ${esc(x.verification)}</span></div>` : ""}
    </div>`).join("");
}

// ------------------------------------------------------------------ report (D1-D8)
export function renderReport(el, a, report, ui, hd) {
  const h = (meta = "") => head("clipboard", "8D report draft", "AI draft. The engineer edits and approves each section", meta, true);
  if (!a) { el.innerHTML = h() + empty("clipboard", "D1–D8 appear here, ready for engineer review, approval and PDF export."); return; }
  if (!report) { el.innerHTML = h() + (stepNote(a, "draft_8d") || empty("clock", "Waiting for earlier steps…")); return; }
  const map = evidenceMap(a);
  const approved = report.sections.filter((s) => s.status === "approved").length;
  el.innerHTML = h(srcBadge(stepFor(a, "draft_8d")?.source)) + `
    <div class="report-bar">
      <div class="reviewer"><label for="reviewerName">Reviewer</label>
        <input id="reviewerName" autocomplete="name" placeholder="Your name (required to approve)" value="${esc(ui.reviewer || "")}"></div>
      <button class="btn ghost small" id="btnPrint" type="button">${icon("printer")}<span>Printable report / PDF</span></button>
      <div class="approval-meter"><span>${approved}/8 approved</span><span class="meter"><span style="width:${(approved / 8) * 100}%"></span></span></div>
    </div>
    ${report.sections.map((s) => {
      const editing = ui.editing.has(s.id);
      return `<div class="d8 ${s.status === "approved" ? "approved" : ""}" data-sid="${s.id}">
        <div class="d8-head">
          <span class="d8-title">${esc(s.title)} <span class="status ${s.status}">${s.status.replace("_", " ")}</span></span>
          <span class="d8-chips">${chips(s.evidence, map)}
            ${(s.untraceable_numbers || []).length ? `<span class="flag" title="These numbers do not match any computed fact or input record">${icon("alert")} check: ${s.untraceable_numbers.map(esc).join(", ")}</span>` : ""}</span>
          <span class="d8-actions">
            ${s.approved_by ? `<span class="signed">${icon("check")} ${esc(s.approved_by)} · ${fmtT(s.approved_at)}</span>` : ""}
            ${editing ? "" : `<button class="btn ghost small" type="button" data-act="edit">${icon("edit")}<span>Edit</span></button>`}
            ${s.status === "approved" ? `<button class="btn ghost small" type="button" data-act="unapprove">Unapprove</button>`
              : `<button class="btn primary small" type="button" data-act="approve">${icon("check")}<span>Approve</span></button>`}
          </span>
        </div>
        <div class="d8-body">
          ${s.deterministic_block ? `<div class="det"><span class="det-label">Computed by RootTrace, not by the AI</span>${esc(s.deterministic_block)}</div>` : ""}
          ${editing ? `<textarea data-edit aria-label="Edit ${esc(s.title)}">${esc(s.content)}</textarea>
            <div class="btn-row" style="margin-top:8px;justify-content:flex-end"><button class="btn ghost small" type="button" data-act="cancel">Cancel</button>
            <button class="btn primary small" type="button" data-act="save">Save changes</button></div>` : bullets(s.content)}
        </div></div>`;
    }).join("")}`;
  el.querySelector("#reviewerName").addEventListener("change", (e) => hd.onReviewer(e.target.value));
  el.querySelector("#btnPrint").addEventListener("click", hd.onPrint);
  el.querySelectorAll(".d8").forEach((box) => {
    const sid = box.dataset.sid;
    box.querySelectorAll("[data-act]").forEach((btn) => btn.addEventListener("click", () => {
      const act = btn.dataset.act;
      if (act === "edit") hd.onEdit(sid);
      if (act === "cancel") hd.onCancel(sid);
      if (act === "save") hd.onSave(sid, box.querySelector("[data-edit]").value);
      if (act === "approve") hd.onApprove(sid, true);
      if (act === "unapprove") hd.onApprove(sid, false);
    }));
  });
}

// ------------------------------------------------------------------ trace + evidence
export function renderTrace(el, a, health) {
  const h = head("cpu", "AMD inference trace", esc(health?.provider || "Where each AI step ran"), "", true);
  if (!a) { el.innerHTML = h + empty("cpu", "Each AI step appears here with its provider, model, live or cached source, latency and tokens."); return; }
  const rows = a.trace || [];
  const total = rows.reduce((s, t) => s + (t.prompt_tokens || 0) + (t.completion_tokens || 0), 0);
  el.innerHTML = h + `
    ${rows.length ? `<div class="table-wrap rwrap"><table class="rtable table-min"><thead><tr><th>Step</th><th class="hide-sm">Provider</th><th>Model</th><th>Source</th>
      <th class="num">Latency</th><th class="num">Tokens in / out</th><th class="num hide-sm">Attempts</th><th>Status</th></tr></thead><tbody>
      ${rows.map((t) => `<tr>${td("Step", `<b>${esc(t.step.replaceAll("_", " "))}</b>`)}${td("Provider", esc(t.provider), "hide-sm")}${td("Model", esc(String(t.model).replace(/^[\w-]+\//, "")), "mono")}
        ${td("Source", `${srcBadge(t.source)}${t.recorded_at ? ` <span class="chip">recorded ${fmtT(t.recorded_at)}</span>` : ""}`)}
        ${td("Latency", `${(t.latency_ms / 1000).toFixed(1)} s`, "num")}
        ${td("Tokens", `${t.prompt_tokens ?? "–"} / ${t.completion_tokens ?? "–"}`, "num")}${td("Attempts", t.attempts, "num hide-sm")}
        ${td("Status", t.status === "ok" ? `<span class="conf high">ok</span>` : `<span class="flag">${esc(t.error || "error")}</span>`)}</tr>`).join("")}
      </tbody></table></div>` : `<div class="working">${icon("loader", "spin")}<span>Waiting for the first AI step…</span></div>`}
    <div class="total"><span>Run <b class="mono">${esc(a.run_id)}</b></span><span>Mode <b>${esc(a.mode)}</b></span>
      <span>${a.elapsed_seconds != null ? `Total <b>${a.elapsed_seconds} s</b>` : "Running…"}</span><span><b>${total}</b> tokens</span></div>`;
}

export function renderEvidence(el, a) {
  const h = head("database", "Evidence registry", "Every AI claim must cite these IDs; invented IDs are dropped");
  if (!a || !(a.evidence || []).length) { el.innerHTML = h + empty("database", "The facts the AI is allowed to use, with their citation IDs, appear after the analysis."); return; }
  const kinds = { spc: "SPC", parameter: "Machine", log: "Log", complaint: "Complaint", image: "Photo", standard: "Standard" };
  const wide = window.innerWidth >= 1024;
  el.innerHTML = h + `<details class="ev-details" ${wide ? "open" : ""}>
    <summary>${icon("chevron")}<span>${a.evidence.length} evidence items</span></summary>
    <ul class="ev-list">${a.evidence.map((e) => `<li><span class="ev">${esc(e.id)}</span><span class="ev-kind">${esc(kinds[e.kind] || e.kind)}</span><p>${esc(e.text)}</p></li>`).join("")}</ul>
  </details>`;
}
