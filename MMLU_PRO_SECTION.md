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
| CrewAI | single agent | 50 | 76.0% | 1 | 2 | 18.90s | 12.06s | 44.19s |
| MAF | single agent | 50 | 80.0% | 1 | 4 | 15.31s | 7.36s | 51.65s |
| LangGraph | debate | 50 | 68.0% | 0 | 5 | 18.84s | 14.90s | 31.82s |
| CrewAI | debate | 50 | 54.0% | 15 | 1 | 79.70s | 31.13s | 186.75s |
| MAF | debate | 50 | 0.0% | 50 | 0 | 181.27s | 181.09s | 182.65s |

## Interpretation

The single-agent results are close enough that they should not be interpreted as strong evidence that one framework improves model reasoning. The main measurable difference is orchestration overhead and output robustness.

The naive debate topology did not improve MMLU-Pro accuracy. LangGraph debate underperformed LangGraph single-agent, and CrewAI debate underperformed CrewAI single-agent while introducing substantial timeout risk. MAF debate was not a valid reasoning result because it ran after the free opencode backend had entered sustained timeout behavior; all 50 examples timed out.

The takeaway is that multi-agent deliberation is not automatically beneficial for closed-book multiple-choice reasoning. To justify debate-style orchestration, the framework must show accuracy gains that offset increased model calls, latency, parse failures, and provider timeout risk.

## Reporting Note

The MAF debate row should be described as backend/provider exhaustion, not as a MAF reasoning failure. A fair follow-up should rerun the debate rows in randomized order or separate fresh provider sessions, and should log model call counts and token cost.
