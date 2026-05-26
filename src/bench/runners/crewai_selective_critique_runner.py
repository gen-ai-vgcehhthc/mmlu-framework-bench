from __future__ import annotations

from bench.runners.base import BaseRunner
from bench.runners.debate import (
    adaptive_consensus_answer,
    critique_consensus_answer,
    critique_judge_prompt,
    critic_prompt,
    solver_prompt,
)


class CrewAISelectiveCritiqueRunner(BaseRunner):
    name = "crewai_selective_critique"

    def answer(self, prompt: str) -> str:
        from crewai.flow.flow import Flow, listen, start

        runner = self

        class MMLUSelectiveCritiqueFlow(Flow):
            @start()
            def solve_a(self) -> str:
                return runner.traced_answer("solver_a", solver_prompt(self.state["prompt"], "Solver A"))

            @listen(solve_a)
            def solve_b(self, answer_a: str) -> str:
                self.state["answer_a"] = answer_a
                return runner.traced_answer("solver_b", solver_prompt(self.state["prompt"], "Solver B"))

            @listen(solve_b)
            def review(self, answer_b: str) -> str:
                self.state["answer_b"] = answer_b
                consensus = adaptive_consensus_answer(self.state["answer_a"], answer_b)
                if consensus:
                    runner.trace_event("consensus", consensus)
                    return consensus

                critique_a = runner.traced_answer(
                    "critic_a",
                    critic_prompt(self.state["prompt"], "Critic A", self.state["answer_a"], answer_b),
                )
                critique_b = runner.traced_answer(
                    "critic_b",
                    critic_prompt(self.state["prompt"], "Critic B", answer_b, self.state["answer_a"]),
                )
                critic_consensus = critique_consensus_answer(critique_a, critique_b)
                if critic_consensus:
                    runner.trace_event("critic_consensus", critic_consensus)
                    return critic_consensus

                return runner.traced_answer(
                    "judge",
                    critique_judge_prompt(
                        self.state["prompt"],
                        self.state["answer_a"],
                        answer_b,
                        critique_a,
                        critique_b,
                    ),
                )

        self.last_trace = []
        flow = MMLUSelectiveCritiqueFlow()
        return str(flow.kickoff(inputs={"prompt": prompt}))
