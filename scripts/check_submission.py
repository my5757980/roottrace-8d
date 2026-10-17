"""Check the lablab submission field lengths in docs/submission/SUBMISSION.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOC = Path(__file__).resolve().parent.parent / "docs" / "submission" / "SUBMISSION.md"
LIMITS = {"Title": (5, 50), "Short description": (50, 255), "Long description": (600, 2000)}


def sections(text: str) -> dict[str, str]:
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def main() -> int:
    found = sections(DOC.read_text(encoding="utf-8"))
    ok = True
    for name, (lo, hi) in LIMITS.items():
        n = len(found.get(name, ""))
        good = lo <= n <= hi
        ok &= good
        print(f"{'OK ' if good else 'BAD'} {name:18s} {n:5d} chars (allowed {lo}-{hi})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
