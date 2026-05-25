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


def critic_prompt(prompt: str, critic_role: str, own_answer: str, other_answer: str) -> str:
    return "\n".join(
        [
            f"You are {critic_role}, a skeptical MMLU-Pro critique agent.",
            "Review the other solver's answer against the original question.",
            "Do not change your own answer unless the other solver exposes a concrete flaw.",
            "Keep the critique concise: at most two bullet points.",
            "End with exactly one line: Revised answer: <letter>",
            "",
            "Original prompt:",
            prompt,
            "",
            "Your original solver output:",
            own_answer,
            "",
            "Other solver output to critique:",
            other_answer,
        ]
    )


def critique_judge_prompt(
    prompt: str,
    answer_a: str,
    answer_b: str,
    critique_a: str,
    critique_b: str,
) -> str:
    return "\n".join(
        [
            "You are the final judge in a multi-agent MMLU-Pro critique discussion.",
            "Use the original question, both solver answers, and both critiques.",
            "Prefer critiques that identify a concrete factual or logical flaw.",
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
            "Critique A output:",
            critique_a,
            "",
            "Critique B output:",
            critique_b,
            "",
            "Final answer:",
        ]
    )
