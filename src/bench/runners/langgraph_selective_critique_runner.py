from __future__ import annotations

from typing_extensions import TypedDict

from bench.runners.base import BaseRunner
from bench.runners.debate import (
    adaptive_consensus_answer,
    critique_consensus_answer,
    critique_judge_prompt,
    critic_prompt,
    solver_prompt,
)


class LangGraphSelectiveCritiqueRunner(BaseRunner):
    name = "langgraph_selective_critique"

    def __init__(self, model):
        super().__init__(model)
        from langgraph.graph import END, START, StateGraph

        runner = self

        class State(TypedDict):
            prompt: str
            answer_a: str
            answer_b: str
            final: str

        def solver_a(state: State) -> dict[str, str]:
            return {"answer_a": runner.traced_answer("solver_a", solver_prompt(state["prompt"], "Solver A"))}

        def solver_b(state: State) -> dict[str, str]:
            return {"answer_b": runner.traced_answer("solver_b", solver_prompt(state["prompt"], "Solver B"))}

        def review(state: State) -> dict[str, str]:
            consensus = adaptive_consensus_answer(state["answer_a"], state["answer_b"])
            if consensus:
                runner.trace_event("consensus", consensus)
                return {"final": consensus}

            critique_a = runner.traced_answer(
                "critic_a",
                critic_prompt(state["prompt"], "Critic A", state["answer_a"], state["answer_b"]),
            )
            critique_b = runner.traced_answer(
                "critic_b",
                critic_prompt(state["prompt"], "Critic B", state["answer_b"], state["answer_a"]),
            )
            critic_consensus = critique_consensus_answer(critique_a, critique_b)
            if critic_consensus:
                runner.trace_event("critic_consensus", critic_consensus)
                return {"final": critic_consensus}

            return {
                "final": runner.traced_answer(
                    "judge",
                    critique_judge_prompt(
                        state["prompt"],
                        state["answer_a"],
                        state["answer_b"],
                        critique_a,
                        critique_b,
                    ),
                )
            }

        graph = StateGraph(State)
        graph.add_node("solver_a", solver_a)
        graph.add_node("solver_b", solver_b)
        graph.add_node("review", review)
        graph.add_edge(START, "solver_a")
        graph.add_edge(START, "solver_b")
        graph.add_edge(["solver_a", "solver_b"], "review")
        graph.add_edge("review", END)
        self._app = graph.compile()

    def answer(self, prompt: str) -> str:
        self.last_trace = []
        result = self._app.invoke({"prompt": prompt, "answer_a": "", "answer_b": "", "final": ""})
        return str(result["final"])
