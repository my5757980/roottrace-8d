// RootTrace 8D UI controller: boot, analysis polling, review actions, custom case upload.
import { api } from "./api.js";
import * as R from "./render.js";

const $ = (id) => document.getElementById(id);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
};

const state = {
  health: null,
  case: null,
  analysis: null,
  report: null,
  polling: false,
  editing: new Set(),
  reviewer: store.get("rt_reviewer") || "",
  runVisible: true,
};

// ------------------------------------------------------------------ feedback
function toast(text, kind = "", ms = 4200) {
  const t = document.createElement("div");
  t.className = `toast ${kind}`;
  t.setAttribute("role", "status");
  t.innerHTML = `${R.icon(kind === "bad" ? "alert" : kind === "ok" ? "check" : "info")}<span>${text}</span>`;
  $("toasts").appendChild(t);
  setTimeout(() => t.remove(), ms);
}

function notice(text, kind = "") {
  const n = $("notice");
  if (!text) { n.hidden = true; return; }
  n.className = `notice ${kind}`;
  n.innerHTML = `${R.icon(kind === "bad" || kind === "warn" ? "alert" : "info")}<span>${text}</span>`;
  n.hidden = false;
}

function renderBadge() {
  const h = state.health;
  const badge = $("amdBadge");
  if (!h) { $("amdText").textContent = "Server unreachable"; return; }
  badge.classList.toggle("live", h.mode === "live");
  badge.classList.toggle("mock", h.mode !== "live");
  const small = window.innerWidth < 768;
  if (h.mode === "live") {
    $("amdText").innerHTML = small ? "<b>AMD live</b>"
      : `AI on <b>${R.esc(h.provider)}</b> · ${R.esc(h.models.text)}${h.models.vision !== h.models.text ? ` + ${R.esc(h.models.vision)}` : ""}`;
    badge.title = `${h.provider} · ${h.models.text} / ${h.models.vision}`;
  } else {
    $("amdText").innerHTML = small ? "<b>Mock mode</b>" : "<b>Mock mode (not AMD)</b>: no AMD key configured";
    badge.title = "No AMD endpoint configured on this server; AI steps use a deterministic stand-in.";
  }
}

// ------------------------------------------------------------------ buttons
function setButtons() {
  const running = state.analysis?.status === "running";
  const live = state.health?.mode === "live";
  const label = running ? "Analyzing…" : live ? "Analyze complaint on AMD" : "Analyze (mock mode)";
  const cachedOk = !!(state.health?.cached_run_available && state.case?.is_sample);
  for (const [btn, lbl] of [[$("btnAnalyze"), label], [$("btnAnalyzeMobile"), running ? "Analyzing…" : live ? "Analyze on AMD" : "Analyze (mock)"]]) {
    btn.disabled = running || !state.case;
    btn.querySelector(".lbl").textContent = lbl;
  }
  $("btnCached").disabled = running || !cachedOk;
  $("btnCached").hidden = !state.case?.is_sample || !state.health?.cached_run_available;
  $("btnCachedMobile").hidden = $("btnCached").hidden;
  $("btnCachedMobile").disabled = $("btnCached").disabled;
  $("btnSample").hidden = !!state.case?.is_sample;
  document.body.dataset.runState = running ? "running" : state.analysis ? state.analysis.status : "idle";
  syncMobileBar();
}

function syncMobileBar() {
  const small = window.innerWidth < 768;
  $("mobileBar").hidden = !small || state.runVisible || !state.case;
}

