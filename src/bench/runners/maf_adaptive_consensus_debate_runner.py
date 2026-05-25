from __future__ import annotations

import asyncio

from bench.runners.base import BaseRunner
from bench.runners.debate import adaptive_consensus_answer, judge_prompt, solver_prompt


class MAFAdaptiveConsensusDebateRunner(BaseRunner):
    name = "maf_adaptive_consensus_debate"

    def __init__(self, model):
        super().__init__(model)
        from agent_framework import step, workflow

        runner = self

        @step
        async def solver_a(prompt: str) -> str:
            return await asyncio.to_thread(runner.traced_answer, "solver_a", solver_prompt(prompt, "Solver A"))

        @step
        async def solver_b(prompt: str) -> str:
            return await asyncio.to_thread(runner.traced_answer, "solver_b", solver_prompt(prompt, "Solver B"))

        @step
        async def judge(prompt: str, answer_a: str, answer_b: str) -> str:
            return await asyncio.to_thread(runner.traced_answer, "judge", judge_prompt(prompt, answer_a, answer_b))

        @workflow
        async def solve(prompt: str) -> str:
            answer_a, answer_b = await asyncio.gather(solver_a(prompt), solver_b(prompt))
            consensus = adaptive_consensus_answer(answer_a, answer_b)
            if consensus:
                runner.trace_event("consensus", consensus)
                return consensus
            return await judge(prompt, answer_a, answer_b)

        self._workflow = solve

    def answer(self, prompt: str) -> str:
        self.last_trace = []

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
