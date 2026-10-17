import pytest

from app.models import Draft8D, DraftSection
from app.report import SectionUpdateError, apply_section_update, build_report


def report():
    draft = Draft8D(sections=[DraftSection(id="D1", content="- team", evidence=["S1", "X9"]),
                              DraftSection(id="D3", content="- contain", evidence=["S8"])])
    return build_report(draft, {"S1", "S8"}, "- Suspect lots: L1")


def test_build_fills_all_sections_and_filters_ids():
    r = report()
    assert [s.id for s in r.sections] == [f"D{i}" for i in range(1, 9)]
    assert r.sections[0].evidence == ["S1"]
    assert r.sections[2].deterministic_block == "- Suspect lots: L1"
    assert "Not drafted" in r.sections[4].content


def test_edit_then_approve_then_edit_needs_reapproval():
    r = report()
    s = apply_section_update(r, "D1", content="- new team")
    assert s.status == "edited" and s.edited
    s = apply_section_update(r, "D1", approved=True, reviewer="A. Engineer")
    assert s.status == "approved" and s.approved_by == "A. Engineer" and s.approved_at is not None
    s = apply_section_update(r, "D1", content="- changed again")
    assert s.status == "needs_reapproval" and s.approved_by is None
    assert r.approved_count == 0


def test_unapprove_returns_to_previous_state():
    r = report()
    apply_section_update(r, "D3", approved=True, reviewer="QE")
    s = apply_section_update(r, "D3", approved=False)
    assert s.status == "ai_draft"


def test_approval_requires_reviewer_and_unknown_section_errors():
    r = report()
    with pytest.raises(SectionUpdateError):
        apply_section_update(r, "D2", approved=True)
    with pytest.raises(KeyError):
        apply_section_update(r, "D9", approved=True, reviewer="x")
    apply_section_update(r, "D2", reviewer="QE")
    assert apply_section_update(r, "D2", approved=True).approved_by == "QE"
