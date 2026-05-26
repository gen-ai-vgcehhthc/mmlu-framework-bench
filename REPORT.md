# MMLU-Pro Agent Framework Comparison Report

Date: 2026-05-25  
Model backends: `opencode/deepseek-v4-flash-free` through `opencode run --pure`; Groq `llama-3.1-8b-instant` through OpenAI-compatible HTTP  
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

- `direct`: calls the configured model backend directly.
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

### N=50 Reasoning Orchestration Matrix

After the initial smoke runs, the main MMLU-Pro experiment was rerun with `N=50`, shuffled with `seed=42`, covering 14 categories: economics, engineering, business, physics, other, law, health, math, history, psychology, philosophy, computer science, biology, and chemistry.

This completed run compares single-agent and the original two-solver-plus-judge debate pattern:

```powershell
docker run --rm `
  -v ${HOME}/.local/share/opencode/auth.json:/root/.local/share/opencode/auth.json:ro `
  -v ${PWD}/results:/app/results `
  mmlu-framework-bench `
  --framework direct `
  --framework langgraph --framework crewai --framework maf `
  --framework langgraph_debate --framework crewai_debate --framework maf_debate `
  --limit 50 --shuffle --seed 42 --resume `
  --output results/mmlu-pro-debate50-seed42.jsonl `
  --summary results/mmlu-pro-debate50-seed42-summary.md
