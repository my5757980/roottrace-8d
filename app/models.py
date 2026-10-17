"""Pydantic schemas for the domain, the AI step outputs and the HTTP API (see data-model.md)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Confidence = Literal["high", "medium", "low"]
Category6M = Literal["Man", "Machine", "Method", "Material", "Measurement", "Environment"]
DefectClass = Literal[
    "dimensional_not_visual",
    "scratch",
    "burr",
    "porosity",
    "crack",
    "discoloration_corrosion",
    "chatter_tool_marks",
    "contamination",
    "other",
]
SectionStatus = Literal["ai_draft", "edited", "approved", "needs_reapproval"]
StepStatus = Literal["pending", "running", "done", "failed", "skipped"]
StepSource = Literal["live", "cached", "mock", "computed"]

SECTION_TITLES: dict[str, str] = {
    "D1": "D1 · Team",
    "D2": "D2 · Problem description (5W2H)",
    "D3": "D3 · Interim containment",
    "D4": "D4 · Root cause (occurrence & escape)",
    "D5": "D5 · Permanent corrective actions",
    "D6": "D6 · Implementation & validation",
    "D7": "D7 · Prevention",
    "D8": "D8 · Closure & recognition",
}
FACT_NAMES = [
    "customer",
    "part_number",
    "part_name",
    "lots",
    "defect_description",
    "quantity_affected",
    "date_received",
    "response_deadline",
    "customer_measurement",
]


def _norm_confidence(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip().lower()
        for level in ("high", "medium", "low"):
            if v.startswith(level):
                return level
        if v in {"med", "moderate"}:
            return "medium"
    return value


_CATEGORY_ALIASES = {
    "man": "Man", "people": "Man", "operator": "Man", "manpower": "Man",
    "machine": "Machine", "equipment": "Machine",
    "method": "Method", "process": "Method", "procedure": "Method",
    "material": "Material", "materials": "Material",
    "measurement": "Measurement", "measure": "Measurement", "inspection": "Measurement",
    "environment": "Environment", "mother nature": "Environment", "milieu": "Environment",
}


def _norm_category(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip().lower()
        for key, cat in _CATEGORY_ALIASES.items():
            if v.startswith(key):
                return cat
    return value


_DEFECT_KEYWORDS = [
    ("dimension", "dimensional_not_visual"),
    ("chatter", "chatter_tool_marks"),
    ("tool mark", "chatter_tool_marks"),
    ("tool_mark", "chatter_tool_marks"),
    ("scratch", "scratch"),
    ("burr", "burr"),
    ("poros", "porosity"),
    ("crack", "crack"),
    ("corros", "discoloration_corrosion"),
    ("discolo", "discoloration_corrosion"),
    ("contamin", "contamination"),
]


def _norm_defect(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip().lower().replace("-", "_")
        allowed = DefectClass.__args__  # type: ignore[attr-defined]
        if v in allowed:
            return v
        for key, cls in _DEFECT_KEYWORDS:
            if key in v:
                return cls
        return "other"
    return value


# --------------------------------------------------------------------------- case inputs


class SpecLimits(BaseModel):
    characteristic: str = "Measured characteristic"
    unit: str = "mm"
    lsl: float | None = None
    usl: float | None = None
    target: float | None = None


class ColumnMap(BaseModel):
    timestamp: str = "timestamp"
    lot: str = "lot"
    value: str
    parameters: list[str] = Field(default_factory=list)


class MaintenanceEvent(BaseModel):
    id: str
    timestamp: datetime
    type: str = "NOTE"
    machine: str = ""
    description: str
    shift: str = ""
    author: str = ""


class DatasetSummary(BaseModel):
    rows: int
    dropped_rows: int
    start: datetime
    end: datetime
    lots: int
    value_column: str
    parameters: list[str]


class ImageMeta(BaseModel):
    index: int
    filename: str
    url: str


# --------------------------------------------------------------------------- SPC results


class Baseline(BaseModel):
    start: datetime
    end: datetime
    n: int
    mean: float
    sigma: float
    mr_bar: float


class Limits(BaseModel):
    cl: float
    ucl: float
    lcl: float
    sigma: float
    zones: dict[str, float]


class Violation(BaseModel):
    rule: int
    index: int
    timestamp: datetime
    value: float
    explanation: str


class CapabilityWindow(BaseModel):
    label: str
    n: int
    mean: float
    sigma: float
    cp: float | None
    cpk: float | None


class ChangePoint(BaseModel):
    detected: bool
    index: int | None = None
    timestamp: datetime | None = None
    last_good_timestamp: datetime | None = None
    mean_before: float | None = None
    mean_after: float | None = None
    delta: float | None = None
    t_stat: float | None = None
    explanation: str


class OutOfSpec(BaseModel):
    count: int
    first: datetime | None = None
    last: datetime | None = None
    lots: list[str] = Field(default_factory=list)
    max_value: float | None = None
    min_value: float | None = None


class Containment(BaseModel):
    start: datetime | None = None
    end: datetime | None = None
    lots: list[str] = Field(default_factory=list)
    n_samples: int = 0
    n_out_of_spec: int = 0
    rationale: str


class Series(BaseModel):
    t: list[str]
    v: list[float]
    lot: list[str]
    flags: list[int]
    downsampled: bool = False


class SPCResult(BaseModel):
    n_points: int
    n_dropped: int
    baseline: Baseline | None
    limits: Limits | None
    violations: list[Violation]
    rule_counts: dict[str, int]
    capability: list[CapabilityWindow]
    change_point: ChangePoint
    out_of_spec: OutOfSpec
    containment: Containment
    series: Series
    explanations: dict[str, str]
    warnings: list[str]


class ParameterShift(BaseModel):
    name: str
    detected: bool
    change_time: datetime | None = None
    mean_before: float | None = None
    mean_after: float | None = None
    delta: float | None = None
    hours_from_cp: float | None = None
    mean_before_cp: float | None = None
    mean_after_cp: float | None = None


class CorrelatedEvent(BaseModel):
    event_id: str
    timestamp: datetime
    type: str
    description: str
    delta_minutes: float


class EvidenceItem(BaseModel):
    id: str
    kind: Literal["spc", "parameter", "log", "complaint", "image", "standard"]
    text: str


# --------------------------------------------------------------------------- AI step outputs


class ComplaintFact(BaseModel):
    name: str
    value: str = "not stated"
    quote: str = ""

    @field_validator("value", "quote", mode="before")
    @classmethod
    def _to_str(cls, v: Any) -> Any:
        if v is None:
            return ""
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return str(v) if not isinstance(v, str) else v


class ComplaintFacts(BaseModel):
    facts: list[ComplaintFact]
    language: str = "en"
    summary: str = ""


class DefectFinding(BaseModel):
    image_index: int = 0
    defect_class: DefectClass
    confidence: Confidence
    observations: list[str] = Field(default_factory=list, max_length=8)
    description: str = ""
    retake_suggestion: str | None = None

    @field_validator("defect_class", mode="before")
    @classmethod
    def norm_defect_class(cls, v: Any) -> Any:
        return _norm_defect(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def norm_confidence(cls, v: Any) -> Any:
        return _norm_confidence(v)

    @field_validator("observations", mode="before")
    @classmethod
    def cap_observations(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [v]
        return v[:8] if isinstance(v, list) else v


class DefectFindings(BaseModel):
    findings: list[DefectFinding] = Field(min_length=1)


class Hypothesis(BaseModel):
    rank: int
    category: Category6M
    statement: str
    supporting: list[str] = Field(default_factory=list)
    contradicting: list[str] = Field(default_factory=list)
    confidence: Confidence
    verification: str = ""
    unsupported: bool = False

    @field_validator("category", mode="before")
    @classmethod
    def norm_category(cls, v: Any) -> Any:
        return _norm_category(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def norm_confidence(cls, v: Any) -> Any:
        return _norm_confidence(v)

    @field_validator("supporting", "contradicting", mode="before")
    @classmethod
    def norm_ids(cls, v: Any) -> Any:
        if v is None:
            return []
        if isinstance(v, str):
            v = [x for x in v.replace(";", ",").split(",")]
        return [str(x).strip().strip("[]") for x in v if str(x).strip()]


class HypothesesOut(BaseModel):
    hypotheses: list[Hypothesis] = Field(min_length=1, max_length=8)


class DraftSection(BaseModel):
    id: str
    title: str = ""
    content: str
    evidence: list[str] = Field(default_factory=list)

    @field_validator("id", mode="before")
    @classmethod
    def _norm_id(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip().upper()
            if v.startswith("D") and len(v) >= 2 and v[1].isdigit():
                return v[:2]
        return v

    @field_validator("evidence", mode="before")
    @classmethod
    def norm_evidence(cls, v: Any) -> Any:
        if v is None:
            return []
        if isinstance(v, str):
            v = v.replace(";", ",").split(",")
        return [str(x).strip().strip("[]") for x in v if str(x).strip()]

    @field_validator("content", mode="before")
    @classmethod
    def _content_str(cls, v: Any) -> Any:
        if isinstance(v, list):
            return "\n".join(f"- {x}" if not str(x).startswith("-") else str(x) for x in v)
        return v


class Draft8D(BaseModel):
    sections: list[DraftSection] = Field(min_length=1)


# --------------------------------------------------------------------------- report + run


class ReportSection(BaseModel):
    id: str
    title: str
    content: str
    ai_content: str = ""
    evidence: list[str] = Field(default_factory=list)
    status: SectionStatus = "ai_draft"
    edited: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None
    untraceable_numbers: list[str] = Field(default_factory=list)
    deterministic_block: str = ""


class Report(BaseModel):
    sections: list[ReportSection]
    reviewer: str | None = None

    @property
    def approved_count(self) -> int:
        return sum(1 for s in self.sections if s.status == "approved")


class StepState(BaseModel):
    name: str
    label: str
    kind: Literal["deterministic", "ai"]
    status: StepStatus = "pending"
    source: StepSource | None = None
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TraceEntry(BaseModel):
    step: str
    provider: str
    model: str
    source: Literal["live", "cached", "mock"]
    started_at: datetime
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    attempts: int = 1
    status: Literal["ok", "error"] = "ok"
    error: str | None = None
    recorded_at: datetime | None = None


class Analysis(BaseModel):
    run_id: str
    mode: Literal["live", "cached", "mock"]
    status: Literal["running", "done", "failed"] = "running"
    started_at: datetime
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    first_draft_seconds: float | None = None
    steps: list[StepState]
    spc: SPCResult | None = None
    parameter_shifts: list[ParameterShift] = Field(default_factory=list)
    correlated_events: list[CorrelatedEvent] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    complaint_facts: ComplaintFacts | None = None
    defect_findings: list[DefectFinding] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    trace: list[TraceEntry] = Field(default_factory=list)
    error: str | None = None

    def step(self, name: str) -> StepState:
        for s in self.steps:
            if s.name == name:
                return s
        raise KeyError(name)


class CaseView(BaseModel):
    id: str
    is_sample: bool
    title: str
    created_at: datetime
    meta: dict[str, Any]
    spec: SpecLimits
    columns: ColumnMap
    dataset_summary: DatasetSummary
    ingest_warnings: list[str]
    complaint_text: str
    images: list[ImageMeta]
    events: list[MaintenanceEvent]
    analysis: Analysis | None
    report: Report | None
