from __future__ import annotations

import asyncio

from bench.runners.base import BaseRunner


class MAFRunner(BaseRunner):
    name = "maf"

    def __init__(self, model):
        super().__init__(model)
        from agent_framework import step, workflow

        runner = self

        @step
        async def call_model(prompt: str) -> str:
            return await asyncio.to_thread(BaseRunner.answer, runner, prompt)

        @workflow
        async def solve(prompt: str) -> str:
            return await call_model(prompt)

        self._workflow = solve

    def answer(self, prompt: str) -> str:
        async def run() -> str:
            result = self._workflow.run(prompt)
            if hasattr(result, "__await__"):
                result = await result
            if isinstance(result, list):
                for event in reversed(result):
                    if getattr(event, "type", None) == "output":
                        return str(getattr(event, "data", ""))
            return str(result)

        return asyncio.run(run())
