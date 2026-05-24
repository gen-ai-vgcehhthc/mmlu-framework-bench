from __future__ import annotations


def solver_prompt(prompt: str, role: str) -> str:
    return "\n".join(
        [
            f"You are {role}, an independent MMLU-Pro reasoning agent.",
            "Analyze the question carefully and choose the best answer.",
            "You may include a short rationale, but the first line must be exactly: Answer: <letter>",
            "",
            prompt,
        ]
    )


def judge_prompt(prompt: str, answer_a: str, answer_b: str) -> str:
    return "\n".join(
        [
            "You are the final judge in a multi-agent MMLU-Pro discussion.",
            "Given the original question and two independent solver outputs, choose the single best answer.",
            "Return only one option letter from A to J. No explanation.",
            "",
            "Original prompt:",
            prompt,
            "",
            "Solver A output:",
            answer_a,
            "",
            "Solver B output:",
            answer_b,
            "",
            "Final answer:",
        ]
    )
