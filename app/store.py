"""In-memory case store: TTL expiry, LRU eviction, unguessable ids. Nothing is persisted."""

from __future__ import annotations

import asyncio
import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.models import (
    Analysis,
    ColumnMap,
    DatasetSummary,
    MaintenanceEvent,
    Report,
    SpecLimits,
)


@dataclass
class ImageInput:
    index: int
    filename: str
    data: bytes  # normalized JPEG


@dataclass
class Case:
    id: str
    is_sample: bool
    title: str
    meta: dict[str, Any]
    spec: SpecLimits
    columns: ColumnMap
    baseline_end: datetime | None
    complaint_text: str
    images: list[ImageInput]
    df: pd.DataFrame
    parameters: list[str]
    dataset_summary: DatasetSummary
    events: list[MaintenanceEvent]
    ingest_warnings: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analysis: Analysis | None = None
    report: Report | None = None
    task: asyncio.Task | None = None
    last_access: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


def new_case_id() -> str:
    return secrets.token_urlsafe(16)


class CaseStore:
    def __init__(self, ttl_s: int = 7200, max_cases: int = 300, clock=time.monotonic):
        self._ttl = ttl_s
        self._max = max_cases
        self._clock = clock
        self._cases: OrderedDict[str, Case] = OrderedDict()

    def __len__(self) -> int:
        return len(self._cases)

    def add(self, case: Case) -> Case:
        self.purge()
        case.last_access = self._clock()
        self._cases[case.id] = case
        self._cases.move_to_end(case.id)
        while len(self._cases) > self._max:
            _, evicted = self._cases.popitem(last=False)
            if evicted.task and not evicted.task.done():
                evicted.task.cancel()
        return case

    def get(self, case_id: str) -> Case | None:
        case = self._cases.get(case_id)
        if case is None:
            return None
        if self._clock() - case.last_access > self._ttl:
            self._cases.pop(case_id, None)
            return None
        case.last_access = self._clock()
        self._cases.move_to_end(case_id)
        return case

    def purge(self) -> int:
        now = self._clock()
        expired = [cid for cid, c in self._cases.items() if now - c.last_access > self._ttl]
        for cid in expired:
            case = self._cases.pop(cid)
            if case.task and not case.task.done():
                case.task.cancel()
        return len(expired)
