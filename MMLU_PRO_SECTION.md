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

## Interpretation

The single-agent results are close enough that they should not be interpreted as strong evidence that one framework improves model reasoning. The main measurable difference is orchestration overhead and output robustness.

The naive debate topology did not produce a clear, framework-wide reasoning improvement. LangGraph debate underperformed LangGraph single-agent, CrewAI debate matched CrewAI single-agent, and MAF debate underperformed MAF single-agent. Among debate runners, LangGraph and MAF tied at 84%, while CrewAI reached 80% with much higher latency.

The takeaway is that multi-agent deliberation is not automatically beneficial for closed-book multiple-choice reasoning. To justify debate-style orchestration, the framework must show accuracy gains that offset increased model calls, latency, parse failures, and provider timeout risk.

The larger Groq follow-up is more favorable to adaptive consensus but still modest: adaptive consensus improved from 35.5% to 37.5%, a +2.0 point gain or 4 additional correct answers out of 200. All three frameworks produced the same accuracy because they implement the same topology over the same model. The topology did reduce unnecessary judge calls: 189/200 questions short-circuited through solver consensus, and only 11/200 reached the judge.

## Trace Note

All 150 debate rows include a `trace` array containing solver A, solver B, and judge outputs with per-call latency and errors. A trace-aware re-score recovers judge-blank rows from solver outputs when appropriate, and the remaining blank rows were retried. Final scoring used raw output for 316 rows, solver consensus fallback for 24 rows, and single-solver fallback for 10 rows.

## Follow-up Topology

The repo now includes two follow-up topologies. `langgraph_adaptive_consensus_debate`, `crewai_adaptive_consensus_debate`, and `maf_adaptive_consensus_debate` make solver consensus a native framework behavior: two solvers run first, and the judge is skipped when both answers match. `langgraph_critique`, `crewai_critique`, and `maf_critique` add two cross-critiques before the final judge. The critique version is more expensive, but better aligned with the hypothesis that multi-agent discussion can improve reasoning by surfacing concrete flaws rather than merely voting.
