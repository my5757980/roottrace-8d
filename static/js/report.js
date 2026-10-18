// Printable 8D report: header + approval summary, facts, chart, hypotheses, D1-D8 (DRAFT watermark
// on unapproved sections), evidence table and AI trace appendix.
import { api } from "./api.js";
import { renderControlChart } from "./chart.js";
import { bullets, esc, fmtT } from "./render.js";

const root = document.getElementById("report");

async function main() {
  const id = new URLSearchParams(location.search).get("case");
  if (!id) { root.innerHTML = "<p>No case id given.</p>"; return; }
  let c;
  try { c = await api.getCase(id); } catch (e) { root.innerHTML = `<p>Could not load the case: ${esc(e.message)}</p>`; return; }
  const a = c.analysis, r = c.report;
  if (!a || !r) { root.innerHTML = "<p>Run the analysis first: there is no 8D draft for this case yet.</p>"; return; }
  const approved = r.sections.filter((s) => s.status === "approved").length;
  const facts = a.complaint_facts?.facts || [];
  const spc = a.spc;
  const today = new Date().toISOString().slice(0, 10);
  document.getElementById("toolbarNote").textContent = approved < 8 ? `${8 - approved} section(s) not approved: they print with a DRAFT mark.` : "All sections approved.";
  document.title = `8D ${c.meta?.part_number || ""} ${c.title}`.trim();

  root.innerHTML = `
    <div class="head">
      <div><h1>8D Report: ${esc(c.title)}</h1>
        <div class="muted">${esc(c.meta?.customer || "")} ${c.meta?.part_number ? "· " + esc(c.meta.part_number) : ""} ${c.meta?.machine ? "· " + esc(c.meta.machine) : ""}</div></div>
      <div class="meta">Case ${esc(c.id.slice(0, 8))} · ${today}<br>Reviewer: ${esc(r.reviewer || "not set")}<br>
        <span class="approval ${approved === 8 ? "full" : "partial"}">${approved}/8 sections approved</span></div>
    </div>

    <h2>Complaint facts</h2>
    <div class="table-scroll"><table><tr><th>Fact</th><th>Value</th><th>Source quote</th></tr>
      ${facts.map((f) => `<tr><td>${esc(f.name.replaceAll("_", " "))}</td><td>${esc(f.value)}</td><td>${f.quote ? "“" + esc(f.quote) + "”" : ""}</td></tr>`).join("")}
    </table></div>

    <h2>Process data: ${esc(c.spec.characteristic)}</h2>
    <div class="chart" id="chart"></div>
    ${spc?.containment?.start ? `<p><b>Containment range (computed):</b> ${fmtT(spc.containment.start)} → ${fmtT(spc.containment.end)} · lots ${spc.containment.lots.map(esc).join(", ")}</p>` : ""}

    <h2>Root-cause hypotheses</h2>
    <div class="table-scroll"><table><tr><th>#</th><th>6M</th><th>Hypothesis</th><th>Evidence</th><th>Confidence</th><th>Verification</th></tr>
      ${(a.hypotheses || []).map((h) => `<tr><td>${h.rank}</td><td>${esc(h.category)}</td><td>${esc(h.statement)}</td>
        <td>${h.supporting.map((x) => `<span class="ev">${esc(x)}</span>`).join("")}${h.contradicting.length ? "<br>against: " + h.contradicting.map((x) => `<span class="ev">${esc(x)}</span>`).join("") : ""}</td>
        <td>${esc(h.confidence)}</td><td>${esc(h.verification)}</td></tr>`).join("")}
    </table></div>

    <h2>8D</h2>
    ${r.sections.map((s) => `<div class="section ${s.status === "approved" ? "" : "draft"}">
      <h3><span>${esc(s.title)}</span><span class="sig">${s.status === "approved" ? `Approved by ${esc(s.approved_by)} · ${fmtT(s.approved_at)}` : "Not approved"}</span></h3>
      ${s.deterministic_block ? `<div class="det">${esc(s.deterministic_block)}</div>` : ""}
      ${bullets(s.content)}
      ${s.evidence.length ? `<div>${s.evidence.map((x) => `<span class="ev">${esc(x)}</span>`).join("")}</div>` : ""}
      ${(s.untraceable_numbers || []).length ? `<div class="flag">Numbers to verify: ${s.untraceable_numbers.map(esc).join(", ")}</div>` : ""}
    </div>`).join("")}

    <h2>Evidence registry</h2>
    <div class="table-scroll"><table><tr><th>ID</th><th>Fact</th></tr>${(a.evidence || []).map((e) => `<tr><td><span class="ev">${esc(e.id)}</span></td><td>${esc(e.text)}</td></tr>`).join("")}</table></div>

    <h2>Appendix: AI inference trace</h2>
    <div class="table-scroll"><table><tr><th>Step</th><th>Provider</th><th>Model</th><th>Source</th><th>Latency</th><th>Tokens in/out</th></tr>
      ${(a.trace || []).map((t) => `<tr><td>${esc(t.step)}</td><td>${esc(t.provider)}</td><td>${esc(String(t.model).replace(/^[\w-]+\//, ""))}</td><td>${esc(t.source)}${t.recorded_at ? " (recorded " + fmtT(t.recorded_at) + ")" : ""}</td>
        <td>${(t.latency_ms / 1000).toFixed(1)} s</td><td>${t.prompt_tokens ?? "–"} / ${t.completion_tokens ?? "–"}</td></tr>`).join("")}
    </table></div>
    <div class="foot">Generated with RootTrace 8D. Statistics are computed deterministically; AI-written sections are drafts until approved by the responsible engineer. Run ${esc(a.run_id)} · mode ${esc(a.mode)}.</div>
  `;
  renderControlChart(document.getElementById("chart"), spc, c.spec, c.events,
    { correlatedIds: (a.correlated_events || []).map((e) => e.event_id), height: 330 });
}

main();
