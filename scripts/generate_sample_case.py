"""Generate the bundled sample case (seeded, reproducible, self-made, MIT).

Story: water-pump housing AH-2207, bearing bore Ø42.000 +0.025/0 mm, machined on CNC-07.
At 2026-10-08 14:20 the boring bar is replaced (BB-17 -> BB-18) with a diameter offset error:
the bore steps up by +0.0085 mm and then drifts with insert wear. The first-piece check is done
"visually only" and warning points are ignored at shift handover. A coolant top-up on 2026-10-09
22:10 lowers concentration: a plausible but mistimed distractor. The customer complains about
two lots, while SPC shows many more suspect lots.

Usage: python scripts/generate_sample_case.py
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "sample_case"
SEED = 2207

START = datetime(2026, 9, 28, 6, 0)
END = datetime(2026, 10, 12, 5, 30)
STEP = timedelta(minutes=30)
TOOL_CHANGE = datetime(2026, 10, 8, 14, 20)
COOLANT_TOPUP = datetime(2026, 10, 9, 22, 10)
BASELINE_END = datetime(2026, 10, 4, 6, 0)

MU, SIGMA = 42.0125, 0.0022
STEP_SHIFT, DRIFT_PER_H = 0.0085, 0.00012
PARTS_PER_SAMPLE = 16  # ~112 s cycle time, one part gauged every 30 min


def shift_of(t: datetime) -> tuple[str, datetime]:
    """Shift letter and the calendar date the shift started (C runs 22:00-06:00)."""
    h = t.hour
    if 6 <= h < 14:
        return "A", t
    if 14 <= h < 22:
        return "B", t
    return "C", t if h >= 22 else t - timedelta(days=1)


def lot_of(t: datetime) -> str:
    letter, day = shift_of(t)
    return f"L{day:%y%m%d}-{letter}"


def generate_process(rng: np.random.Generator) -> list[dict]:
    rows = []
    t = START
    serial_by_day: dict[str, int] = {}
    tool_life = 3900
    tool_id = "BB-17"
    while t <= END:
        hours = (t - START).total_seconds() / 3600
        thermal = 0.0004 * math.sin(2 * math.pi * (t.hour + t.minute / 60 - 14) / 24)
        value = MU + thermal + rng.normal(0, SIGMA)
        if t > TOOL_CHANGE:
            if tool_id == "BB-17":
                tool_id, tool_life = "BB-18", 0
            value += STEP_SHIFT + DRIFT_PER_H * (t - TOOL_CHANGE).total_seconds() / 3600
        spindle = 31.0 + 0.6 * math.sin(2 * math.pi * (t.hour - 14) / 24) + rng.normal(0, 0.15)
        coolant = (7.5 if t < COOLANT_TOPUP else 5.6) + rng.normal(0, 0.12)
        tool_life += PARTS_PER_SAMPLE
        letter, day = shift_of(t)
        key = f"{day:%y%m%d}"
        serial_by_day[key] = serial_by_day.get(key, 0) + PARTS_PER_SAMPLE
        rows.append({
            "timestamp": t.strftime("%Y-%m-%d %H:%M"),
            "machine": "CNC-07",
            "shift": letter,
            "lot": lot_of(t),
            "part_serial": f"AH2207-{key}-{serial_by_day[key]:04d}",
            "bore_diameter_mm": f"{value:.4f}",
            "spindle_temp_c": f"{spindle:.2f}",
            "coolant_conc_pct": f"{coolant:.2f}",
            "tool_id": tool_id,
            "tool_life_count": tool_life,
        })
        _ = hours
        t += STEP
    return rows


MAINTENANCE = [
    ("2026-09-29 07:10", "CNC-07", "PM", "A", "M. Rossi", "Weekly PM: way lube level OK, chip conveyor cleaned."),
    ("2026-10-01 10:30", "CNC-07", "CALIBRATION", "A", "QA Lab", "Bore air gauge AG-3 mastered with setting ring 42.0125 mm, calibration OK."),
    ("2026-10-02 22:40", "CNC-07", "SHIFT_HANDOVER", "C", "D. Bianchi", "No issues. Bore SPC sheet in control."),
    ("2026-10-05 09:00", "CNC-07", "PM", "A", "M. Rossi", "Spindle bearing temperature check: 31 °C, within limits."),
    ("2026-10-06 18:15", "CNC-07", "SHIFT_HANDOVER", "B", "L. Conti", "Tool life counter BB-17 above 7,000 parts; replacement planned at 8,000."),
    ("2026-10-08 14:20", "CNC-07", "TOOL_CHANGE", "B", "L. Conti", "Boring bar BB-17 replaced with BB-18 (end of tool life). Diameter offset entered from presetter sheet."),
    ("2026-10-08 14:45", "CNC-07", "FIRST_PIECE", "B", "L. Conti", "First-piece check after tool change done visually only - CMM queue busy. Production released."),
    ("2026-10-08 22:05", "CNC-07", "SHIFT_HANDOVER", "B", "L. Conti", "Bore SPC: points above upper warning line. Waiting for quality engineer review; machine running."),
    ("2026-10-09 22:10", "CNC-07", "COOLANT", "C", "S. Greco", "Coolant tank topped up with water; concentration not re-measured after refill."),
    ("2026-10-10 06:05", "CNC-07", "SHIFT_HANDOVER", "C", "S. Greco", "Bore values high on SPC sheet, no stop. Lots L261009-C and L261010-A shipped to warehouse."),
    ("2026-10-11 13:30", "CNC-07", "STOPPAGE", "A", "M. Rossi", "Chip conveyor jam cleared (15 min stop)."),
]

COMPLAINT = """From: Giulia Ferri <g.ferri@ardena-motors.example>
To: Supplier Quality - Valtek Components <quality@valtek.example>
Date: Mon, 12 Oct 2026 08:40 +0200
Subject: 8D REQUEST - AH-2207 water pump housing - bore oversize - 37 parts rejected

