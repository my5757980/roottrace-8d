from datetime import datetime

import numpy as np
import pandas as pd

from app.correlate import correlate_events
from app.models import MaintenanceEvent
from app.spc import parameter_shifts

CP = datetime(2026, 10, 8, 14, 30)


def ev(i, ts, typ="NOTE"):
    return MaintenanceEvent(id=f"L{i}", timestamp=ts, type=typ, description=typ)


def test_event_in_window_matched_with_signed_delta():
    out = correlate_events([ev(1, datetime(2026, 10, 8, 14, 20), "TOOL_CHANGE"),
                            ev(2, datetime(2026, 10, 8, 14, 45), "FIRST_PIECE")], CP)
    assert [c.event_id for c in out] == ["L1", "L2"]
    assert out[0].delta_minutes == -10.0 and out[1].delta_minutes == 15.0


def test_event_outside_window_excluded_and_empty_log():
    assert correlate_events([ev(1, datetime(2026, 10, 8, 20, 0))], CP) == []
    assert correlate_events([], CP) == []
    assert correlate_events([ev(1, CP)], None) == []


def test_parameter_shift_reports_hours_from_cp():
    t = pd.date_range("2026-10-01 00:00", periods=400, freq="30min")
    rng = np.random.default_rng(2)
    coolant = np.where(t < pd.Timestamp("2026-10-06 00:00"), 7.5, 5.6) + rng.normal(0, 0.1, 400)
    df = pd.DataFrame({"_ts": t, "_v": 0.0, "_lot": "L", "coolant": coolant})
    cp = datetime(2026, 10, 5, 0, 0)
    (shift,) = parameter_shifts(df, ["coolant"], cp)
    assert shift.detected and shift.delta < -1.5
    assert abs(shift.hours_from_cp - 24.0) <= 0.5
