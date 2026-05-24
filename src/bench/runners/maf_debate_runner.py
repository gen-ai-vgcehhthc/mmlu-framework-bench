from __future__ import annotations

import asyncio

from bench.runners.base import BaseRunner
from bench.runners.debate import judge_prompt, solver_prompt


class MAFDebateRunner(BaseRunner):
    name = "maf_debate"

    def __init__(self, model):
        super().__init__(model)
        from agent_framework import step, workflow

        runner = self

        @step
        async def solver_a(prompt: str) -> str:
            return await asyncio.to_thread(BaseRunner.answer, runner, solver_prompt(prompt, "Solver A"))

        @step
        async def solver_b(prompt: str) -> str:
            return await asyncio.to_thread(BaseRunner.answer, runner, solver_prompt(prompt, "Solver B"))

        @step
        async def judge(prompt: str, answer_a: str, answer_b: str) -> str:
            return await asyncio.to_thread(BaseRunner.answer, runner, judge_prompt(prompt, answer_a, answer_b))

        @workflow
        async def solve(prompt: str) -> str:
            answer_a, answer_b = await asyncio.gather(solver_a(prompt), solver_b(prompt))
            return await judge(prompt, answer_a, answer_b)

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
