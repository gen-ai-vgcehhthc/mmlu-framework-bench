from __future__ import annotations

from bench.model import ModelClient


class BaseRunner:
    name = "base"

    def __init__(self, model: ModelClient):
        self.model = model
        self.last_trace: list[dict[str, object]] = []

    def answer(self, prompt: str) -> str:
        result = self.model.complete(prompt)
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
        result = self.model.complete(prompt)
        self.last_trace.append(
            {
                "role": role,
                "elapsed_s": result.elapsed_s,
                "error": result.error,
                "output": result.text,
            }
        )
        if result.error:
            raise RuntimeError(result.error + "\n" + result.text)
        return result.text
