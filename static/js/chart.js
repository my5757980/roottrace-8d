// SVG individuals control chart: data, CL/UCL/LCL, zones, spec limits, run-rule violations,
// change point, containment range and maintenance events. The chart is drawn at the container's
// real pixel width, so labels stay legible from phones to 4K screens, and it prints crisply.

const NS = "http://www.w3.org/2000/svg";
export const RULE_COLORS = { 1: "#dc2626", 2: "#ea580c", 3: "#d97706", 4: "#7c3aed" };

function el(name, attrs = {}, parent) {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

function title(node, text) {
  el("title", {}, node).textContent = text;
  return node;
}

const ms = (iso) => new Date(iso).getTime();
const fmtTime = (iso) => String(iso).replace("T", " ").slice(0, 16);

export function renderControlChart(container, spc, spec, events = [], opts = {}) {
  container.innerHTML = "";
  const s = spc?.series;
  if (!s || !s.t.length) {
    container.innerHTML = '<div class="empty">No data to plot.</div>';
    return;
  }
  const W = Math.max(300, Math.round(opts.width || container.clientWidth || 1000));
  const narrow = W < 560;
  const H = opts.height || Math.round(Math.min(380, Math.max(240, W * 0.4)));
  const fs = narrow ? 10.5 : 11.5;
  const m = { l: narrow ? 50 : 62, r: narrow ? 40 : 92, t: 30, b: 30 };
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img",
    "aria-label": `Individuals control chart of ${spec?.characteristic || "the measured characteristic"}`,
    style: "font-family: Inter, Segoe UI, Arial, sans-serif" });
  const times = s.t.map(ms);
  const t0 = times[0], t1 = times[times.length - 1] || t0 + 1;
  const L = spc.limits;
  const yVals = [...s.v];
  if (L) yVals.push(L.ucl, L.lcl);
  if (spec?.usl != null) yVals.push(spec.usl);
  if (spec?.lsl != null) yVals.push(spec.lsl);
  let y0 = Math.min(...yVals), y1 = Math.max(...yVals);
  const pad = (y1 - y0) * 0.08 || 1;
  y0 -= pad; y1 += pad;
  const pw = W - m.l - m.r, ph = H - m.t - m.b;
  const X = (t) => m.l + ((t - t0) / (t1 - t0 || 1)) * pw;
  const Y = (v) => m.t + (1 - (v - y0) / (y1 - y0 || 1)) * ph;
  const decimals = Math.max(1, Math.min(6, Math.ceil(-Math.log10((y1 - y0) / 6)) + 1));

  el("rect", { x: m.l, y: m.t, width: pw, height: ph, fill: "#fcfdfe", stroke: "#e2e8f0" }, svg);

  // containment range
  const c = spc.containment;
  if (c?.start && c?.end) {
    const xa = X(ms(c.start)), xb = X(ms(c.end));
    title(el("rect", { x: xa, y: m.t, width: Math.max(2, xb - xa), height: ph, fill: "#fee2e2", opacity: 0.6 }, svg),
      `Containment range ${fmtTime(c.start)} → ${fmtTime(c.end)}`);
    if (xb - xa > 70) {
      const yLsl = spec?.lsl != null ? Y(spec.lsl) - 6 : H - m.b - 7;
      const lbl = el("text", { x: xa + 6, y: Math.min(H - m.b - 7, yLsl), "font-size": fs, fill: "#b91c1c", "font-weight": 700 }, svg);
      lbl.textContent = xb - xa > 150 ? "SUSPECT RANGE: contain" : "SUSPECT";
    }
  }

  // y grid + ticks
  const yTicks = narrow ? 4 : 5;
  for (let i = 0; i <= yTicks; i++) {
    const v = y0 + ((y1 - y0) * i) / yTicks;
    const y = Y(v);
    el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, stroke: "#f1f5f9" }, svg);
    el("text", { x: m.l - 6, y: y + 4, "font-size": fs, "text-anchor": "end", fill: "#64748b" }, svg).textContent = v.toFixed(decimals);
  }
  // x ticks: days, spaced so labels never collide
  const day = 86400000;
  const days = Math.max(1, (t1 - t0) / day);
  const stepDays = Math.max(1, Math.ceil(days / Math.max(1, Math.floor(pw / 58))));
  const start = new Date(t0); start.setHours(0, 0, 0, 0);
  for (let t = start.getTime() + day; t < t1; t += stepDays * day) {
    const x = X(t);
    if (x < m.l + 10 || x > W - m.r - 10) continue;
    el("line", { x1: x, x2: x, y1: m.t, y2: H - m.b, stroke: "#f1f5f9" }, svg);
    const d = new Date(t);
    el("text", { x, y: H - m.b + 16, "font-size": fs, "text-anchor": "middle", fill: "#64748b" }, svg)
      .textContent = `${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  const hline = (v, color, dash, label, width = 1.4) => {
    if (v == null) return;
    const y = Y(v);
    el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, stroke: color, "stroke-width": width, "stroke-dasharray": dash || "" }, svg);
    const tx = el("text", { x: W - m.r + 5, y: y + 4, "font-size": fs, fill: color, "font-weight": 600 }, svg);
    tx.textContent = narrow ? label : `${label} ${v.toFixed(decimals)}`;
    title(tx, `${label} ${v.toFixed(decimals)}`);
  };
  if (L) {
    for (const z of ["pos1", "pos2", "neg1", "neg2"]) {
      const y = Y(L.zones[z]);
      el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, stroke: "#bfdbfe", "stroke-width": 0.8, "stroke-dasharray": "2 4" }, svg);
    }
    hline(L.cl, "#1d4ed8", "", "CL");
    hline(L.ucl, "#1d4ed8", "6 4", "UCL");
    hline(L.lcl, "#1d4ed8", "6 4", "LCL");
  }
  hline(spec?.usl, "#b91c1c", "3 3", "USL", 1.8);
  hline(spec?.lsl, "#b91c1c", "3 3", "LSL", 1.8);

  // data line
  const pts = s.v.map((v, i) => `${X(times[i]).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");
  el("polyline", { points: pts, fill: "none", stroke: "#475569", "stroke-width": narrow ? 0.9 : 1.1, opacity: 0.85, "stroke-linejoin": "round" }, svg);

  // flagged + out-of-spec points
  const usl = spec?.usl, lsl = spec?.lsl;
  const r = narrow ? 2.4 : 3.2;
  s.v.forEach((v, i) => {
    const rule = s.flags[i];
    const oos = (usl != null && v > usl) || (lsl != null && v < lsl);
    if (!rule && !oos) return;
    const cx = X(times[i]), cy = Y(v);
    const g = el("g", {}, svg);
    if (rule) el("circle", { cx, cy, r, fill: RULE_COLORS[rule] || "#dc2626" }, g);
    if (oos) el("circle", { cx, cy, r: r + 2.3, fill: "none", stroke: "#b91c1c", "stroke-width": 1.2 }, g);
    title(g, `${fmtTime(s.t[i])} · ${v.toFixed(decimals)} · lot ${s.lot[i]}${rule ? ` · WE rule ${rule}` : ""}${oos ? " · OUT OF SPEC" : ""}`);
  });

  // maintenance events
  const correlated = new Set(opts.correlatedIds || []);
  for (const ev of events) {
    const t = ms(ev.timestamp);
    if (t < t0 || t > t1) continue;
    const x = X(t);
    const hot = correlated.has(ev.id);
    const g = el("g", { style: "cursor: help" }, svg);
    el("path", { d: `M${x - 5},${m.t - 13} L${x + 5},${m.t - 13} L${x},${m.t - 4} Z`, fill: hot ? "#b91c1c" : "#94a3b8" }, g);
    if (hot) el("line", { x1: x, x2: x, y1: m.t, y2: H - m.b, stroke: "#b91c1c", "stroke-width": 0.8, "stroke-dasharray": "2 3" }, g);
    title(g, `${ev.id} · ${fmtTime(ev.timestamp)} · ${ev.type}: ${ev.description}`);
  }

  // change point
  const cp = spc.change_point;
  if (cp?.detected && cp.timestamp) {
    const x = X(ms(cp.timestamp));
    el("line", { x1: x, x2: x, y1: m.t, y2: H - m.b, stroke: "#0f172a", "stroke-width": 2 }, svg);
    const label = narrow ? `Shift ${fmtTime(cp.timestamp).slice(5)}` : `Shift ${fmtTime(cp.timestamp)}`;
    const right = x > m.l + pw * 0.62;
    const tx = el("text", { x: right ? x - 6 : x + 6, y: m.t + 15, "font-size": fs + 1, "font-weight": 700, fill: "#0f172a",
      "text-anchor": right ? "end" : "start", "paint-order": "stroke", stroke: "#fcfdfe", "stroke-width": 3 }, svg);
    tx.textContent = label;
  }
  container.appendChild(svg);
}

// Re-draw on container resize (debounced). Returns a disposer.
export function autoResizeChart(container, draw) {
  if (typeof ResizeObserver === "undefined") return () => {};
  let last = container.clientWidth;
  let timer = null;
  const ro = new ResizeObserver(() => {
    const w = container.clientWidth;
    if (!w || Math.abs(w - last) < 8) return;
    last = w;
    clearTimeout(timer);
    timer = setTimeout(() => draw(w), 120);
  });
  ro.observe(container);
  return () => { clearTimeout(timer); ro.disconnect(); };
}
