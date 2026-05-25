# MMLU-Pro Section

## Purpose

MMLU-Pro is used here as a reasoning orchestration benchmark. Unlike GAIA and tau-bench, it does not require external tools, web browsing, persistent state, or business workflow interaction. This makes it useful for isolating whether LangGraph, CrewAI, and Microsoft Agent Framework can implement multi-agent deliberation patterns that improve closed-book reasoning accuracy.

The core question is:

> Given the same model and same MMLU-Pro questions, do framework-orchestrated multi-agent debate patterns improve reasoning accuracy enough to justify their added latency and failure surface?

## Setup

Model backend: `opencode/deepseek-v4-flash-free` via `opencode run --pure`  
Dataset: `TIGER-Lab/MMLU-Pro`, test split  
Sample: 50 shuffled questions, seed 42  
Patterns:

- Direct single call baseline
- LangGraph, CrewAI, and MAF single-agent wrappers
- LangGraph, CrewAI, and MAF two-solver-plus-judge debate

## Results

| Framework | Pattern | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| direct | single call | 50 | 82.0% | 0 | 1 | 10.24s | 6.09s | 27.91s |
| LangGraph | single agent | 50 | 88.0% | 0 | 1 | 12.47s | 7.79s | 38.56s |
| CrewAI | single agent | 50 | 78.0% | 0 | 2 | 15.88s | 12.06s | 31.07s |
| MAF | single agent | 50 | 82.0% | 0 | 4 | 15.14s | 7.36s | 51.65s |
| LangGraph | debate | 50 | 60.0% | 0 | 13 | 26.09s | 17.57s | 68.31s |
| CrewAI | debate | 50 | 40.0% | 0 | 23 | 47.67s | 38.37s | 99.43s |
| MAF | debate | 50 | 78.0% | 0 | 4 | 22.97s | 15.22s | 77.25s |

## Interpretation

The single-agent results are close enough that they should not be interpreted as strong evidence that one framework improves model reasoning. The main measurable difference is orchestration overhead and output robustness.

The naive debate topology did not improve MMLU-Pro accuracy. LangGraph debate underperformed LangGraph single-agent, CrewAI debate underperformed CrewAI single-agent, and MAF debate was slightly below MAF single-agent. Among debate runners, MAF was the most robust: it reached 78% accuracy with only 4 parse failures, compared with 60% / 13 parse failures for LangGraph debate and 40% / 23 parse failures for CrewAI debate.

The takeaway is that multi-agent deliberation is not automatically beneficial for closed-book multiple-choice reasoning. To justify debate-style orchestration, the framework must show accuracy gains that offset increased model calls, latency, parse failures, and provider timeout risk.

## Trace Note

All 150 debate rows include a `trace` array containing solver A, solver B, and judge outputs with per-call latency and errors. The traces show that many debate failures were judge/output-control failures rather than clean reasoning mistakes: solvers often produced a valid option, but the judge returned blank or non-parseable output.
