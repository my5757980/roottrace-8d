import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import load_settings
from app.llm.mock import MockLLM
from app.main import create_app

SAMPLE = Path(__file__).resolve().parents[2] / "sample_case"
TOOL_CHANGE = datetime(2026, 10, 8, 14, 20)


@pytest.fixture()
def client():
    app = create_app(load_settings(), llm=MockLLM())
    with TestClient(app) as c:
        yield c


def wait_done(client, case_id, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get(f"/api/cases/{case_id}/analysis").json()
        if data["status"] != "running":
            return data
        time.sleep(0.05)
    raise AssertionError("analysis did not finish")


def test_health_reports_mock_mode(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["mode"] == "mock" and "MOCK" in h["provider"]


def test_golden_path_sample_case(client):
    case = client.post("/api/cases/sample").json()
    assert case["is_sample"] and case["images"] and case["events"]
    r = client.post(f"/api/cases/{case['id']}/analyze", json={"mode": "live"})
    assert r.status_code == 202
    data = wait_done(client, case["id"])
    assert data["status"] == "done", data.get("error")
    assert all(s["status"] == "done" for s in data["steps"]), [(s["name"], s["status"], s["message"]) for s in data["steps"]]

    spc = data["spc"]
    cp = datetime.fromisoformat(spc["change_point"]["timestamp"])
    assert abs((cp - TOOL_CHANGE).total_seconds()) <= 15 * 60
    cont = spc["containment"]
    assert set(spc["out_of_spec"]["lots"]).issubset(cont["lots"])
    assert (cp - datetime.fromisoformat(cont["start"])).total_seconds() <= 3600
    assert cont["n_out_of_spec"] == spc["out_of_spec"]["count"]
    assert {"L261008-B", "L261009-A"}.issubset(cont["lots"])

    assert any(c["type"] == "TOOL_CHANGE" for c in data["correlated_events"])
    report = data["report"]
    assert [s["id"] for s in report["sections"]] == [f"D{i}" for i in range(1, 9)]
    assert "Suspect lots" in report["sections"][2]["deterministic_block"]
    assert len([t for t in data["trace"] if t["step"] in {"complaint_facts", "defect_vision", "hypotheses", "draft_8d"}]) == 4
    assert data["hypotheses"] and all(h["supporting"] for h in data["hypotheses"])
    assert data["mode"] == "mock"


def test_analysis_conflict_and_cached_rules(client):
    case = client.post("/api/cases/sample").json()
    client.post(f"/api/cases/{case['id']}/analyze", json={"mode": "live"})
    second = client.post(f"/api/cases/{case['id']}/analyze", json={"mode": "live"})
    assert second.status_code in (202, 409)
    wait_done(client, case["id"])
    assert client.get("/api/cases/unknown-case-id-000000/analysis").status_code == 404


def test_section_review_flow(client):
    case = client.post("/api/cases/sample").json()
    client.post(f"/api/cases/{case['id']}/analyze", json={})
    wait_done(client, case["id"])
    url = f"/api/cases/{case['id']}/report/sections/D4"
    assert client.patch(url, json={"approved": True}).status_code == 422  # reviewer required
    r = client.patch(url, json={"approved": True, "reviewer": "QE Test"}).json()
    assert r["status"] == "approved" and r["approved_count"] == 1
    r = client.patch(url, json={"content": "- edited root cause 99.9999"}).json()
    assert r["status"] == "needs_reapproval" and "99.9999" in r["untraceable_numbers"]


def _upload(client, csv: bytes, **form):
    files = {"process_csv": ("data.csv", csv, "text/csv")}
    data = {"characteristic": "Bore", "value_column": "bore", "lsl": "9.7", "usl": "10.3",
            "complaint_text": "Customer rejected 12 parts from lot L3.", **form}
    return client.post("/api/cases", data=data, files=files)


def test_custom_case_upload_and_validation(client):
    from datetime import timedelta

    rows = ["timestamp,lot,bore"]
    t0 = datetime(2026, 1, 1)
    for i in range(120):
        v = 10.0 + (0.4 if i >= 80 else 0.0) + 0.01 * ((i * 7) % 5 - 2)
        rows.append(f"{t0 + timedelta(minutes=30 * i):%Y-%m-%d %H:%M},L{i // 16},{v:.3f}")
    good = ("\n".join(rows) + "\n").encode()
    r = _upload(client, good)
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    client.post(f"/api/cases/{cid}/analyze", json={"mode": "live"})
    data = wait_done(client, cid)
    assert data["spc"]["change_point"]["detected"]
    assert client.post(f"/api/cases/{cid}/analyze", json={"mode": "cached"}).status_code == 422

    bad = _upload(client, b"when,lot,bore\n2026-01-01,L1,1\n2026-01-02,L1,2\n")
    assert bad.status_code == 422 and "timestamp" in bad.json()["error"]["message"]
