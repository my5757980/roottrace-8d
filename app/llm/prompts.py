"""Prompt builders for the four AI steps. The model interprets computed facts; it never computes."""

from __future__ import annotations

import base64
import json

from app.models import FACT_NAMES, SECTION_TITLES

TAXONOMY = ["dimensional_not_visual", "scratch", "burr", "porosity", "crack", "discoloration_corrosion",
            "chatter_tool_marks", "contamination", "other"]

SYSTEM_BASE = (
    "You are RootTrace 8D, an assistant for supplier quality engineers in automotive and industrial "
    "manufacturing. You are precise, evidence-driven and never invent facts. Reply with ONE JSON object only, "
    "no prose, no markdown fences."
)


def complaint_facts_messages(complaint_text: str) -> list[dict]:
    schema = {
        "facts": [{"name": "<one of: " + ", ".join(FACT_NAMES) + ">", "value": "<value or 'not stated'>",
                   "quote": "<verbatim text from the complaint that supports the value, or empty>"}],
        "language": "<ISO code of the complaint language>",
        "summary": "<max 2 sentences in English>",
    }
    system = (SYSTEM_BASE + " Task: extract the key facts of a customer quality complaint. Return exactly one "
              "entry per fact name, in the listed order. Copy numbers, lot numbers and dates exactly as written. "
              "Deadlines are often relative (e.g. 'containment within 24 hours', '8D within 10 working days'): report them. "
              "If a fact is not in the text, use value 'not stated' and an empty quote. Translate values to "
              "English if needed but keep the quote in the original language.\nJSON schema:\n"
              + json.dumps(schema, ensure_ascii=False))
    return [{"role": "system", "content": system},
            {"role": "user", "content": "Customer complaint:\n<<<\n" + complaint_text + "\n>>>"}]


def _data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")


def defect_vision_messages(images: list[bytes], context: str) -> list[dict]:
    schema = {"findings": [{"image_index": 0, "defect_class": "<one of: " + ", ".join(TAXONOMY) + ">",
                            "confidence": "high|medium|low",
                            "observations": ["<short visual observation>"],
                            "description": "<1-2 sentences>",
                            "retake_suggestion": "<null or how to take a better photo>"}]}
    system = (SYSTEM_BASE + " Task: visual inspection of photos of a rejected machined metal part. For each image, "
              "classify the most relevant visible defect into exactly one taxonomy class and list what you can "
              "actually see (surface marks, burrs, tags, damage). A dimensional deviation (oversize/undersize) "
              "cannot be confirmed from a photo: if that is the complaint, say so and use "
              "'dimensional_not_visual' unless another defect is clearly visible. Do not guess beyond what is "
              "visible; use low confidence when unsure and suggest a retake.\nJSON schema:\n"
              + json.dumps(schema, ensure_ascii=False))
    content: list[dict] = [{"type": "text", "text": f"Context: {context}\nThere are {len(images)} image(s), "
                                                    "in order, index starting at 0."}]
    for jpeg in images:
        content.append({"type": "image_url", "image_url": {"url": _data_url(jpeg)}})
    return [{"role": "system", "content": system}, {"role": "user", "content": content}]


def hypotheses_messages(context: str, evidence_block: str) -> list[dict]:
    schema = {"hypotheses": [{"rank": 1, "category": "Man|Machine|Method|Material|Measurement|Environment",
                              "statement": "<specific, testable root-cause hypothesis>",
                              "supporting": ["<evidence ID>"], "contradicting": ["<evidence ID>"],
                              "confidence": "high|medium|low",
                              "verification": "<one concrete check that would confirm or reject it>"}]}
    system = (SYSTEM_BASE + " Task: propose 3 to 6 ranked root-cause hypotheses (Ishikawa 6M) for the quality "
              "problem, using ONLY the evidence items provided. Rules: cite evidence IDs exactly as given "
              "(e.g. S4, L6, P2, C3, I1) in 'supporting' and, where timing or data argue against a hypothesis, "
              "in 'contradicting'. Rank 1 = best supported. Prefer hypotheses that explain the timing of the "
              "detected shift. Include at least one hypothesis for the escape point (why the defect was not "
              "detected before shipment). Use confidence 'low' when evidence is thin. If you mention a number, "
              "copy it exactly from the evidence. Do not invent names, numbers or events.\nJSON schema:\n"
              + json.dumps(schema, ensure_ascii=False))
    user = f"Case:\n{context}\n\nEvidence items:\n{evidence_block}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def draft_8d_messages(context: str, containment_block: str, hypotheses_json: str, evidence_block: str) -> list[dict]:
    sections = [{"id": sid, "title": title, "content": "<3-8 lines, each starting with '- '>",
                 "evidence": ["<evidence ID>"]} for sid, title in SECTION_TITLES.items()]
    system = (SYSTEM_BASE + " Task: draft an 8D report for the supplier quality engineer to review and sign. "
              "Rules: (1) Use only the evidence items, the containment facts and the hypotheses provided. "
              "(2) Cite the evidence IDs each section relies on in its 'evidence' list. "
              "(3) Copy every number exactly as written in the evidence; never compute or estimate new numbers, and do not "
              "invent quantities, sample sizes, durations or percentages (write 'agreed sample size', 'next production runs', "
              "'agreed period' instead). "
              "(4) D3 MUST quarantine and sort exactly the suspect lots and time range from the containment facts, "
              "include stock at the plant, in transit and at the customer, and the customer notification. "
              "(5) D1: list roles only (quality engineer, production, maintenance, process engineering), no names. "
              "(6) D2: 5W2H (what, where, when, who, why it matters, how detected, how many). "
              "(7) D4: occurrence root cause and escape point from the top hypotheses, marked 'to be verified' "
              "with the verification steps. (8) D5-D7: concrete actions with owners as roles; D6 must use "
              "measurable acceptance checks (e.g. capability target from S0). (9) D8: closure placeholder. "
              "Keep the language clear and factual for a customer-facing report.\nJSON schema:\n"
              + json.dumps({"sections": sections}, ensure_ascii=False))
    user = (f"Case:\n{context}\n\nContainment facts (computed, use verbatim in D3):\n{containment_block}\n\n"
            f"Ranked hypotheses:\n{hypotheses_json}\n\nEvidence items:\n{evidence_block}")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
