from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from datasets import load_dataset

from bench.prompt import LETTERS
from bench.types import Question


def load_questions(
    dataset: str,
    split: str,
    limit: int | None = None,
    category: str | None = None,
    shuffle: bool = False,
    seed: int = 42,
) -> list[Question]:
    rows = load_dataset(dataset, split=split)
    if shuffle:
        rows = rows.shuffle(seed=seed)
    questions: list[Question] = []

    for idx, row in enumerate(rows):
        item = normalize_row(idx, dict(row))
        if category and (item.category or "").lower() != category.lower():
            continue
        questions.append(item)
        if limit is not None and len(questions) >= limit:
            break

    return questions


def normalize_row(idx: int, row: dict[str, Any]) -> Question:
    options = coerce_options(row)
    answer = coerce_answer(row, options)
    question_id = str(row.get("question_id") or row.get("id") or idx)
    category = row.get("category") or row.get("subject")
    return Question(
        id=question_id,
        question=str(row["question"]),
        options=options,
        answer=answer,
        category=str(category) if category is not None else None,
        raw=row,
    )


def coerce_options(row: dict[str, Any]) -> list[str]:
    raw_options = row.get("options") or row.get("choices")
    if isinstance(raw_options, str):
        raise ValueError("Dataset returned options as a string; expected a list")
    if isinstance(raw_options, Iterable):
        return [str(option) for option in raw_options]

    options: list[str] = []
    for letter in LETTERS:
        if letter in row:
            options.append(str(row[letter]))
    if not options:
        raise ValueError(f"Cannot find options in row keys: {sorted(row.keys())}")
    return options


def coerce_answer(row: dict[str, Any], options: list[str]) -> str:
    answer = row.get("answer")
    if isinstance(answer, str) and len(answer.strip()) == 1:
        letter = answer.strip().upper()
        if letter in LETTERS:
            return letter

    answer_index = row.get("answer_index")
    if answer_index is not None:
        return LETTERS[int(answer_index)]

    if isinstance(answer, str) and answer in options:
        return LETTERS[options.index(answer)]

    raise ValueError(f"Cannot coerce answer from row keys: {sorted(row.keys())}")
