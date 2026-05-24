from __future__ import annotations

import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
ANSWER_RE = re.compile(r"\b([A-J])\b", re.IGNORECASE)


def clean_output(text: str) -> str:
    cleaned = ANSI_RE.sub("", text)
    kept: list[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("Performing one time database migration"):
            continue
        if stripped.startswith("sqlite-migration:"):
            continue
        if stripped == "Database migration complete.":
            continue
        kept.append(stripped)
    return "\n".join(kept).strip()


def parse_answer(text: str) -> str | None:
    cleaned = clean_output(text)
    if len(cleaned) == 1 and cleaned.upper() in "ABCDEFGHIJ":
        return cleaned.upper()

    first_line = cleaned.splitlines()[0].strip() if cleaned else ""
    if len(first_line) == 1 and first_line.upper() in "ABCDEFGHIJ":
        return first_line.upper()

    match = ANSWER_RE.search(cleaned)
    return match.group(1).upper() if match else None
