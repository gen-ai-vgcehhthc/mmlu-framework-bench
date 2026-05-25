from __future__ import annotations

from typing_extensions import TypedDict

from bench.runners.base import BaseRunner
from bench.runners.debate import adaptive_consensus_answer, judge_prompt, solver_prompt


class LangGraphAdaptiveConsensusDebateRunner(BaseRunner):
    name = "langgraph_adaptive_consensus_debate"

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

        def judge(state: State) -> dict[str, str]:
            consensus = adaptive_consensus_answer(state["answer_a"], state["answer_b"])
            if consensus:
                runner.trace_event("consensus", consensus)
                return {"final": consensus}
            return {"final": runner.traced_answer("judge", judge_prompt(state["prompt"], state["answer_a"], state["answer_b"]))}

        graph = StateGraph(State)
        graph.add_node("solver_a", solver_a)
        graph.add_node("solver_b", solver_b)
        graph.add_node("judge", judge)
        graph.add_edge(START, "solver_a")
        graph.add_edge(START, "solver_b")
        graph.add_edge(["solver_a", "solver_b"], "judge")
        graph.add_edge("judge", END)
        self._app = graph.compile()

    def answer(self, prompt: str) -> str:
        self.last_trace = []
        result = self._app.invoke({"prompt": prompt, "answer_a": "", "answer_b": "", "final": ""})
        return str(result["final"])
