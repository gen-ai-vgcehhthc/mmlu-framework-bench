from __future__ import annotations

from bench.runners.base import BaseRunner
from bench.runners.debate import critique_judge_prompt, critic_prompt, solver_prompt


class CrewAICritiqueRunner(BaseRunner):
    name = "crewai_critique"

    def answer(self, prompt: str) -> str:
        from crewai.flow.flow import Flow, listen, start

        runner = self

        class MMLUCritiqueFlow(Flow):
            @start()
            def solve_a(self) -> str:
                return runner.traced_answer("solver_a", solver_prompt(self.state["prompt"], "Solver A"))

            @listen(solve_a)
            def solve_b(self, answer_a: str) -> str:
                self.state["answer_a"] = answer_a
                return runner.traced_answer("solver_b", solver_prompt(self.state["prompt"], "Solver B"))

            @listen(solve_b)
            def critique_a(self, answer_b: str) -> str:
                self.state["answer_b"] = answer_b
                return runner.traced_answer(
                    "critic_a",
                    critic_prompt(self.state["prompt"], "Critic A", self.state["answer_a"], answer_b),
                )

            @listen(critique_a)
            def critique_b(self, critique_a: str) -> str:
                self.state["critique_a"] = critique_a
                return runner.traced_answer(
                    "critic_b",
                    critic_prompt(self.state["prompt"], "Critic B", self.state["answer_b"], self.state["answer_a"]),
                )

            @listen(critique_b)
            def judge(self, critique_b: str) -> str:
                return runner.traced_answer(
                    "judge",
                    critique_judge_prompt(
                        self.state["prompt"],
                        self.state["answer_a"],
                        self.state["answer_b"],
                        self.state["critique_a"],
                        critique_b,
                    ),
                )

        self.last_trace = []
        flow = MMLUCritiqueFlow()
        return str(flow.kickoff(inputs={"prompt": prompt}))
