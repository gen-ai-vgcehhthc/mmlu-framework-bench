from __future__ import annotations

from bench.types import Question


LETTERS = "ABCDEFGHIJ"


def build_prompt(item: Question) -> str:
    option_lines = []
    for idx, option in enumerate(item.options):
        if idx >= len(LETTERS):
            break
        option_lines.append(f"{LETTERS[idx]}. {option}")

    return "\n".join(
        [
            "Answer this MMLU-Pro multiple-choice question.",
            "Think privately, then return only the single best option letter.",
            "Do not include explanation, punctuation, markdown, or extra text.",
            "",
            f"Question: {item.question}",
            "",
            "Options:",
            *option_lines,
            "",
            "Answer:",
        ]
    )
