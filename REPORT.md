# MMLU-Pro Agent Framework Comparison Report

Date: 2026-05-26
Dataset: `TIGER-Lab/MMLU-Pro`, `test` split
Frameworks: LangGraph, CrewAI, Microsoft Agent Framework (MAF)
Backends: opencode `deepseek-v4-flash-free`; Groq `llama-3.1-8b-instant`; exploratory mixed runs with Groq `llama-3.3-70b-versatile` and opencode DeepSeek

## Executive Summary

This MMLU-Pro experiment should be read as a reasoning orchestration benchmark, not as a general model leaderboard. MMLU-Pro is useful here because it removes external-tool and long-horizon workflow variables: every framework receives the same closed-book multiple-choice questions and the same answer format. That makes it a clean test of whether framework-orchestrated multi-agent discussion improves reasoning enough to justify extra calls, latency, cost, and failure surface.

The main result is that framework choice did not materially change accuracy when the topology, prompt, and model were held constant. LangGraph, CrewAI, and MAF reached the same scores for the same Groq topologies. Their differences were mostly operational: latency, control-flow ergonomics, dependency isolation, observability, and ease of expressing stateful multi-agent patterns.

Adaptive consensus was the best same-model topology tested. On Groq `llama-3.1-8b-instant`, it improved direct accuracy from 35.5% to 37.5% at `N=200`, a net gain of 4 questions. Full critique was more expensive and weaker at 36.0%. Selective critique reduced critique cost dramatically but landed at 37.0%, slightly below adaptive consensus. The strongest result came from a mixed-model MAF selective run: Groq 8B as the primary model plus opencode DeepSeek as the secondary model reached 81.5% at `N=200`. That result should be interpreted as model heterogeneity plus topology, not as a pure framework effect.

Recommended reading:

- Use **LangGraph** when explicit deterministic graph control, checkpoints, and low-level state transitions matter most.
- Use **CrewAI** when the workflow naturally maps to roles, tasks, and teams, and developer speed matters more than orchestration transparency.
- Use **MAF** when production workflow concerns, HITL, OpenTelemetry, Azure/Foundry/Copilot alignment, and Microsoft ecosystem integration are central.
- Keep a **direct baseline** in every benchmark. It prevents framework overhead from being mistaken for model improvement.

## Benchmark Question

For the broader GAIA / tau-bench / MMLU-Pro benchmark report, MMLU-Pro answers this narrower question:

> Given the same model and same MMLU-Pro questions, do LangGraph, CrewAI, and MAF make it easier to implement multi-agent reasoning topologies that improve accuracy enough to justify their added runtime, cost, and debugging complexity?

This is reasonable for MAF because the hypothesis is not that MAF itself makes the model smarter. The hypothesis is that MAF can express useful multi-agent workflows, such as independent solvers, consensus gates, critique, and role-routed model diversity. MMLU-Pro is a good first test for that because it measures closed-book reasoning without confounding tool use.

## Experimental Setup

The harness builds the same MMLU-Pro prompt for every run and asks the model to return only `A` through `J`. Docker is used without a devcontainer. Each framework is installed into its own virtual environment because current CrewAI and MAF releases have incompatible OpenTelemetry dependency requirements.

Tested runners:

- `direct`: one raw model call, no agent framework.
- `langgraph`, `crewai`, `maf`: one model call wrapped in each framework.
- `*_adaptive_consensus_debate`: two independent solvers; if they agree, return consensus; otherwise call a judge.
- `*_critique`: two solvers, two cross-critiques, then a judge on every question.
- `*_selective_critique`: two solvers first; critique only runs when solvers disagree.
- mixed-model selective critique: primary model handles default roles while `solver_b` and `critic_b` are routed to a secondary model.

All multi-agent runners record trace logs with role outputs, per-call latency, errors, and, for mixed-model runs, the concrete model used by each role.

## Final Results

### DeepSeek Through Opencode, N=50

The first complete run used opencode `deepseek-v4-flash-free`, shuffled with `seed=42`, across 50 MMLU-Pro questions. Timeout and blank-output rows from the first long run were retried. The final file has 350 rows: 7 runners x 50 questions, with 0 errors and 0 parse failures.

