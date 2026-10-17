"""8D report sections: build from the AI draft, and the engineer review state machine."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models import SECTION_TITLES, Draft8D, Report, ReportSection
from app.numbers import find_untraceable

MISSING_SECTION = "- Not drafted by the model: please complete this section."


class SectionUpdateError(ValueError):
    pass


def build_report(draft: Draft8D, valid_ids: set[str], containment_text: str) -> Report:
    by_id = {s.id: s for s in draft.sections}
    sections = []
    for sid, title in SECTION_TITLES.items():
        ds = by_id.get(sid)
        content = (ds.content or "").strip() if ds else ""
        content = content or MISSING_SECTION
        evidence = [e for e in (ds.evidence if ds else []) if e in valid_ids]
        sections.append(ReportSection(
            id=sid, title=title, content=content, ai_content=content, evidence=list(dict.fromkeys(evidence)),
            deterministic_block=containment_text if sid == "D3" else "",
        ))
    return Report(sections=sections)


def trace_numbers(report: Report, allowed: list[float]) -> None:
    for s in report.sections:
        s.untraceable_numbers = find_untraceable(s.content, [], allowed)


def apply_section_update(report: Report, section_id: str, *, content: str | None = None,
                         approved: bool | None = None, reviewer: str | None = None,
                         allowed: list[float] | None = None, now: datetime | None = None) -> ReportSection:
    section = next((s for s in report.sections if s.id == section_id), None)
    if section is None:
        raise KeyError(section_id)
    now = now or datetime.now(timezone.utc)
    if reviewer is not None and reviewer.strip():
        report.reviewer = reviewer.strip()[:80]

    if content is not None:
        new = content.strip()
        if not new:
            raise SectionUpdateError("Section content cannot be empty.")
        if new != section.content.strip():
            was_approved = section.status == "approved"
            section.content = new
            section.edited = True
            section.status = "needs_reapproval" if was_approved else "edited"
            if was_approved:
                section.approved_by, section.approved_at = None, None
            if allowed is not None:
                section.untraceable_numbers = find_untraceable(new, [], allowed)

    if approved is True:
        name = (reviewer or report.reviewer or "").strip()
        if not name:
            raise SectionUpdateError("Enter the reviewer name before approving a section.")
        section.status = "approved"
        section.approved_by, section.approved_at = name[:80], now
    elif approved is False and section.status in ("approved", "needs_reapproval"):
        section.status = "edited" if section.edited else "ai_draft"
        section.approved_by, section.approved_at = None, None
    return section
