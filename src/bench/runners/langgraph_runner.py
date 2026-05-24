from __future__ import annotations

from typing_extensions import TypedDict

from bench.runners.base import BaseRunner


class LangGraphRunner(BaseRunner):
    name = "langgraph"

    def __init__(self, model):
        super().__init__(model)
        from langgraph.graph import END, StateGraph

        class State(TypedDict):
            prompt: str
            answer: str

        def solve(state: State) -> dict[str, str]:
            return {"answer": super(LangGraphRunner, self).answer(state["prompt"])}

        graph = StateGraph(State)
        graph.add_node("solve", solve)
        graph.set_entry_point("solve")
        graph.add_edge("solve", END)
        self._app = graph.compile()

    def answer(self, prompt: str) -> str:
        result = self._app.invoke({"prompt": prompt, "answer": ""})
        return str(result["answer"])
