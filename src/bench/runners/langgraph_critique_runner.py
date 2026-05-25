from __future__ import annotations

from typing_extensions import TypedDict

from bench.runners.base import BaseRunner
from bench.runners.debate import critique_judge_prompt, critic_prompt, solver_prompt


class LangGraphCritiqueRunner(BaseRunner):
    name = "langgraph_critique"

    def __init__(self, model):
        super().__init__(model)
        from langgraph.graph import END, START, StateGraph

        runner = self

        class State(TypedDict):
            prompt: str
            answer_a: str
            answer_b: str
            critique_a: str
            critique_b: str
            final: str

        def solver_a(state: State) -> dict[str, str]:
            return {"answer_a": runner.traced_answer("solver_a", solver_prompt(state["prompt"], "Solver A"))}

        def solver_b(state: State) -> dict[str, str]:
            return {"answer_b": runner.traced_answer("solver_b", solver_prompt(state["prompt"], "Solver B"))}

        def critic_a(state: State) -> dict[str, str]:
            return {
                "critique_a": runner.traced_answer(
                    "critic_a",
                    critic_prompt(state["prompt"], "Critic A", state["answer_a"], state["answer_b"]),
                )
            }

        def critic_b(state: State) -> dict[str, str]:
            return {
                "critique_b": runner.traced_answer(
                    "critic_b",
                    critic_prompt(state["prompt"], "Critic B", state["answer_b"], state["answer_a"]),
                )
            }

        def judge(state: State) -> dict[str, str]:
            return {
                "final": runner.traced_answer(
                    "judge",
                    critique_judge_prompt(
                        state["prompt"],
                        state["answer_a"],
                        state["answer_b"],
                        state["critique_a"],
                        state["critique_b"],
                    ),
                )
            }

        graph = StateGraph(State)
        graph.add_node("solver_a", solver_a)
        graph.add_node("solver_b", solver_b)
        graph.add_node("critic_a", critic_a)
        graph.add_node("critic_b", critic_b)
        graph.add_node("judge", judge)
        graph.add_edge(START, "solver_a")
        graph.add_edge(START, "solver_b")
        graph.add_edge(["solver_a", "solver_b"], "critic_a")
        graph.add_edge(["solver_a", "solver_b"], "critic_b")
        graph.add_edge(["critic_a", "critic_b"], "judge")
        graph.add_edge("judge", END)
        self._app = graph.compile()

    def answer(self, prompt: str) -> str:
        self.last_trace = []
        result = self._app.invoke(
            {
                "prompt": prompt,
                "answer_a": "",
                "answer_b": "",
                "critique_a": "",
                "critique_b": "",
                "final": "",
            }
        )
        return str(result["final"])
