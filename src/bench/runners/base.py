from __future__ import annotations

from bench.model import OpencodeModel


class BaseRunner:
    name = "base"

    def __init__(self, model: OpencodeModel):
        self.model = model
        self.last_trace: list[dict[str, object]] = []

    def answer(self, prompt: str) -> str:
        result = self.model.complete(prompt)
        if result.error:
            raise RuntimeError(result.error + "\n" + result.text)
        return result.text

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