```

| Framework | Pattern | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| direct | single call | 50 | 84.0% | 0 | 0 | 10.32s | 6.18s | 27.91s |
| LangGraph | single agent | 50 | 90.0% | 0 | 0 | 12.47s | 7.79s | 38.56s |
| CrewAI | single agent | 50 | 80.0% | 0 | 0 | 15.94s | 12.27s | 31.07s |
| MAF | single agent | 50 | 88.0% | 0 | 0 | 15.13s | 7.36s | 51.65s |
| LangGraph | debate | 50 | 84.0% | 0 | 0 | 26.05s | 17.19s | 68.31s |
| CrewAI | debate | 50 | 80.0% | 0 | 0 | 46.96s | 37.59s | 99.43s |
| MAF | debate | 50 | 84.0% | 0 | 0 | 22.99s | 15.22s | 77.25s |

The timeout and blank-output rows from the first long run were removed and rerun. The final result file now has 350 rows: 7 runners x 50 questions, with 0 errors and 0 parse failures. All 150 debate rows include a `trace` array with solver A, solver B, and judge outputs, per-call latency, and per-call errors.

After inspecting the trace logs, the result file was re-scored with trace-aware parsing. The final scoring used raw model output for 316 rows, solver consensus fallback for 24 rows, and single-solver fallback for 10 rows. Remaining blank rows were retried rather than inferred.

### Main Reading

In this MMLU-Pro setup, the single-agent frameworks did not show consistent reasoning gains over direct calls. LangGraph single-agent scored highest at 90%, followed by MAF at 88%, direct at 84%, and CrewAI at 80%. Given `N=50` and non-deterministic free-provider calls, the main signal is not that one framework "reasons better"; it is that orchestration adds measurable latency and output-control surfaces.

The debate topology did not produce a clear, framework-wide reasoning gain. LangGraph debate fell from 90% single-agent to 84%, CrewAI debate matched CrewAI single-agent at 80%, and MAF debate fell from 88% single-agent to 84%. The result does not support a claim that naive same-model debate reliably improves MMLU-Pro reasoning.

The trace logs show why parse-aware evaluation matters: each debate example uses three model calls instead of one, so blank judge outputs can hide useful solver outputs. The corrected result should still be reported with the caveat that `solver_consensus` and `single_solver_fallback` are post-processing fallbacks, not native judge success. A critique topology has been added for follow-up runs to test whether explicit cross-examination is more useful than naive debate.

After this run, the benchmark code was updated to replace the original `_debate` runners with `_adaptive_consensus_debate` runners. The new topology still starts with two independent solvers, but it skips the judge when both solvers parse to the same answer and records that short-circuit as a native `consensus` trace step. This converts part of the previous post-processing fallback into explicit framework behavior and reduces unnecessary provider calls.

### N=200 Adaptive Consensus Follow-Up

To test the revised topology at a larger sample size and lower cost, a second run used Groq `llama-3.1-8b-instant`, `N=200`, shuffled with `seed=42`, four Groq API keys, `max_tokens=64`, and adaptive consensus runners. The initial `concurrency=2` run hit Groq `HTTP 429` on fast runners, so failed rows were removed and resumed with `concurrency=1` plus HTTP retry/backoff. The final JSONL has 1,400 rows: 7 runners x 200 questions, with 0 errors and 0 parse failures.

| Framework | Pattern | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| direct | single call | 200 | 35.5% | 0 | 0 | 0.31s | 0.27s | 0.48s |
| LangGraph | single agent | 200 | 35.5% | 0 | 0 | 2.14s | 2.10s | 2.51s |
| CrewAI | single agent | 200 | 35.5% | 0 | 0 | 7.59s | 7.59s | 10.52s |
| MAF | single agent | 200 | 35.5% | 0 | 0 | 1.15s | 1.14s | 1.35s |
| LangGraph | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 1.71s | 1.67s | 2.07s |
| CrewAI | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 6.96s | 6.89s | 7.65s |
| MAF | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 2.46s | 3.16s | 3.61s |

All three adaptive runners reached the same accuracy because they implement the same topology over the same model backend. The topology short-circuited through solver consensus on 189/200 questions and called the judge on only 11/200 questions, for about 2.06 model calls per question instead of the worst-case 3. This is useful for cost control.

The accuracy gain over single-call baselines was only +2.0 percentage points, or 4 more correct answers out of 200. That is a useful direction for follow-up, but not strong evidence by itself that same-model discussion reliably improves reasoning. The larger signal is operational: adaptive consensus reduced judge calls and gave consistent behavior across frameworks, while latency still reflected framework overhead.

For the overall three-benchmark report, MMLU-Pro should be framed as a **reasoning orchestration benchmark**: it tests whether frameworks can implement deliberation patterns cleanly, and whether those patterns improve closed-book QA accuracy enough to justify their extra calls, latency, and failure risk.

### N=200 Critique and Token-Usage Follow-Up

The final Groq follow-up reran `N=200` with the original seven runners plus the three critique runners. This run used six Groq keys from separate accounts, rebuilt Docker after adding provider usage capture, and recorded provider-reported `prompt_tokens`, `completion_tokens`, and `total_tokens` in every JSONL row and every traced solver/critic/judge call. The final result file has 2,000 rows: 10 runners x 200 questions, with 0 errors and 0 parse failures.

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

The full run consumed 1,750,430 provider-reported tokens. The single-call runners each used 51,941 tokens. Adaptive consensus used about 125.5K tokens per framework, with 411 model calls: 200 solver A calls, 200 solver B calls, and only 11 judge calls because 189/200 questions reached solver consensus. Critique used about 388.7K tokens per framework and 1,000 model calls: two solvers, two critics, and one judge for every question.

Accuracy did not scale with cost. Adaptive consensus produced the best accuracy at 37.5%, a net +4 correct answers over direct. Critique reached only 36.0%, a net +1 over direct. Direct-to-critique transitions were nearly balanced: critique fixed 17 direct-wrong answers but broke 16 direct-correct answers. The trace logs suggest the critique/judge stage often changed answers without a reliable signal that the change was better.

Operationally, the run exposed Groq TPM pressure. Two intermediate rows hit HTTP 429 before the final result: a direct row with a 530-token request and a LangGraph critique row with a 1,338-token request. The adapter was updated so 429/5xx retries rotate keys on each retry and parse Groq's "try again in Xs" message when no `Retry-After` header is present. The final critique portion was resumed at `concurrency=1`, which completed without errors.

### Next Architecture: Selective Critique

The next topology is `selective_critique`, implemented for all three frameworks. It keeps adaptive consensus as the first gate, then runs critique only when the two solvers disagree:

1. Solver A and Solver B answer independently.
2. If their parsed answers match, return consensus immediately.
3. If they disagree, run Critic A and Critic B as cross-critiques.
4. If both critics converge on the same parsed answer, return critic consensus.
5. Otherwise, call a final judge with the original prompt, solver outputs, and critique outputs.

This design directly addresses the critique run's failure mode. Full critique changed many answers, but its gains and losses nearly canceled out: it fixed 17 direct-wrong questions and broke 16 direct-correct questions. Selective critique should avoid touching the 189/200 solver-consensus cases observed in adaptive consensus, while adding extra review only to the 11/200 disagreement cases where the simple judge was weakest.

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

The opencode CLI backend is practical and cheap, but it hides token usage and introduces CLI/database startup behavior. The harness now also supports OpenAI-compatible HTTP backends, including xAI Grok (`--backend grok`) and Groq (`--backend groq`). For a stronger cost study, record token usage from those provider responses.

## Next Steps

1. Add token usage and price extraction for OpenAI-compatible provider responses.
2. Add stratified sampling by category instead of pure shuffle.
3. Run critique topology at `N=50` or `N=100` before trying `N=200`.
4. Add native tool-call and HITL test cases beyond MMLU-Pro.
5. Add observability screenshots/traces for each framework.

## References

- MMLU-Pro paper: https://arxiv.org/abs/2406.01574
- MMLU-Pro dataset: https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro
- LangGraph docs: https://docs.langchain.com/oss/python/langgraph
- CrewAI Flows docs: https://docs.crewai.com/en/concepts/flows
- Microsoft Agent Framework repo: https://github.com/microsoft/agent-framework
- MAF functional workflow docs: https://learn.microsoft.com/en-us/agent-framework/workflows/functional
