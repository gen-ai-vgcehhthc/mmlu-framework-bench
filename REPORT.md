# MMLU-Pro Agent Framework Comparison Report

Date: 2026-05-24  
Model backend: `opencode/deepseek-v4-flash-free` through `opencode run --pure`  
Frameworks: LangGraph, CrewAI, Microsoft Agent Framework (MAF)  
Dataset: `TIGER-Lab/MMLU-Pro`, `test` split

## Executive Summary

For this experiment, the most important result is not accuracy. Because all frameworks share the same prompt and same model backend, accuracy should mostly match unless a framework integration changes output handling. The bigger differences are runtime overhead, dependency isolation, state/control ergonomics, and debugging surface.

Recommendation:

- Use **LangGraph** when you need explicit control flow, deterministic state transitions, and graph-shaped multi-agent topology.
- Use **CrewAI** when the problem is naturally role/task/team based and developer speed matters more than low-level orchestration control.
- Use **MAF** when production workflow concerns matter: checkpointing, HITL, OpenTelemetry, Microsoft ecosystem, and Azure/Foundry/Copilot alignment.
- Keep a **direct baseline** in every benchmark. It exposed framework overhead clearly and kept the model/provider noise honest.

## Experiment Design

The harness builds the same MMLU-Pro prompt for every run and asks the model to return only `A` through `J`. Runners differ only in orchestration wrapper:

- `direct`: calls opencode directly.
- `langgraph`: wraps the model call in a `StateGraph`.
- `crewai`: wraps the model call in a CrewAI Flow.
- `maf`: wraps the model call in a MAF functional workflow step.

Docker is used without a devcontainer. Each framework is installed into its own virtual environment because the current CrewAI and MAF releases conflict on OpenTelemetry dependency versions.

Primary run:

```powershell
docker run --rm `
  -v ${HOME}/.local/share/opencode/auth.json:/root/.local/share/opencode/auth.json:ro `
  -v ${PWD}/results:/app/results `
  mmlu-framework-bench `
  --framework direct --framework langgraph --framework crewai --framework maf `
  --limit 8 --shuffle --seed 42 --prewarm `
  --output results/mmlu-pro-shuffle8-seed42.jsonl `
  --summary results/mmlu-pro-shuffle8-seed42-summary.md
