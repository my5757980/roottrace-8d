"""Correlate the detected shift with maintenance/shift-log events (deterministic)."""

from __future__ import annotations

from datetime import datetime

from app.models import CorrelatedEvent, MaintenanceEvent

DEFAULT_WINDOW_H = 2.0


def correlate_events(events: list[MaintenanceEvent], cp_time: datetime | None,
                     window_h: float = DEFAULT_WINDOW_H) -> list[CorrelatedEvent]:
    if cp_time is None or not events:
        return []
    out = []
    for ev in events:
        delta_min = (ev.timestamp - cp_time).total_seconds() / 60.0
        if abs(delta_min) <= window_h * 60:
            out.append(CorrelatedEvent(event_id=ev.id, timestamp=ev.timestamp, type=ev.type,
                                       description=ev.description, delta_minutes=round(delta_min, 1)))
    return sorted(out, key=lambda c: (abs(c.delta_minutes), c.timestamp))