Dear Valtek team,

during bearing press-fit at our station OP40 (Plant Torino Nord) we rejected 37 water pump housings,
part number AH-2207, because the press-fit force was below the minimum of 4.2 kN. Our CMM measured
the bearing bore at 42.027-42.031 mm against the drawing requirement 42.000 +0.025/0 mm.

The rejected parts come from your lots L261008-B and L261009-A (delivery note DN-55812, received on
10 Oct 2026). A photo of one rejected housing is attached.

Please:
- confirm containment (D3) within 24 hours, including stock in transit and at your plant;
- send the 8D report with the root cause (D4) within 10 working days.

Regards,
Giulia Ferri
Supplier Quality Engineer - Ardena Motors S.p.A.
"""


def _font(size: int):
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def render_photo(rng: np.random.Generator, path: Path) -> None:
    w, h = 1280, 960
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = 610.0, 470.0
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy)
    theta = np.arctan2(dy, dx)

    # workbench: dark rubber mat with grain
    bench = 46 + rng.normal(0, 6, (h, w)).astype(np.float32)
    img = np.stack([bench * 0.95, bench, bench * 1.08], axis=-1)

    # housing face: brushed aluminium with facing rings and top-left light
    light = 1.0 + 0.18 * (-(dx + dy) / 900.0)
    rings = 4.0 * np.sin(r * 0.9) + rng.normal(0, 3.0, (h, w))
    face = (172 + rings) * light
    face_mask = r <= 420
    for ch, tint in enumerate((0.98, 1.0, 1.03)):
        img[..., ch] = np.where(face_mask, face * tint, img[..., ch])

    # chamfer ring
    chamfer = (r > 205) & (r <= 222)
    for ch in range(3):
        img[..., ch] = np.where(chamfer, 205 * light, img[..., ch])

    # bore wall with regular chatter marks (72 lobes) + irregular wear streaks
    wall = (r > 150) & (r <= 205)
    chatter = 20.0 * np.sin(theta * 72.0) * np.exp(-((r - 178) / 22.0) ** 2)
    streak = 10.0 * np.sin(theta * 9.0 + 1.3) * (r - 150) / 55.0
    wall_val = (118 + chatter + streak + rng.normal(0, 4, (h, w))) * (0.75 + 0.35 * (r - 150) / 55.0)
    for ch in range(3):
        img[..., ch] = np.where(wall, wall_val, img[..., ch])

    # through hole
    hole = r <= 150
    hole_val = 18 + 10 * (r / 150.0)
    for ch in range(3):
        img[..., ch] = np.where(hole, hole_val, img[..., ch])

    # four bolt holes
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        bx, by = cx + 315 * math.cos(a), cy + 315 * math.sin(a)
        br = np.sqrt((xx - bx) ** 2 + (yy - by) ** 2)
        for ch in range(3):
            img[..., ch] = np.where(br <= 26, 30, np.where((br > 26) & (br <= 31), 150, img[..., ch]))

    arr = np.clip(img, 0, 255).astype(np.uint8)
    pil = Image.fromarray(arr, "RGB").filter(ImageFilter.GaussianBlur(0.6))
    draw = ImageDraw.Draw(pil)

    # red reject tag tied to the part
    tag = Image.new("RGBA", (360, 170), (200, 30, 36, 255))
    td = ImageDraw.Draw(tag)
    td.rectangle([6, 6, 353, 163], outline=(255, 255, 255, 255), width=3)
    td.text((22, 16), "REJECT", fill=(255, 255, 255, 255), font=_font(46))
    td.text((22, 76), "Lot L261009-A", fill=(255, 255, 255, 255), font=_font(28))
    td.text((22, 114), "OP40 press-fit low", fill=(255, 255, 255, 255), font=_font(24))
    tag = tag.rotate(-8, expand=True, resample=Image.BICUBIC)
    pil.paste(tag, (880, 700), tag)
    draw.line([(900, 735), (780, 640)], fill=(235, 235, 235), width=3)

    # scale bar
    draw.rectangle([60, 900, 260, 908], fill=(235, 235, 235))
    draw.text((60, 868), "20 mm", fill=(235, 235, 235), font=_font(24))
    pil.save(path, format="JPEG", quality=88)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    rows = generate_process(rng)
    header = list(rows[0].keys())
    with open(OUT / "process_data.csv", "w", encoding="utf-8", newline="\n") as f:
        f.write(",".join(header) + "\n")
        for row in rows:
            f.write(",".join(str(row[k]) for k in header) + "\n")

    with open(OUT / "maintenance_log.csv", "w", encoding="utf-8", newline="\n") as f:
        f.write("timestamp,machine,type,shift,author,description\n")
        for ts, machine, typ, shift, author, desc in MAINTENANCE:
            f.write(f'{ts},{machine},{typ},{shift},{author},"{desc}"\n')

    (OUT / "complaint.txt").write_text(COMPLAINT, encoding="utf-8", newline="\n")
    render_photo(rng, OUT / "defect_photo.jpg")

    case = {
        "title": "AH-2207 water pump housing: bearing bore oversize",
        "customer": "Ardena Motors S.p.A. (fictional)",
        "supplier": "Valtek Components (fictional)",
        "part_number": "AH-2207",
        "part_name": "Water pump housing",
        "machine": "CNC-07",
        "spec": {"characteristic": "Bearing bore diameter", "unit": "mm",
                 "lsl": 42.000, "usl": 42.025, "target": 42.0125},
        "columns": {"timestamp": "timestamp", "lot": "lot", "value": "bore_diameter_mm",
                    "parameters": ["spindle_temp_c", "coolant_conc_pct", "tool_life_count"]},
        "baseline_end": BASELINE_END.strftime("%Y-%m-%d %H:%M"),
        "files": {"complaint": "complaint.txt", "images": ["defect_photo.jpg"],
                  "process": "process_data.csv", "maintenance": "maintenance_log.csv"},
    }
    (OUT / "case.json").write_text(json.dumps(case, indent=2), encoding="utf-8", newline="\n")
    oos = sum(1 for r in rows if float(r["bore_diameter_mm"]) > 42.025 or float(r["bore_diameter_mm"]) < 42.0)
    print(f"wrote {len(rows)} process rows ({oos} out of spec), {len(MAINTENANCE)} log events, photo, case.json -> {OUT}")


if __name__ == "__main__":
    main()
