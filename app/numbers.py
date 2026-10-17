"""Number-trace check: every number in AI narrative must come from evidence or input records."""

from __future__ import annotations

import re

# a number not glued to letters/digits/dots on the left and not followed by a letter or digit
NUM_RE = re.compile(r"(?<![A-Za-z0-9_.])(\d+(?:[.,]\d+)?)(?![A-Za-z0-9_]|[.,]\d)")
STANDARD_CONSTANTS = {1.33, 1.67, 100.0, 0.0}


def _parse(token: str) -> tuple[float, int]:
    token = token.replace(",", ".")
    decimals = len(token.split(".")[1]) if "." in token else 0
    return float(token), decimals


def numbers_in(text: str) -> list[str]:
    return [m.group(1) for m in NUM_RE.finditer(text or "")]


def allowed_values(evidence_texts: list[str]) -> list[float]:
    values: list[float] = []
    for text in evidence_texts:
        for tok in numbers_in(text):
            values.append(_parse(tok)[0])
    return values


def is_ignored(value: float, decimals: int) -> bool:
    if decimals == 0 and value <= 12:
        return True
    if decimals == 0 and 1990 <= value <= 2100:
        return True
    return value in STANDARD_CONSTANTS


def find_untraceable(text: str, evidence_texts: list[str], allowed: list[float] | None = None) -> list[str]:
    allowed = allowed if allowed is not None else allowed_values(evidence_texts)
    flagged: list[str] = []
    for tok in numbers_in(text):
        value, decimals = _parse(tok)
        if is_ignored(value, decimals):
            continue
        ok = any(abs(round(a, decimals) - value) < 1e-9 or abs(a - value) < 1e-9 for a in allowed)
        if not ok and tok not in flagged:
            flagged.append(tok)
    return flagged
