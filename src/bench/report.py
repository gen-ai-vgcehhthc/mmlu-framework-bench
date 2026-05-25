from __future__ import annotations

import statistics
from collections import defaultdict

from bench.types import RunResult


def summarize(results: list[RunResult]) -> str:
    lines = [
        "# MMLU-Pro Framework Bench Summary",
        "",
        (
            "| Framework | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 | "
            "Prompt Tokens | Completion Tokens | Total Tokens |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    by_framework: dict[str, list[RunResult]] = defaultdict(list)
    for result in results:
        by_framework[result.framework].append(result)

    for framework in sorted(by_framework):
        group = by_framework[framework]
        n = len(group)
        correct = sum(1 for item in group if item.correct)
        errors = sum(1 for item in group if item.error)
        parse_failures = sum(1 for item in group if item.predicted is None and not item.error)
        latencies = [item.elapsed_s for item in group]
        avg = statistics.mean(latencies) if latencies else 0
        median = statistics.median(latencies) if latencies else 0
        p95 = percentile(latencies, 95)
        prompt_tokens = usage_total(group, "prompt_tokens")
        completion_tokens = usage_total(group, "completion_tokens")
        total_tokens = usage_total(group, "total_tokens")
        lines.append(
            f"| {framework} | {n} | {correct / n:.1%} | {errors} | {parse_failures} | "
            f"{avg:.2f}s | {median:.2f}s | {p95:.2f}s | "
            f"{format_usage(prompt_tokens)} | {format_usage(completion_tokens)} | {format_usage(total_tokens)} |"
        )

    lines.extend(["", *scorecard()])
    return "\n".join(lines) + "\n"


def usage_total(results: list[RunResult], key: str) -> int | None:
    values = [
        int(result.usage[key])
        for result in results
        if result.usage is not None and isinstance(result.usage.get(key), (int, float))
    ]
    if not values:
        return None
    return sum(values)


def format_usage(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,}"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def scorecard() -> list[str]:
    return [
        "## Framework Scorecard",
        "",
        "| Area | LangGraph | CrewAI | MAF |",
        "|---|---|---|---|",
        "| Runtime & efficiency | Fine-grained graph control; good for explicit parallel branches and retries. | Higher-level orchestration; convenient but heavier runtime surface. | Workflow-first model with async functional workflows and checkpointing. |",
        "| Cost control | Easy to centralize model calls and add budget gates per node. | Cost depends on crew/task design; hidden extra planner/manager calls can matter. | Step boundaries make expensive calls explicit; good place for budgets/retries. |",
        "| Parallel processing | Strong graph fan-out/fan-in patterns. | Flows and crews support structured work, but less transparent for micro-benchmarks. | Native async workflows make parallelism direct with `asyncio.gather`. |",
        "| Control flow & determinism | Best fit for deterministic state machines. | Best fit for role/task collaboration, less ideal when every edge must be explicit. | Strong workflow control; API is newer and still moving. |",
        "| State & memory | Checkpointers/stores are mature and explicit. | Built-in memory features are convenient, with more framework policy. | Checkpointing is a first-class production concern. |",
        "| Multi-agent topology | Supervisor/swarm/graph topologies are flexible. | Natural crew/team mental model. | Sequential, concurrent, handoff, and group workflow patterns. |",
        "| Developer experience | More code, more control. | Fastest conceptual start for role-based tasks. | Clean production story, but newest API among the three. |",
        "| Observability & debug | LangSmith ecosystem, node-level traces. | Observability integrations exist; abstractions can hide calls. | OpenTelemetry-oriented production debugging. |",
        "| Tool calling | Strong via LangChain/LangGraph tool ecosystem. | Tool API is central to agents/tasks. | Supports agent skills/tools, Microsoft ecosystem leaning. |",
        "| Human approval | Interrupts/checkpointing fit approval gates. | Human feedback features in flows/tasks. | HITL is part of workflow context patterns. |",
        "| Commercial support | LangChain/LangSmith/LangGraph platform. | CrewAI platform and enterprise offering. | Microsoft-backed, Azure/Foundry/GitHub Copilot alignment. |",
        "| Cloud deployment | LangGraph Platform or self-host. | CrewAI Enterprise/AMP or self-host. | Azure/Foundry and local/cloud workflow hosting patterns. |",
    ]