```

The shuffled sample covered: math 2, engineering 2, physics 1, health 1, history 1, economics 1.

## Quantitative Results

Primary shuffled sample, `N=8` per runner:

| Framework | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---:|---:|---:|---:|---:|---:|
| direct | 87.5% | 0 | 0 | 8.83s | 7.24s | 16.53s |
| LangGraph | 87.5% | 0 | 0 | 10.88s | 9.64s | 17.86s |
| CrewAI | 87.5% | 0 | 0 | 12.96s | 11.57s | 18.30s |
| MAF | 87.5% | 0 | 0 | 8.58s | 7.84s | 12.10s |

All frameworks missed the same physics question, so accuracy differences were not meaningful in this small shuffled run. Runtime overhead was more informative:

- MAF was closest to direct in this run, slightly faster on average due normal provider variance.
- LangGraph added modest overhead from worker/graph wrapping.
- CrewAI had the largest overhead, likely from Flow initialization and framework runtime setup.

Sequential first-10 run, not representative because it was all business questions:

| Framework | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---:|---:|---:|---:|---:|---:|
| direct | 90.0% | 0 | 0 | 6.84s | 5.61s | 12.33s |
| LangGraph | 70.0% | 0 | 2 | 9.50s | 7.31s | 20.75s |
| CrewAI | 70.0% | 0 | 2 | 12.04s | 10.59s | 18.69s |
| MAF | 80.0% | 0 | 0 | 8.80s | 6.31s | 19.88s |

Concurrency smoke run, `limit=6`, `concurrency=2`, all business:

| Framework | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---:|---:|---:|---:|---:|---:|
| direct | 83.3% | 0 | 0 | 7.86s | 6.60s | 12.90s |
| LangGraph | 83.3% | 0 | 0 | 11.40s | 7.41s | 21.31s |
| CrewAI | 66.7% | 0 | 0 | 12.34s | 12.06s | 13.83s |
| MAF | 66.7% | 0 | 1 | 12.62s | 6.79s | 28.19s |

## Metric-by-Metric Analysis

### Runtime & Efficiency

Direct remained the best latency baseline. Among frameworks, MAF and LangGraph were lighter than CrewAI for this single-call workflow. CrewAI's Flow abstraction is pleasant, but for a tiny benchmark node it carries visible startup overhead.

Cost control could not be measured directly because opencode CLI did not expose stable per-call token/cost metadata. The benchmark records latency, errors, parse failures, and raw output; cost hooks should be added when using a provider SDK with token usage.

Parallelism was limited by the free opencode backend and CLI subprocess model. LangGraph and MAF have clearer native parallel workflow stories than CrewAI for deterministic fan-out/fan-in, but this harness intentionally kept provider pressure low.

### Control & State Management

LangGraph gives the strongest low-level control: explicit nodes, edges, state schema, and checkpoint/store ecosystem. It is the best fit when correctness depends on knowing exactly what happens next.

CrewAI is optimized for role/task mental models. It is better for "team of agents" product workflows than for a deterministic benchmark harness.

MAF sits closer to production workflow infrastructure: `@workflow`, `@step`, checkpointing, and HITL concepts are central. Its functional workflow API is clean, but newer and more likely to shift.

### Developer Experience & Debugging

Observed setup friction:

- CrewAI and MAF could not be installed together in one Python environment because of incompatible OpenTelemetry requirements.
- CrewAI wrote framework output to stdout, so the worker had to redirect stdout while emitting JSON.
- MAF returned workflow events rather than only final text, so the runner had to extract the final `output` event.
- opencode first-run database migration logs can pollute raw model output; the harness now supports `--prewarm` and cleans migration lines.

This is a real-world differentiator: frameworks with richer observability often emit more runtime surface area, which helps debugging but complicates benchmarking and automation.

### External Interaction

Tool calling:

- LangGraph benefits from the LangChain tool ecosystem and explicit tool nodes.
- CrewAI has tools as a core agent/task concept.
- MAF has agent skills/tools and is aligned with Microsoft provider integrations.

Human approval:

- LangGraph supports interrupt/checkpoint style approval flows.
- CrewAI has human feedback features in Flows and task patterns.
- MAF exposes HITL through workflow context patterns.

### Ecosystem & Business Landing

LangGraph has the strongest graph-control ecosystem and LangSmith observability path. CrewAI has a fast-moving platform and a simple collaboration vocabulary. MAF has the clearest Microsoft enterprise path, including Azure/Foundry/GitHub Copilot alignment.

## Limitations

This is a small, free-provider experiment, not a publishable model benchmark. The full MMLU-Pro split has 12,032 test examples; running all frameworks across the full split would require much more quota and time. The report should be read as an integration and orchestration comparison, not a claim about the model's MMLU-Pro score.

The opencode CLI backend is practical and cheap, but it hides token usage and introduces CLI/database startup behavior. For a stronger cost study, add an OpenAI-compatible HTTP backend with usage metadata and fixed retry policy.

## Next Steps

1. Add a provider adapter that records token usage and price.
2. Add stratified sampling by category instead of pure shuffle.
3. Run `N=100` with `concurrency=1` and `concurrency=4` on a quota-safe model.
4. Add native tool-call and HITL test cases beyond MMLU-Pro.
5. Add observability screenshots/traces for each framework.

## References

- MMLU-Pro paper: https://arxiv.org/abs/2406.01574
- MMLU-Pro dataset: https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro
- LangGraph docs: https://docs.langchain.com/oss/python/langgraph
- CrewAI Flows docs: https://docs.crewai.com/en/concepts/flows
- Microsoft Agent Framework repo: https://github.com/microsoft/agent-framework
- MAF functional workflow docs: https://learn.microsoft.com/en-us/agent-framework/workflows/functional