| Framework | Pattern | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| direct | single call | 50 | 84.0% | 0 | 0 | 10.32s | 6.18s | 27.91s |
| LangGraph | single agent | 50 | 90.0% | 0 | 0 | 12.47s | 7.79s | 38.56s |
| CrewAI | single agent | 50 | 80.0% | 0 | 0 | 15.94s | 12.27s | 31.07s |
| MAF | single agent | 50 | 88.0% | 0 | 0 | 15.13s | 7.36s | 51.65s |
| LangGraph | debate | 50 | 84.0% | 0 | 0 | 26.05s | 17.19s | 68.31s |
| CrewAI | debate | 50 | 80.0% | 0 | 0 | 46.96s | 37.59s | 99.43s |
| MAF | debate | 50 | 84.0% | 0 | 0 | 22.99s | 15.22s | 77.25s |

This run does not support a claim that naive same-model debate improves MMLU-Pro reasoning. Debate increased latency and did not beat the strongest single-agent runs. Trace-aware parsing mattered because blank judge outputs sometimes hid usable solver outputs, but remaining blank rows were retried rather than inferred.

### Groq 8B, N=200

The main larger run used Groq `llama-3.1-8b-instant`, shuffled with `seed=42`, with provider token usage recorded. The final JSONL has 2,000 rows: 10 runners x 200 questions, with 0 errors and 0 parse failures.

| Framework | Pattern | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 | Total Tokens |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | single call | 200 | 35.5% | 0 | 0 | 0.45s | 0.24s | 1.42s | 51,941 |
| LangGraph | single agent | 200 | 35.5% | 0 | 0 | 1.97s | 1.94s | 2.37s | 51,941 |
| CrewAI | single agent | 200 | 35.5% | 0 | 0 | 7.05s | 6.92s | 7.95s | 51,941 |
| MAF | single agent | 200 | 35.5% | 0 | 0 | 1.37s | 1.19s | 3.29s | 51,941 |
| LangGraph | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 2.25s | 1.84s | 3.99s | 125,571 |
| CrewAI | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 7.14s | 7.08s | 7.88s | 125,533 |
| MAF | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 1.62s | 1.22s | 3.43s | 125,533 |
| LangGraph | critique | 200 | 36.0% | 0 | 0 | 4.62s | 3.07s | 12.09s | 388,678 |
| CrewAI | critique | 200 | 36.0% | 0 | 0 | 7.64s | 7.56s | 8.36s | 388,663 |
| MAF | critique | 200 | 36.0% | 0 | 0 | 3.00s | 2.72s | 5.93s | 388,688 |

Accuracy did not scale with cost. Adaptive consensus produced the best same-model result at 37.5%, a net +4 correct answers over direct. Full critique reached only 36.0%, a net +1 over direct, while using roughly 7.5x the direct token count. Direct-to-critique transitions were nearly balanced: critique fixed 17 direct-wrong answers but broke 16 direct-correct answers.

The reason full critique underperformed is that same-model critique often changed answers without adding a reliable correctness signal. The judge received more text, but not necessarily more independent evidence. When all agents share the same model family, prompt, and blind spots, critique can amplify plausible but wrong rationales. Adaptive consensus worked better because it only spent an extra judge call on disagreement cases and avoided perturbing the many cases where both solvers already matched.

### Selective Critique, N=200

Selective critique was added to address full critique's failure mode. It keeps adaptive consensus as the first gate, then runs cross-critique only when the two solvers disagree. This run used Groq `llama-3.1-8b-instant`, `N=200`, and all three frameworks. The final file has 600 rows with 0 errors and 0 parse failures.

| Framework | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 | Total Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LangGraph selective critique | 200 | 37.0% | 0 | 0 | 2.38s | 1.80s | 4.76s | 136,112 |
| CrewAI selective critique | 200 | 37.0% | 0 | 0 | 7.07s | 6.92s | 8.03s | 135,001 |
| MAF selective critique | 200 | 37.0% | 0 | 0 | 1.73s | 1.16s | 4.48s | 135,001 |

Selective critique was cheaper than full critique, about 135K tokens per framework instead of 388K, but it did not beat adaptive consensus. It reached 37.0%, or +3 correct answers over direct, while adaptive consensus reached +4. The topology behaved as designed: roughly 190/200 examples short-circuited through solver consensus, and only 10/200 reached critique.

### Mixed-Model Exploratory Runs

The harness now supports role-routed mixed-model runs through `--secondary-backend`, `--secondary-model`, and `--secondary-roles`. The first tests kept Groq `llama-3.1-8b-instant` as the primary model and routed `solver_b` and `critic_b` to a secondary model.

