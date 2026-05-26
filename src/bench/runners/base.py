from __future__ import annotations

from typing import Any

from bench.model import ModelClient


class BaseRunner:
    name = "base"

    def __init__(self, model: ModelClient):
        self.model = model
        self.last_trace: list[dict[str, object]] = []
        self.last_usage: dict[str, Any] | None = None

    def answer(self, prompt: str) -> str:
        result = self.model.complete(prompt)
        self.last_usage = merge_usage(self.last_usage, result.usage)
        if result.error:
            raise RuntimeError(result.error + "\n" + result.text)
        return result.text

    def trace_event(self, role: str, output: str, elapsed_s: float = 0.0, error: str | None = None) -> None:
        self.last_trace.append(
            {
                "role": role,
                "elapsed_s": elapsed_s,
                "error": error,
                "output": output,
            }
        )

    def traced_answer(self, role: str, prompt: str) -> str:
        model = model_for_role(self.model, role)
        result = model.complete(prompt)
        self.last_usage = merge_usage(self.last_usage, result.usage)
        self.last_trace.append(
            {
                "role": role,
                "model": model.model,
                "elapsed_s": result.elapsed_s,
                "error": result.error,
                "output": result.text,
                "usage": result.usage,
            }
        )
        if result.error:
            raise RuntimeError(result.error + "\n" + result.text)
        return result.text


def merge_usage(*items: dict[str, Any] | None) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}
    for item in items:
        if not item:
            continue
        for key, value in item.items():
            if isinstance(value, (int, float)):
                merged[key] = merged.get(key, 0) + value
            elif key not in merged:
                merged[key] = value
    return merged or None


def model_for_role(model: ModelClient, role: str) -> ModelClient:
    selector = getattr(model, "for_role", None)
    if callable(selector):
        return selector(role)
    return model
