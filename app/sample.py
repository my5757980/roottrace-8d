"""Bundled sample case and its recorded (cached) AMD run."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import ROOT_DIR
from app.ingest import normalize_image, parse_maintenance_log, parse_process_csv, read_complaint, summarize_dataset
from app.models import ColumnMap, SpecLimits
from app.store import Case, ImageInput, new_case_id

SAMPLE_DIR = ROOT_DIR / "sample_case"
CACHED_RUN = SAMPLE_DIR / "cached_run.json"


@dataclass
class SampleInputs:
    meta: dict[str, Any]
    spec: SpecLimits
    columns: ColumnMap
    baseline_end: datetime | None
    complaint: str
    images: list[tuple[str, bytes]]
    process_bytes: bytes
    maintenance_bytes: bytes


def load_sample_inputs(sample_dir: Path = SAMPLE_DIR) -> SampleInputs:
    meta = json.loads((sample_dir / "case.json").read_text(encoding="utf-8"))
    files = meta["files"]
    images = []
    for name in files.get("images", []):
        raw = (sample_dir / name).read_bytes()
        images.append((name, normalize_image(raw, name, "image/jpeg", 50 * 1024 * 1024)))
    baseline_end = datetime.fromisoformat(meta["baseline_end"]) if meta.get("baseline_end") else None
    return SampleInputs(
        meta={k: v for k, v in meta.items() if k not in {"spec", "columns", "files", "baseline_end"}},
        spec=SpecLimits(**meta["spec"]), columns=ColumnMap(**meta["columns"]), baseline_end=baseline_end,
        complaint=read_complaint((sample_dir / files["complaint"]).read_text(encoding="utf-8")),
        images=images, process_bytes=(sample_dir / files["process"]).read_bytes(),
        maintenance_bytes=(sample_dir / files["maintenance"]).read_bytes(),
    )


def build_case(inputs: SampleInputs, *, is_sample: bool = True, title: str | None = None) -> Case:
    df, params, warnings = parse_process_csv(inputs.process_bytes, inputs.columns)
    dropped = 0
    for w in warnings:
        if "dropped" in w:
            dropped = int(w.split()[0])
    events = parse_maintenance_log(inputs.maintenance_bytes)
    return Case(
        id=new_case_id(), is_sample=is_sample, title=title or inputs.meta.get("title", "Sample case"),
        meta=inputs.meta, spec=inputs.spec, columns=inputs.columns, baseline_end=inputs.baseline_end,
        complaint_text=inputs.complaint,
        images=[ImageInput(index=i, filename=name, data=data) for i, (name, data) in enumerate(inputs.images)],
        df=df, parameters=params, dataset_summary=summarize_dataset(df, inputs.columns, params, dropped),
        events=events, ingest_warnings=warnings,
    )


def load_cached_run(path: Path = CACHED_RUN) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or "steps" not in data:
        return None
    return data
