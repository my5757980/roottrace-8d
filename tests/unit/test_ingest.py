import io

import pytest
from PIL import Image

from app.ingest import IngestError, normalize_image, parse_maintenance_log, parse_process_csv, read_complaint
from app.models import ColumnMap

COLS = ColumnMap(value="bore")


def test_missing_value_column_names_the_column():
    data = b"timestamp,lot,other\n2026-01-01 10:00,L1,1\n2026-01-01 10:30,L1,2\n"
    with pytest.raises(IngestError) as err:
        parse_process_csv(data, COLS)
    assert "bore" in err.value.message


def test_non_numeric_rows_dropped_and_counted_and_sorted():
    data = (b"timestamp,lot,bore,temp\n2026-01-01 11:00,L1,42.01,30\n2026-01-01 10:00,L1,abc,30\n"
            b"2026-01-01 10:30,L1,42.02,31\n")
    df, params, warnings = parse_process_csv(data, COLS)
    assert len(df) == 2 and params == ["temp"]
    assert any("1 row(s) dropped" in w for w in warnings)
    assert any("sorted" in w for w in warnings)
    assert df["_ts"].is_monotonic_increasing


def test_mixed_timestamp_formats_parse():
    data = b"timestamp,lot,bore\n2026-01-01T10:00:00,L1,1.0\n2026/01/01 10:30,L1,1.1\n"
    df, _, _ = parse_process_csv(data, COLS)
    assert len(df) == 2


def test_image_wrong_type_and_oversize_rejected():
    with pytest.raises(IngestError):
        normalize_image(b"not an image", "x.gif", "image/gif", 10_000_000)
    with pytest.raises(IngestError) as err:
        normalize_image(b"0" * 2000, "big.jpg", "image/jpeg", 1000)
    assert err.value.status == 413


def test_image_normalized_to_bounded_jpeg():
    buf = io.BytesIO()
    Image.new("RGB", (3000, 1500), (200, 10, 10)).save(buf, format="PNG")
    out = normalize_image(buf.getvalue(), "p.png", "image/png", 10_000_000)
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG" and max(img.size) <= 1024


def test_eml_subject_and_body_extracted():
    eml = (b"From: a@b.example\r\nSubject: 8D REQUEST bore\r\nContent-Type: text/plain\r\n\r\n"
           b"37 housings rejected.\r\n")
    text = read_complaint(eml, "c.eml")
    assert "8D REQUEST bore" in text and "37 housings rejected." in text


def test_maintenance_log_requires_columns_and_assigns_ids():
    with pytest.raises(IngestError):
        parse_maintenance_log(b"when,what\n2026-01-01,x\n")
    events = parse_maintenance_log(b"timestamp,type,description\n2026-01-02 10:00,PM,b\n2026-01-01 10:00,TOOL,a\n")
    assert [e.id for e in events] == ["L1", "L2"] and events[0].description == "a"