function modeNotice() {
  const a = state.analysis;
  if (!a) {
    if (state.health && state.health.mode !== "live") {
      notice("<b>Mock mode:</b> no AMD endpoint is configured on this server, so the AI steps use a deterministic stand-in."
        + (state.health?.cached_run_available ? " Use <b>Replay recorded AMD run</b> to see real AMD output." : ""), "warn");
    } else notice("");
    return;
  }
  const fallback = a.steps.filter((s) => s.source === "cached" && a.mode !== "cached");
  if (a.error && a.status !== "running") notice(R.esc(a.error), a.status === "failed" ? "bad" : "warn");
  else if (a.mode === "cached") {
    const rec = a.trace.find((t) => t.recorded_at)?.recorded_at;
    notice(`Replaying a <b>recorded AMD run</b>${rec ? ` from ${R.fmtT(rec)} UTC` : ""}. The statistics are recomputed live, and the AI outputs come from the recording.`);
  } else if (fallback.length) {
    notice(`Live AMD capacity was busy for ${fallback.length} step(s), so those steps came from the recorded AMD run.`, "warn");
  } else if (a.mode === "mock") {
    notice("<b>Mock mode:</b> the AI steps use a deterministic stand-in, <b>not AMD</b>. Configure the AMD endpoint for live runs.", "warn");
  } else notice("");
}

// ------------------------------------------------------------------ rendering
function renderAll() {
  const c = state.case;
  if (!c) return;
  const a = state.analysis;
  R.renderCase($("casePanel"), c, { onZoom: zoom });
  R.renderSteps($("steps"), a);
  R.renderProgress($("progress"), $("progressFill"), $("progressLabel"), a);
  R.renderKpis($("kpis"), a);
  R.renderFacts($("cardFacts"), a);
  R.renderDefect($("cardDefect"), a, c, { onZoom: zoom });
  R.renderSpc($("cardSpc"), a, c);
  R.renderEvents($("cardEvents"), a);
  R.renderHypotheses($("cardHyp"), a);
  renderReport();
  R.renderTrace($("cardTrace"), a, state.health);
  R.renderEvidence($("cardEvidence"), a);
  modeNotice();
  setButtons();
}

function renderReport() {
  R.renderReport($("cardReport"), state.analysis, state.report, state, {
    onReviewer: (name) => { state.reviewer = name.trim(); store.set("rt_reviewer", state.reviewer); },
    onPrint: () => window.open(`/report.html?case=${encodeURIComponent(state.case.id)}`, "_blank", "noopener"),
    onEdit: (sid) => { state.editing.add(sid); renderReport(); },
    onCancel: (sid) => { state.editing.delete(sid); renderReport(); },
    onSave: (sid, text) => patch(sid, { content: text, reviewer: state.reviewer || undefined }, () => {
      state.editing.delete(sid);
      toast(`${sid} saved. It now needs approval.`, "ok");
    }),
    onApprove: (sid, approved) => {
      const input = document.getElementById("reviewerName");
      const name = input?.value.trim() || state.reviewer;
      if (approved && !name) {
        toast("Enter your name as reviewer before approving.", "bad");
        input?.focus();
        return;
      }
      if (name) { state.reviewer = name; store.set("rt_reviewer", name); }
      patch(sid, { approved, reviewer: name || undefined }, () => toast(approved ? `${sid} approved by ${R.esc(name)}.` : `${sid} unapproved.`, approved ? "ok" : ""));
    },
  });
}

async function patch(sid, body, after) {
  try {
    const updated = await api.patchSection(state.case.id, sid, body);
    const idx = state.report.sections.findIndex((s) => s.id === sid);
    if (idx >= 0) state.report.sections[idx] = { ...state.report.sections[idx], ...updated };
    if (updated.reviewer) state.report.reviewer = updated.reviewer;
    if (after) after();
    renderReport();
  } catch (e) {
    toast(R.esc(e.message), "bad");
  }
}

// ------------------------------------------------------------------ actions
async function loadSample() {
  const c = await api.createSample();
  setCase(c);
}

function setCase(c) {
  state.case = c;
  state.analysis = c.analysis;
  state.report = c.report;
  state.editing.clear();
  renderAll();
}

