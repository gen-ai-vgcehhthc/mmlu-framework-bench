from __future__ import annotations

from bench.runners.base import BaseRunner
from bench.runners.debate import judge_prompt, solver_prompt


class CrewAIDebateRunner(BaseRunner):
    name = "crewai_debate"

    def answer(self, prompt: str) -> str:
        from crewai.flow.flow import Flow, listen, start

        runner = self

        class MMLUDebateFlow(Flow):
            @start()
            def solve_a(self) -> str:
                return runner.traced_answer("solver_a", solver_prompt(self.state["prompt"], "Solver A"))

            @listen(solve_a)
            def solve_b(self, answer_a: str) -> str:
                self.state["answer_a"] = answer_a
                return runner.traced_answer("solver_b", solver_prompt(self.state["prompt"], "Solver B"))

            @listen(solve_b)
            def judge(self, answer_b: str) -> str:
                return runner.traced_answer("judge", judge_prompt(self.state["prompt"], self.state["answer_a"], answer_b))

        self.last_trace = []
        flow = MMLUDebateFlow()
        return str(flow.kickoff(inputs={"prompt": prompt}))
