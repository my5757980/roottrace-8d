"""Parsing and validation of case inputs. Every problem raises IngestError with an actionable message."""

from __future__ import annotations

import email
import io
from email import policy
from pathlib import PurePath

import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError

from app.models import ColumnMap, DatasetSummary, MaintenanceEvent

MAX_COMPLAINT_CHARS = 20_000
IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
TEXT_EXTS = {".txt", ".eml", ""}
MAX_IMAGE_SIDE = 1024


class IngestError(Exception):
    def __init__(self, message: str, details: list[str] | None = None, *, status: int = 422,
                 code: str = "invalid_input"):
        super().__init__(message)
        self.message = message
        self.details = details or []
        self.status = status
        self.code = code


def check_size(data: bytes, max_bytes: int, label: str) -> None:
    if len(data) > max_bytes:
        raise IngestError(f"{label} is {len(data) / 1_048_576:.1f} MB; the limit is {max_bytes / 1_048_576:.0f} MB.",
                          status=413, code="file_too_large")


def _read_csv(data: bytes, label: str) -> pd.DataFrame:
    if not data or not data.strip():
        raise IngestError(f"{label} is empty.")
    try:
        df = pd.read_csv(io.BytesIO(data), sep=None, engine="python")
    except Exception as exc:  # pandas raises many types
        raise IngestError(f"{label} could not be read as CSV.", [str(exc)[:200]]) from exc
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_process_csv(data: bytes, columns: ColumnMap) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Return (frame with _ts/_v/_lot columns sorted by time, parameter columns, warnings)."""
    df = _read_csv(data, "Process data file")
    required = [columns.timestamp, columns.lot, columns.value]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise IngestError(
            f"Process data is missing required column(s): {', '.join(missing)}.",
            [f"Columns found: {', '.join(df.columns) or '(none)'}",
             "Required: a timestamp column, a lot column and a numeric measurement column. "
             "Set the column names in the form if yours differ."],
        )
    warnings: list[str] = []
    ts = pd.to_datetime(df[columns.timestamp], errors="coerce", format="mixed")
    if getattr(ts.dt, "tz", None) is not None:
        ts = ts.dt.tz_convert(None)
    values = pd.to_numeric(df[columns.value], errors="coerce")
    valid = ts.notna() & values.notna()
    dropped = int((~valid).sum())
    if int(valid.sum()) < 2:
        raise IngestError(
            f"Process data has fewer than 2 rows with a valid timestamp and a numeric '{columns.value}'.",
            [f"{dropped} row(s) could not be parsed."],
        )
    out = df.loc[valid].copy()
    out["_ts"] = ts[valid].values
    out["_v"] = values[valid].astype(float).values
    out["_lot"] = out[columns.lot].astype(str).str.strip().values
    if not out["_ts"].is_monotonic_increasing:
        warnings.append("Rows were not in time order and have been sorted by timestamp.")
    out = out.sort_values("_ts", kind="mergesort").reset_index(drop=True)
    if dropped:
        warnings.append(f"{dropped} row(s) dropped: unparseable timestamp or non-numeric '{columns.value}'.")
    if columns.parameters:
        params = [p for p in columns.parameters if p in out.columns]
        absent = [p for p in columns.parameters if p not in out.columns]
        if absent:
            warnings.append(f"Parameter column(s) not found and ignored: {', '.join(absent)}.")
    else:
        skip = {columns.timestamp, columns.lot, columns.value}
        params = [c for c in out.columns if c not in skip and not c.startswith("_")
                  and pd.api.types.is_numeric_dtype(out[c])]
    for p in params:
        out[p] = pd.to_numeric(out[p], errors="coerce")
    return out, params, warnings


def summarize_dataset(df: pd.DataFrame, columns: ColumnMap, params: list[str], dropped: int) -> DatasetSummary:
    return DatasetSummary(
        rows=int(len(df)), dropped_rows=dropped,
        start=df["_ts"].iloc[0].to_pydatetime(), end=df["_ts"].iloc[-1].to_pydatetime(),
        lots=int(df["_lot"].nunique()), value_column=columns.value, parameters=params,
    )


def parse_maintenance_log(data: bytes | None) -> list[MaintenanceEvent]:
    if not data or not data.strip():
        return []
    df = _read_csv(data, "Maintenance log")
    lower = {c.lower(): c for c in df.columns}
    if "timestamp" not in lower or "description" not in lower:
        raise IngestError(
            "Maintenance log must have 'timestamp' and 'description' columns.",
            [f"Columns found: {', '.join(df.columns)}", "Optional columns: type, machine, shift, author."],
        )
    ts = pd.to_datetime(df[lower["timestamp"]], errors="coerce", format="mixed")
    df = df.assign(_ts=ts).dropna(subset=["_ts"]).sort_values("_ts", kind="mergesort").reset_index(drop=True)

    def col(row, name: str) -> str:
        key = lower.get(name)
        val = row[key] if key else ""
        return "" if val is None or (isinstance(val, float) and np.isnan(val)) else str(val).strip()

    events = []
    for i, row in df.iterrows():
        events.append(MaintenanceEvent(
            id=f"L{i + 1}", timestamp=row["_ts"].to_pydatetime(), type=col(row, "type") or "NOTE",
            machine=col(row, "machine"), description=col(row, "description"),
            shift=col(row, "shift"), author=col(row, "author"),
        ))
    return events


def normalize_image(data: bytes, filename: str, content_type: str | None, max_bytes: int) -> bytes:
    check_size(data, max_bytes, f"Image '{filename}'")
    ext = PurePath(filename or "").suffix.lower()
    if (content_type or "").lower() not in IMAGE_TYPES and ext not in IMAGE_EXTS:
        raise IngestError(f"Image '{filename}' has an unsupported type; use JPG or PNG.", code="unsupported_type")
    try:
        img = Image.open(io.BytesIO(data))
        img.draft("RGB", (MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))  # JPEG: decode at reduced scale, keeps memory low
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise IngestError(f"Image '{filename}' could not be decoded; use a JPG or PNG photo.",
                          code="unsupported_type") from exc
    img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def read_complaint(data: bytes | str | None, filename: str = "") -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        ext = PurePath(filename or "").suffix.lower()
        if ext not in TEXT_EXTS:
            raise IngestError(f"Complaint file '{filename}' must be .txt or .eml.", code="unsupported_type")
        if ext == ".eml":
            msg = email.message_from_bytes(data, policy=policy.default)
            body = msg.get_body(preferencelist=("plain",))
            text = body.get_content() if body is not None else ""
            header = "\n".join(f"{h}: {msg[h]}" for h in ("From", "Date", "Subject") if msg[h])
            data = f"{header}\n\n{text}".strip()
        else:
            data = data.decode("utf-8", errors="replace")
    text = data.replace("\r\n", "\n").strip()
    if len(text) > MAX_COMPLAINT_CHARS:
        raise IngestError(f"Complaint text is {len(text)} characters; the limit is {MAX_COMPLAINT_CHARS}.")
    return text
