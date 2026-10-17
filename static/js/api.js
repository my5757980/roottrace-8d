// Thin fetch helpers for the RootTrace 8D API.

async function request(method, url, body, isForm = false) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    if (isForm) {
      opts.body = body;
    } else {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(url, opts);
  let data = null;
  try { data = await res.json(); } catch { data = null; }
  if (!res.ok) {
    const err = new Error(data?.error?.message || `Request failed (${res.status})`);
    err.status = res.status;
    err.details = data?.error?.details || [];
    err.code = data?.error?.code;
    throw err;
  }
  return data;
}

export const api = {
  health: () => request("GET", "/api/health"),
  createSample: () => request("POST", "/api/cases/sample"),
  createCase: (form) => request("POST", "/api/cases", form, true),
  getCase: (id) => request("GET", `/api/cases/${encodeURIComponent(id)}`),
  analyze: (id, mode) => request("POST", `/api/cases/${encodeURIComponent(id)}/analyze`, { mode }),
  poll: (id) => request("GET", `/api/cases/${encodeURIComponent(id)}/analysis`),
  patchSection: (id, sid, body) => request("PATCH", `/api/cases/${encodeURIComponent(id)}/report/sections/${sid}`, body),
};
