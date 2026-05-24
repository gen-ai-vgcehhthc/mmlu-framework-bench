from __future__ import annotations

from bench.model import OpencodeModel


class BaseRunner:
    name = "base"

    def __init__(self, model: OpencodeModel):
        self.model = model

    def answer(self, prompt: str) -> str:
        result = self.model.complete(prompt)
        if result.error:
            raise RuntimeError(result.error + "\n" + result.text)
        return result.text
