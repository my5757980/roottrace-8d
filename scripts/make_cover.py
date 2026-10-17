"""Render the 16:9 submission cover image (docs/submission/cover.png) from the sample case."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "submission" / "cover.png"
W, H = 1920, 1080


def font(size: int, bold: bool = False):
    names = (["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold
             else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), (11, 18, 32))
    d = ImageDraw.Draw(img)
    for y in range(H):  # subtle vertical gradient
        c = int(11 + 14 * y / H)
        d.line([(0, y), (W, y)], fill=(c, c + 7, c + 21))

    # title block
    d.rounded_rectangle([110, 120, 190, 200], radius=18, fill=(15, 118, 110))
    d.text((150, 160), "RT", font=font(40, True), fill="white", anchor="mm")
    d.text((220, 118), "RootTrace 8D", font=font(92, True), fill="white")
    d.text((115, 250), "Complaint → evidence-backed 8D in minutes",
           font=font(46), fill=(204, 251, 241))
    bullets = ["Deterministic SPC finds the shift and the suspect lots",
               "AI on AMD drafts D1–D8 and cites every fact",
               "The engineer approves; nothing is invented"]
    for i, b in enumerate(bullets):
        y = 360 + i * 64
        d.ellipse([118, y + 14, 134, y + 30], fill=(20, 184, 166))
        d.text((150, y), b, font=font(36), fill=(229, 231, 235))
    d.rounded_rectangle([115, 590, 720, 650], radius=30, fill=(17, 26, 46), outline=(225, 29, 46), width=3)
    d.ellipse([140, 610, 160, 630], fill=(225, 29, 46))
    d.text((178, 600), "AI inference on AMD Instinct GPUs", font=font(30, True), fill="white")

    # mini control chart from the sample data
    rows = list(csv.DictReader(open(ROOT / "sample_case" / "process_data.csv", encoding="utf-8")))
    vals = [float(r["bore_diameter_mm"]) for r in rows]
    x0, y0, x1, y1 = 110, 700, 1180, 1000
    d.rounded_rectangle([x0 - 10, y0 - 10, x1 + 10, y1 + 10], radius=16, fill=(248, 250, 252))
    lo, hi = 41.998, 42.036

    def Y(v):
        return y1 - (v - lo) / (hi - lo) * (y1 - y0)

    n = len(vals)
    cp = next(i for i, r in enumerate(rows) if r["timestamp"] >= "2026-10-08 14:30")
    d.rectangle([x0 + (cp - 1) / n * (x1 - x0), y0, x1, y1], fill=(254, 226, 226))
    for v, col in ((42.025, (185, 28, 28)), (42.0, (185, 28, 28))):
        d.line([(x0, Y(v)), (x1, Y(v))], fill=col, width=3)
    pts = [(x0 + i / (n - 1) * (x1 - x0), Y(v)) for i, v in enumerate(vals)]
    d.line(pts, fill=(71, 85, 105), width=2)
    for (x, y), v in zip(pts, vals):
        if v > 42.025:
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(220, 38, 38))
    xc = x0 + cp / n * (x1 - x0)
    d.line([(xc, y0), (xc, y1)], fill=(17, 24, 39), width=4)
    d.text((xc - 12, y0 + 8), "shift 14:30 · after tool change", font=font(26, True), fill=(17, 24, 39), anchor="ra")
    d.text((xc - 12, y1 - 78), "contain 11 suspect lots (customer named 2) →", font=font(26, True), fill=(185, 28, 28), anchor="ra")

    # defect photo
    photo = Image.open(ROOT / "sample_case" / "defect_photo.jpg").convert("RGB")
    photo.thumbnail((640, 480))
    px, py = 1240, 140
    d.rounded_rectangle([px - 8, py - 8, px + photo.width + 8, py + photo.height + 8], radius=18, fill=(248, 250, 252))
    img.paste(photo, (px, py))
    d.text((px, py + photo.height + 26), "Defect photo → AI vision on AMD", font=font(30), fill=(229, 231, 235))
    d.text((1240, 760), "AMD Developer Hackathon · ACT III", font=font(34, True), fill=(94, 234, 212))
    d.text((1240, 812), "Track 1 · Intelligent Industry", font=font(30), fill=(209, 213, 219))
    d.text((1240, 990), "MIT licensed · sample data is fictional", font=font(24), fill=(156, 163, 175))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