| Mixed Run | Framework | N | Accuracy | Errors | Parse Failures | Avg Latency | Tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| Groq 8B primary + Groq 70B secondary | MAF selective critique | 20 | 60.0% | 0 | 0 | 2.07s | 32,762 |
| Groq 8B primary + opencode DeepSeek secondary | MAF selective critique | 10 | 70.0% | 0 | 0 | 15.75s | 10,249 Groq-reported tokens |
| Groq 70B primary + Groq 70B secondary | MAF selective critique | 200 | 53.5% | 0 | 0 | 1.18s | 139,805 |
| Groq 70B primary + Groq 8B secondary | MAF selective critique | 200 | 56.0% | 0 | 0 | 2.01s | 271,837 |
| Groq 8B primary + Groq 70B secondary | MAF selective critique | 200 | 49.5% | 0 | 0 | 18.94s | 273,497 |
| Groq 8B primary + opencode DeepSeek secondary | MAF selective critique | 100 | 80.0% | 0 | 0 | 27.65s | 93,311 Groq-reported tokens |
| Groq 8B primary + opencode DeepSeek secondary | MAF selective critique | 200 | 81.5% | 0 | 0 | 25.83s | 187,217 Groq-reported tokens |

The Groq-only mixed runs separate model strength from model diversity. `70B+70B` reached 53.5%, showing that a stronger same-model pair improves over the 8B same-model run but still does not create much new deliberation signal: the two 70B solvers agreed on 186/200 questions. `70B+8B` reached 56.0%, while the reverse `8B+70B` reached only 49.5%. This suggests routing matters: putting the stronger model in the primary/judge role was better than using it only as the secondary dissenter. The reverse run also had severe latency long tails, likely from Groq 70B rate-limit backoff, with p95 at 124.37s.

The mixed opencode result is still the clearest positive signal in this study, but it changes the interpretation. On the same 200-question sample, Groq direct and MAF single-agent scored 35.5%, MAF adaptive consensus scored 37.5%, MAF same-model critique scored 36.0%, Groq `70B+70B` selective critique scored 53.5%, and MAF mixed Groq+opencode selective critique scored 81.5%. Trace analysis shows why: Groq 8B `solver_a` was correct on 75/200 questions, while opencode DeepSeek `solver_b` was correct on 158/179 parseable solver outputs. In direct solver comparisons, `solver_b` was right while `solver_a` was wrong on 96 questions; the reverse happened only 5 times.

This means the gain is mainly driven by a much stronger or more suitable secondary model, with the framework topology acting as the routing and arbitration layer. It is still relevant to the MAF multi-agent hypothesis because heterogeneous agents gave useful disagreement signal, but it is not evidence that framework debate alone improves reasoning. One caveat: 1/200 opencode traces contained an Exa Web Search marker. Excluding that row gives 162/199 = 81.4%, so the aggregate result is effectively unchanged, but the run should be labeled as opencode-backed rather than strictly closed-book.

## Metric-by-Metric Analysis

### Runtime & Efficiency

Direct calls are the latency and cost baseline. Single-agent framework wrappers did not change token usage because they send the same prompt to the same model, but they did add orchestration overhead. In the Groq N=200 run, CrewAI had the largest runtime overhead, LangGraph was moderate, and MAF was generally the lightest framework wrapper.

For multi-agent topologies, token cost was driven by model-call count. Direct used about 52K tokens per 200-question run. Adaptive consensus used about 125.5K tokens because it called the judge only 11 times. Full critique used about 388.7K tokens because it always ran two solvers, two critics, and a judge.

### Parallel Processing

Framework capability and provider limits should be separated. LangGraph and MAF both express deterministic fan-out/fan-in cleanly, and MAF's async workflow style made concurrent solver calls straightforward. CrewAI can express collaborative flows, but its higher-level runtime is heavier for a micro-benchmark. In practice, Groq TPM limits and opencode CLI behavior constrained concurrency more than the frameworks did.

### Control Flow & Determinism

LangGraph provides the clearest graph-level control with explicit nodes, edges, and state. MAF provides a clean workflow-step model with production-oriented checkpoint and HITL concepts. CrewAI is less ideal when every edge and state transition must be audited, but it is ergonomic when the problem naturally maps to role/task collaboration.

