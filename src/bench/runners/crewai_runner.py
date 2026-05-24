from __future__ import annotations

from bench.runners.base import BaseRunner


class CrewAIRunner(BaseRunner):
    name = "crewai"

    def answer(self, prompt: str) -> str:
        from crewai.flow.flow import Flow, start

        runner = self

        class MMLUFlow(Flow):
            @start()
            def solve(self) -> str:
                return BaseRunner.answer(runner, self.state["prompt"])

        flow = MMLUFlow()
        return str(flow.kickoff(inputs={"prompt": prompt}))
