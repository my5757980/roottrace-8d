"""Deterministic mock provider for local development and tests. It is labelled MOCK (not AMD).

It reads the same prompts as a real model and builds schema-valid answers from the evidence block,
so the whole pipeline and UI can run without a key. It is never used in live mode.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import TypeVar

from pydantic import BaseModel

from app.models import FACT_NAMES, SECTION_TITLES, TraceEntry

T = TypeVar("T", bound=BaseModel)
MOCK_PROVIDER = "MOCK (not AMD)"

_EVID_RE = re.compile(r"^\[([A-Z]\d+)\]\s*(.+)$", re.M)


def _user_text(messages: list[dict]) -> str:
    parts = []
    for m in messages:
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            parts.extend(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
    return "\n".join(parts)


def _evidence(text: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _EVID_RE.finditer(text)}


def _find(ev: dict[str, str], *keywords: str, prefix: str | None = None) -> list[str]:
    out = []
    for k, v in ev.items():
        if prefix and not k.startswith(prefix):
            continue
        low = v.lower()
        if all(kw in low for kw in keywords):
            out.append(k)
    return out


def _first(m: re.Match | None, group: int = 0) -> str:
    return m.group(group).strip() if m else "not stated"


def mock_complaint_facts(text: str) -> dict:
    body = text.split("<<<", 1)[-1]
    lots = re.findall(r"\bL\d{6}-[A-C]\b", body)
    qty = re.search(r"\b(\d+)\s+(?:water pump housings|housings|parts|pieces|pcs)\b", body, re.I)
    meas = re.search(r"\d+\.\d+\s*[-–]\s*\d+\.\d+\s*mm", body)
    part_no = re.search(r"\b[A-Z]{2}-\d{4}\b", body)
    customer = re.search(r"Supplier Quality Engineer\s*[-–]\s*(.+)", body)
    received = re.search(r"received on\s+([^)\n]+)", body, re.I)
    deadline = re.search(r"within\s+24\s+hours", body, re.I)
    defect = re.search(r"press-fit force was below the minimum of [\d.]+\s*kN", body, re.I)
    values = {
        "customer": (_first(customer, 1), _first(customer)),
        "part_number": (_first(part_no), _first(part_no)),
        "part_name": ("water pump housing" if "water pump housing" in body.lower() else "not stated",
                      "water pump housings" if "water pump housings" in body.lower() else ""),
        "lots": (", ".join(dict.fromkeys(lots)) or "not stated", " and ".join(dict.fromkeys(lots))),
        "defect_description": (("Bearing bore oversize: " + _first(defect)) if defect else "not stated", _first(defect)),
        "quantity_affected": (_first(qty, 1), _first(qty)),
        "date_received": (_first(received, 1), _first(received)),
        "response_deadline": ("D3 containment within 24 hours" if deadline else "not stated", _first(deadline)),
        "customer_measurement": (_first(meas), _first(meas)),
    }
    facts = []
    for name in FACT_NAMES:
        v, q = values.get(name, ("not stated", ""))
        facts.append({"name": name, "value": v, "quote": "" if q == "not stated" else q})
    return {"facts": facts, "language": "en",
            "summary": "The customer rejected housings with an oversize bearing bore and requests containment and an 8D."}


def mock_defect(text: str) -> dict:
    n = int(_first(re.search(r"There are (\d+) image", text), 1)) if "There are" in text else 1
    findings = []
    for i in range(max(1, n)):
        findings.append({
            "image_index": i, "defect_class": "chatter_tool_marks", "confidence": "medium",
            "observations": ["regular circumferential marks on the bore wall", "red reject tag attached to the part",
                             "no cracks or porosity visible"],
            "description": "The bore wall shows a regular chatter pattern consistent with tool vibration or a "
                           "worn or mis-set boring tool; the oversize itself cannot be confirmed from the photo.",
            "retake_suggestion": None,
        })
    return {"findings": findings}


def mock_hypotheses(text: str) -> dict:
    ev = _evidence(text)
    shift = _find(ev, "shift detected", prefix="S")
    tool = _find(ev, "tool_change") + _find(ev, "boring bar")
    first_piece = _find(ev, "first-piece") + _find(ev, "first piece")
    handover = _find(ev, "warning line") + _find(ev, "no stop")
    coolant = _find(ev, "coolant", prefix="P") + _find(ev, "coolant", prefix="L")
    rules = _find(ev, "western electric", prefix="S")
    tool_life = _find(ev, "tool life", prefix="P")
    oos = _find(ev, "out of specification between", prefix="S")
    image = [k for k in ev if k.startswith("I")]
    uniq = lambda xs: list(dict.fromkeys(xs))  # noqa: E731
    hyps = [
        {"rank": 1, "category": "Machine",
         "statement": "Diameter offset error on the new boring bar after the tool change shifted the bore upward.",
         "supporting": uniq(shift + tool + tool_life + image)[:5], "contradicting": [], "confidence": "high",
         "verification": "Measure the BB-18 diameter on the presetter and compare it with the offset entered in the CNC."},
        {"rank": 2, "category": "Method",
         "statement": "The first-piece check after the tool change was not measured, so the offset error was released.",
         "supporting": uniq(first_piece + shift)[:4], "contradicting": [], "confidence": "high" if first_piece else "low",
         "verification": "Review the tool-change procedure and first-piece records for the last 20 tool changes."},
        {"rank": 3, "category": "Measurement",
         "statement": "Escape point: SPC warning points were recorded but the reaction plan was not triggered.",
         "supporting": uniq(handover + rules + oos)[:4], "contradicting": [], "confidence": "medium" if handover else "low",
         "verification": "Audit the SPC sheets and reaction-plan sign-offs for shifts after the change."},
        {"rank": 4, "category": "Material",
         "statement": "Low coolant concentration after the top-up affected cutting conditions.",
         "supporting": uniq(coolant)[:3], "contradicting": shift[:1], "confidence": "low",
         "verification": "Compare bore values just before and after the coolant top-up."},
    ]
    for h in hyps:
        if not h["supporting"]:
            h["supporting"] = list(ev)[:1]
            h["confidence"] = "low"
    return {"hypotheses": hyps}


def mock_draft(text: str) -> dict:
    ev = _evidence(text)
    block = text.split("Containment facts (computed, use verbatim in D3):", 1)[-1].split("Ranked hypotheses:", 1)[0].strip()
    shift = _find(ev, "shift detected", prefix="S")
    tool = _find(ev, "tool_change")
    oos = _find(ev, "out of specification between", prefix="S")
    contain = _find(ev, "containment range", prefix="S")
    first_piece = _find(ev, "first-piece")
    shift_txt = ev.get(shift[0], "") if shift else ""
    contents = {
        "D1": "- Supplier quality engineer (team leader)\n- Production supervisor CNC-07\n- Maintenance technician\n"
              "- Process engineer (machining)\n- Quality inspector (sorting)",
        "D2": f"- What: bearing bore oversize, low press-fit force at the customer\n- When: {shift_txt or 'see evidence'}\n"
              f"- How many: {ev.get(oos[0], 'see out-of-specification evidence') if oos else 'see evidence'}\n"
              "- How detected: customer press-fit station; supplier SPC data confirms the shift",
        "D3": f"- Quarantine and 100% sort all suspect lots at the plant, in transit and at the customer\n"
              f"- {ev.get(contain[0], block) if contain else block}\n"
              "- Notify the customer of the suspect lots and the sorting plan within the requested deadline",
        "D4": "- Occurrence (to be verified): diameter offset error after the boring bar change\n"
              f"- Escape (to be verified): first-piece check not measured{' (' + first_piece[0] + ')' if first_piece else ''}; "
              "SPC warning points not escalated\n- Verification: presetter measurement of the new tool, record review",
        "D5": "- Mandatory measured first-piece check after every tool change\n"
              "- Automatic SPC alarm with machine stop on run-rule violation",
        "D6": "- Implement the measured first-piece check and SPC alarm\n"
              "- Validate: capability study after the change must meet the S0 target\n"
              "- Monitor the next tool changes with the control chart",
        "D7": "- Update the control plan and PFMEA for the tool-change step\n"
              "- Apply the same rule to all boring operations\n- Share the lesson learned with all shifts",
        "D8": "- Closure after customer acceptance of the corrective actions\n- Recognise the team",
    }
    evidence = {"D2": shift + oos, "D3": contain, "D4": shift + tool + first_piece, "D6": ["S0"]}
    return {"sections": [{"id": sid, "title": title, "content": contents[sid], "evidence": evidence.get(sid, [])}
                         for sid, title in SECTION_TITLES.items()]}


class MockLLM:
    """Same interface as LLMClient.chat_json."""

    def __init__(self, delay_s: float = 0.0):
        self.delay_s = delay_s

    @property
    def source(self) -> str:
        return "mock"

    async def aclose(self) -> None:
        return None

    async def chat_json(self, role: str, messages: list[dict], schema: type[T], step: str, *,
                        max_tokens: int = 2000, temperature: float = 0.2) -> tuple[T, TraceEntry]:
        started = datetime.now(timezone.utc)
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        text = _user_text(messages)
        builders = {"complaint_facts": mock_complaint_facts, "defect_vision": mock_defect,
                    "hypotheses": mock_hypotheses, "draft_8d": mock_draft}
        data = builders[step](text)
        parsed = schema.model_validate(data)
        prompt_chars = sum(len(str(m.get("content", ""))) for m in messages)
        trace = TraceEntry(step=step, provider=MOCK_PROVIDER, model="mock-deterministic", source="mock",
                           started_at=started, latency_ms=int(self.delay_s * 1000),
                           prompt_tokens=prompt_chars // 4, completion_tokens=len(str(data)) // 4)
        return parsed, trace