The benchmark confirms that deterministic topology design matters more than the framework label. When all three frameworks implemented the same adaptive or selective topology, they produced the same accuracy.

### State & Memory

MMLU-Pro does not stress long-term memory. It does, however, stress short-lived state: solver answers, parsed labels, critique text, judge decisions, and fallback traces. LangGraph makes this state most explicit. MAF's workflow model is also a good fit. CrewAI is convenient, but more framework behavior is hidden behind the flow abstraction.

### Observability & Debugging

Trace logging was essential. It exposed blank judge outputs, parse failures, solver consensus, critique behavior, and mixed-model role routing. The harness now records trace arrays for multi-agent runs and token usage for OpenAI-compatible HTTP responses.

Setup friction was also informative:

- CrewAI and MAF required separate virtual environments because of OpenTelemetry dependency conflicts.
- CrewAI wrote framework output to stdout, so the worker had to redirect stdout while emitting JSON.
- MAF returned workflow events rather than only final text, so the runner had to extract final output events.
- opencode first-run migration logs and occasional empty outputs required prewarm, cleaning, retries, and explicit timeout handling.

### Tool Calling and Human Approval

MMLU-Pro does not exercise tool use or human approval, so this benchmark should not be used to rank those features directly. Based on framework design:

- LangGraph has strong tool-node, interrupt, checkpoint, and LangSmith observability patterns.
- CrewAI has a natural agent/task/tool vocabulary and human-feedback workflow features.
- MAF has agent skills/tools, HITL workflow context, OpenTelemetry, and Microsoft ecosystem alignment.

These capabilities should be evaluated in GAIA and tau-bench rather than inferred from MMLU-Pro.

### Ecosystem & Commercial Landing

LangGraph has the strongest graph-control ecosystem and LangSmith path. CrewAI has the simplest collaboration vocabulary and a fast-moving platform. MAF has the clearest Microsoft enterprise path, especially for Azure, Foundry, GitHub Copilot, workflow checkpointing, and OpenTelemetry-centered production monitoring.

## Timeout and Rate-Limit Notes

The timeout issues came from backend and orchestration interaction, not from MMLU-Pro itself. opencode can return empty output or take longer through the CLI, especially around first-run setup and provider latency. Groq introduced rate limits through TPM/HTTP 429 pressure when concurrent runners made many fast requests. The final runs used retries, key rotation, provider backoff parsing, row-level resume, and lower concurrency where needed.

The latest opencode health retry completed with 0 errors and 0 parse failures. It is usable, but for long runs the safer configuration is `--parse-retries 2`, `--timeout 180`, and conservative concurrency.

## Limitations

This is not a publishable model benchmark. The full MMLU-Pro test split has 12,032 examples, while the main framework comparison used shuffled samples of 50 and 200. Free or low-cost providers introduce non-determinism, quota pressure, and retry artifacts.

Accuracy should be interpreted carefully. With the same model and topology, the frameworks should usually produce the same answers; any accuracy difference can come from provider variance, parse handling, or orchestration side effects. The stronger conclusion is about framework control, cost, latency, traceability, and how cleanly each framework expresses multi-agent reasoning patterns.

## Recommendations

1. For the combined GAIA / tau-bench / MMLU-Pro report, frame MMLU-Pro as the closed-book reasoning and orchestration slice.
2. Use adaptive consensus as the same-model baseline. It was the best cost/accuracy tradeoff tested.
3. Treat full critique as currently unjustified for weak same-model runs because it adds cost and can break correct answers.
4. Validate the mixed-model result with a strict no-web/no-tool secondary backend or a fully token-accounted HTTP secondary model before making a closed-book accuracy claim.
5. Use GAIA and tau-bench to evaluate tool calling, long-horizon state, human approval, and workflow realism.
6. Keep direct runs in every experiment and always report token usage, parse failures, timeout/error counts, and trace availability.

## References

- MMLU-Pro paper: https://arxiv.org/abs/2406.01574
- MMLU-Pro dataset: https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro
- LangGraph docs: https://docs.langchain.com/oss/python/langgraph
- CrewAI Flows docs: https://docs.crewai.com/en/concepts/flows
- Microsoft Agent Framework repo: https://github.com/microsoft/agent-framework
- MAF functional workflow docs: https://learn.microsoft.com/en-us/agent-framework/workflows/functional
