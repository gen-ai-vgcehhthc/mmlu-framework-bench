from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Question:
    id: str
    question: str
    options: list[str]
    answer: str
    category: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class ModelResult:
    text: str
    elapsed_s: float
    error: str | None = None


@dataclass(frozen=True)
class RunResult:
    framework: str
    model: str
    question_id: str
    category: str | None
    expected: str
    predicted: str | None
    correct: bool
    elapsed_s: float
    raw_output: str
    error: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "model": self.model,
            "question_id": self.question_id,
            "category": self.category,
            "expected": self.expected,
            "predicted": self.predicted,
            "correct": self.correct,
            "elapsed_s": self.elapsed_s,
            "raw_output": self.raw_output,
            "error": self.error,
        }
