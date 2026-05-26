from __future__ import annotations

import asyncio

from bench.runners.base import BaseRunner
from bench.runners.debate import (
    adaptive_consensus_answer,
    critique_consensus_answer,
    critique_judge_prompt,
    critic_prompt,
    solver_prompt,
)


class MAFSelectiveCritiqueRunner(BaseRunner):
    name = "maf_selective_critique"

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
        async def critic_a(prompt: str, answer_a: str, answer_b: str) -> str:
            return await asyncio.to_thread(
                runner.traced_answer,
                "critic_a",
                critic_prompt(prompt, "Critic A", answer_a, answer_b),
            )

        @step
        async def critic_b(prompt: str, answer_a: str, answer_b: str) -> str:
            return await asyncio.to_thread(
                runner.traced_answer,
                "critic_b",
                critic_prompt(prompt, "Critic B", answer_b, answer_a),
            )

        @step
        async def judge(prompt: str, answer_a: str, answer_b: str, critique_a: str, critique_b: str) -> str:
            return await asyncio.to_thread(
                runner.traced_answer,
                "judge",
                critique_judge_prompt(prompt, answer_a, answer_b, critique_a, critique_b),
            )

        @workflow
        async def solve(prompt: str) -> str:
            answer_a, answer_b = await asyncio.gather(solver_a(prompt), solver_b(prompt))
            consensus = adaptive_consensus_answer(answer_a, answer_b)
            if consensus:
                runner.trace_event("consensus", consensus)
                return consensus

            critique_a, critique_b = await asyncio.gather(
                critic_a(prompt, answer_a, answer_b),
                critic_b(prompt, answer_a, answer_b),
            )
            critic_consensus = critique_consensus_answer(critique_a, critique_b)
            if critic_consensus:
                runner.trace_event("critic_consensus", critic_consensus)
                return critic_consensus

            return await judge(prompt, answer_a, answer_b, critique_a, critique_b)

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
