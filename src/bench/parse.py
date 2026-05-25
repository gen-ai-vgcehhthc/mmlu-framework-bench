from __future__ import annotations

import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
EXPLICIT_ANSWER_RE = re.compile(
    r"(?:final\s+answer|answer|option|choice|選項|答案)\s*(?:is|:|：|-)?\s*\(?\b([A-J])\b\)?",
    re.IGNORECASE,
)
LETTER_LINE_RE = re.compile(r"^\s*(?:\(?([A-J])\)?)[\s\).:：-]*$", re.IGNORECASE)
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

    lines = cleaned.splitlines()
    first_line = lines[0].strip() if lines else ""
    line_match = LETTER_LINE_RE.match(first_line)
    if line_match:
        return line_match.group(1).upper()

    explicit_matches = EXPLICIT_ANSWER_RE.findall(cleaned)
    if explicit_matches:
        return explicit_matches[-1].upper()

    for line in lines:
        line_match = LETTER_LINE_RE.match(line)
        if line_match:
            return line_match.group(1).upper()

    match = ANSWER_RE.search(cleaned)
    return match.group(1).upper() if match else None


def parse_answer_with_trace(text: str, trace: list[dict[str, object]] | None) -> tuple[str | None, str | None]:
    predicted = parse_answer(text)
    if predicted:
        return predicted, "raw"

    if not trace:
        return None, None

    by_role: dict[str, str] = {}
    for step in trace:
        role = str(step.get("role") or "")
        output = str(step.get("output") or "")
        answer = parse_answer(output)
        if answer:
            by_role[role] = answer

    judge = by_role.get("judge")
    if judge:
        return judge, "trace_judge"

    consensus = by_role.get("consensus")
    if consensus:
        return consensus, "trace_consensus"

    solver_answers = [by_role[role] for role in ("solver_a", "solver_b") if role in by_role]
    if len(solver_answers) == 2 and solver_answers[0] == solver_answers[1]:
        return solver_answers[0], "solver_consensus"
    if len(solver_answers) == 1:
        return solver_answers[0], "single_solver_fallback"

    return None, None