async function analyze(mode) {
  if (!state.case || state.analysis?.status === "running") return;
  try {
    const a = await api.analyze(state.case.id, mode);
    state.analysis = a;
    state.report = a.report;
    state.editing.clear();
    renderAll();
    if (window.innerWidth < 1024) $("progress").scrollIntoView({ behavior: "smooth", block: "center" });
    await pollUntilDone();
    if (state.analysis?.status === "done") {
      toast(`8D draft ready in ${state.analysis.first_draft_seconds ?? state.analysis.elapsed_seconds}s. Review and approve each section.`, "ok");
    }
  } catch (e) {
    if (e.status === 404) { toast("Your session expired. Reloading the sample case…"); await loadSample(); return; }
    toast(R.esc(e.message), "bad");
    setButtons();
  }
}

async function pollUntilDone() {
  if (state.polling) return;
  state.polling = true;
  try {
    while (state.analysis?.status === "running") {
      await sleep(1500);
      const a = await api.poll(state.case.id);
      state.analysis = a;
      state.report = a.report;
      renderAll();
    }
  } catch (e) {
    toast(`Lost contact with the server: ${R.esc(e.message)}`, "bad");
  } finally {
    state.polling = false;
    setButtons();
  }
}

function zoom(src) {
  const box = document.createElement("div");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-label", "Defect photo");
  box.innerHTML = `<img src="${R.esc(src)}" alt="Defect photo, enlarged">`;
  const close = () => { box.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  box.addEventListener("click", close);
  document.addEventListener("keydown", onKey);
  document.body.appendChild(box);
}

// ------------------------------------------------------------------ custom case dialog
function wireDialog() {
  const dlg = $("newCaseDialog");
  const form = $("newCaseForm");
  const close = () => dlg.close();
  $("btnNew").addEventListener("click", () => { $("newCaseErrors").textContent = ""; dlg.showModal(); });
  $("newCaseCancel").addEventListener("click", close);
  $("newCaseClose").addEventListener("click", close);
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData();
    for (const field of form.elements) {
      if (!field.name) continue;
      if (field.type === "file") {
        for (const file of field.files) fd.append(field.name, file, file.name);
      } else if (String(field.value).trim() !== "") {
        fd.append(field.name, field.value.trim());
      }
    }
    $("newCaseSubmit").disabled = true;
    try {
      const c = await api.createCase(fd);
      dlg.close();
      setCase(c);
      toast("Your case is loaded. Press Analyze to run it.", "ok");
    } catch (e) {
      $("newCaseErrors").textContent = [e.message, ...(e.details || [])].join("\n");
    } finally {
      $("newCaseSubmit").disabled = false;
    }
  });
}

function wireResponsive() {
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((entries) => {
      state.runVisible = entries[0].isIntersecting;
      syncMobileBar();
    }, { threshold: 0.1 }).observe($("runActions"));
  }
  let lastSmall = window.innerWidth < 768;
  window.addEventListener("resize", () => {
    const small = window.innerWidth < 768;
    syncMobileBar();
    if (small !== lastSmall) { lastSmall = small; renderBadge(); }
  }, { passive: true });
}

async function boot() {
  try { state.health = await api.health(); } catch { state.health = null; }
  renderBadge();
  $("btnAnalyze").addEventListener("click", () => analyze("live"));
  $("btnAnalyzeMobile").addEventListener("click", () => analyze("live"));
  $("btnCached").addEventListener("click", () => analyze("cached"));
  $("btnCachedMobile").addEventListener("click", () => analyze("cached"));
  $("btnSample").addEventListener("click", () => { notice(""); loadSample(); });
  wireDialog();
  wireResponsive();
  // empty states before the first case loads
  R.renderFacts($("cardFacts"), null); R.renderDefect($("cardDefect"), null, null); R.renderEvents($("cardEvents"), null);
  R.renderHypotheses($("cardHyp"), null); R.renderTrace($("cardTrace"), null, null); R.renderEvidence($("cardEvidence"), null);
  try {
    await loadSample();
  } catch (e) {
    $("casePanel").innerHTML = `<div class="notice bad">${R.icon("alert")}<span>Could not load the sample case: ${R.esc(e.message)}</span></div>`;
  }
}

boot();
