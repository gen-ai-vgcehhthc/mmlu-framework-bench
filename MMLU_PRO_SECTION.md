# MMLU-Pro Section

## Purpose

MMLU-Pro is used here as a reasoning orchestration benchmark. Unlike GAIA and tau-bench, it does not require external tools, web browsing, persistent state, or business workflow interaction. This makes it useful for isolating whether LangGraph, CrewAI, and Microsoft Agent Framework can implement multi-agent deliberation patterns that improve closed-book reasoning accuracy.

The core question is:

> Given the same model and same MMLU-Pro questions, do framework-orchestrated multi-agent debate patterns improve reasoning accuracy enough to justify their added latency and failure surface?

## Setup

Model backends: `opencode/deepseek-v4-flash-free` via `opencode run --pure`; Groq `llama-3.1-8b-instant` via OpenAI-compatible HTTP  
Dataset: `TIGER-Lab/MMLU-Pro`, test split  
Samples: 50 shuffled DeepSeek questions and 200 shuffled Groq questions, seed 42  
Patterns:

- Direct single call baseline
- LangGraph, CrewAI, and MAF single-agent wrappers
- LangGraph, CrewAI, and MAF two-solver-plus-judge debate
- LangGraph, CrewAI, and MAF adaptive consensus debate

## Results

| Framework | Pattern | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| direct | single call | 50 | 84.0% | 0 | 0 | 10.32s | 6.18s | 27.91s |
| LangGraph | single agent | 50 | 90.0% | 0 | 0 | 12.47s | 7.79s | 38.56s |
| CrewAI | single agent | 50 | 80.0% | 0 | 0 | 15.94s | 12.27s | 31.07s |
| MAF | single agent | 50 | 88.0% | 0 | 0 | 15.13s | 7.36s | 51.65s |
| LangGraph | debate | 50 | 84.0% | 0 | 0 | 26.05s | 17.19s | 68.31s |
| CrewAI | debate | 50 | 80.0% | 0 | 0 | 46.96s | 37.59s | 99.43s |
| MAF | debate | 50 | 84.0% | 0 | 0 | 22.99s | 15.22s | 77.25s |

Follow-up Groq `llama-3.1-8b-instant`, `N=200`, adaptive consensus:

| Framework | Pattern | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| direct | single call | 200 | 35.5% | 0 | 0 | 0.31s | 0.27s | 0.48s |
| LangGraph | single agent | 200 | 35.5% | 0 | 0 | 2.14s | 2.10s | 2.51s |
| CrewAI | single agent | 200 | 35.5% | 0 | 0 | 7.59s | 7.59s | 10.52s |
| MAF | single agent | 200 | 35.5% | 0 | 0 | 1.15s | 1.14s | 1.35s |
| LangGraph | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 1.71s | 1.67s | 2.07s |
| CrewAI | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 6.96s | 6.89s | 7.65s |
| MAF | adaptive consensus debate | 200 | 37.5% | 0 | 0 | 2.46s | 3.16s | 3.61s |

Final Groq `llama-3.1-8b-instant`, `N=200`, adaptive consensus plus critique, with provider token usage recorded:

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

## Interpretation

The single-agent results are close enough that they should not be interpreted as strong evidence that one framework improves model reasoning. The main measurable difference is orchestration overhead and output robustness.

The naive debate topology did not produce a clear, framework-wide reasoning improvement. LangGraph debate underperformed LangGraph single-agent, CrewAI debate matched CrewAI single-agent, and MAF debate underperformed MAF single-agent. Among debate runners, LangGraph and MAF tied at 84%, while CrewAI reached 80% with much higher latency.

The takeaway is that multi-agent deliberation is not automatically beneficial for closed-book multiple-choice reasoning. To justify debate-style orchestration, the framework must show accuracy gains that offset increased model calls, latency, parse failures, and provider timeout risk.

The larger Groq follow-up is more favorable to adaptive consensus but still modest: adaptive consensus improved from 35.5% to 37.5%, a +2.0 point gain or 4 additional correct answers out of 200. All three frameworks produced the same accuracy because they implement the same topology over the same model. The topology did reduce unnecessary judge calls: 189/200 questions short-circuited through solver consensus, and only 11/200 reached the judge.

The critique topology was more expensive but did not improve enough to justify its cost on this model. It improved from 35.5% to 36.0%, or only 1 additional correct answer out of 200, while using about 388.7K tokens per framework versus 51.9K for direct and 125.5K for adaptive consensus. Direct-to-critique transitions show 17 direct-wrong questions fixed but 16 direct-correct questions broken, so the final judge mostly traded errors instead of resolving them. In contrast, adaptive consensus fixed 13 direct-wrong questions and broke 9 direct-correct questions, for a net +4.

This supports a narrower conclusion: same-model multi-agent discussion can change answers, but stronger topology alone is not enough. Adaptive consensus is the best current tradeoff because it gains the most accuracy in this run with far fewer calls than critique. Critique needs either a stronger judge, heterogeneous models, better disagreement detection, or selective invocation only on high-uncertainty items.

## Next Topology: Selective Critique

The next architecture should keep the useful part of adaptive consensus and make critique conditional:

1. Run two independent solvers.
2. If both solvers parse to the same answer, return consensus and skip all later calls.
3. If solvers disagree, run two cross-critics.
4. If both critics converge on the same revised answer, return critic consensus.
5. Otherwise, call a final judge with the original prompt, both solver outputs, and both critiques.

This is implemented as `langgraph_selective_critique`, `crewai_selective_critique`, and `maf_selective_critique`. It targets the main failure observed in full critique: critique fixed 17 direct-wrong answers but broke 16 direct-correct answers. Selective critique should preserve the 189/200 easy consensus cases from adaptive consensus while spending extra reasoning only on disagreement cases, where the previous judge was weakest.

## Trace Note

All 150 debate rows include a `trace` array containing solver A, solver B, and judge outputs with per-call latency and errors. A trace-aware re-score recovers judge-blank rows from solver outputs when appropriate, and the remaining blank rows were retried. Final scoring used raw output for 316 rows, solver consensus fallback for 24 rows, and single-solver fallback for 10 rows.

## Follow-up Topology

The repo now includes two follow-up topologies. `langgraph_adaptive_consensus_debate`, `crewai_adaptive_consensus_debate`, and `maf_adaptive_consensus_debate` make solver consensus a native framework behavior: two solvers run first, and the judge is skipped when both answers match. `langgraph_critique`, `crewai_critique`, and `maf_critique` add two cross-critiques before the final judge. The critique version is more expensive, but better aligned with the hypothesis that multi-agent discussion can improve reasoning by surfacing concrete flaws rather than merely voting.
