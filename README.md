# MMLU-Pro Framework Bench

Compare LangGraph, CrewAI, and Microsoft Agent Framework (MAF) on the same MMLU-Pro prompts and the same model backend.

The default backend is `opencode/deepseek-v4-flash-free` through the local `opencode run` CLI, so it can reuse the free model access already configured on this machine. You can also switch to GitHub Copilot models exposed by opencode, for example `github-copilot/gpt-5.4-mini`.

See [REPORT.md](REPORT.md) for the experiment write-up and framework comparison.

## What This Measures

Quantitative MMLU-Pro run:

- Accuracy
- Parse failures
- Runtime latency: average, median, p95
- Success/error rate
- Concurrency throughput when `--concurrency` is greater than 1
- Debate trace records for multi-agent runs: solver A, solver B, judge output, per-call latency, and per-call errors

Qualitative framework scorecard:

- Runtime & efficiency: cost control, batching, parallelism
- Control & state management: determinism, state/memory, multi-agent topology
- Developer experience: setup, debugging, observability
- External interaction: tools and human approval
- Ecosystem & production: commercial support, community, cloud deployment

MMLU-Pro is useful here because it expands the original MMLU style from four-choice questions to a harder ten-choice setup, which makes answer parsing and reasoning failures easier to see. The framework comparison is still mostly an orchestration comparison: all runners share the same prompt and model backend.

## Quick Start

Host-local smoke test using the installed opencode:

```powershell
python -m pip install -r requirements.txt -e .
python -m venv .venv-langgraph; .\.venv-langgraph\Scripts\pip install -r requirements\langgraph.txt
python -m venv .venv-crewai; .\.venv-crewai\Scripts\pip install -r requirements\crewai.txt
python -m venv .venv-maf; .\.venv-maf\Scripts\pip install -r requirements\maf.txt
$env:BENCH_LANGGRAPH_PYTHON = "$PWD\.venv-langgraph\Scripts\python.exe"
$env:BENCH_CREWAI_PYTHON = "$PWD\.venv-crewai\Scripts\python.exe"
$env:BENCH_MAF_PYTHON = "$PWD\.venv-maf\Scripts\python.exe"
python -m bench.cli --framework direct --limit 3
python -m bench.cli --framework langgraph --framework crewai --framework maf --limit 3
```

Docker smoke test:

```powershell
docker build -t mmlu-framework-bench .
docker run --rm `
  -v ${HOME}/.local/share/opencode/auth.json:/root/.local/share/opencode/auth.json:ro `
  -v ${PWD}/results:/app/results `
  mmlu-framework-bench --framework direct --limit 3
```

Run all frameworks on a small sample:

```powershell
python -m bench.cli `
  --framework direct --framework langgraph --framework crewai --framework maf `
  --model opencode/deepseek-v4-flash-free `
  --limit 20 `
  --output results/sample-20.jsonl `
  --summary results/sample-20-summary.md
```

Try a Copilot model exposed by opencode:

```powershell
python -m bench.cli --framework langgraph --limit 10 --model github-copilot/gpt-5.4-mini
```

## Full Run

The full MMLU-Pro test split is large and can hit free-provider limits. Start with a category or small limit first.

```powershell
python -m bench.cli `
  --framework direct --framework langgraph --framework crewai --framework maf `
  --model opencode/deepseek-v4-flash-free `
  --split test `
  --output results/full.jsonl `
  --summary results/full-summary.md
```

Useful switches:

- `--category math` filters MMLU-Pro categories.
- `--limit 50` caps questions after filtering.
- `--shuffle --seed 42` samples across the split instead of taking the dataset's first rows.
- `--concurrency 2` runs questions in parallel. Keep this low for free providers.
- `--dataset TIGER-Lab/MMLU-Pro` changes the dataset source if needed.
- `--prewarm` spends one cheap model call before each framework to keep opencode first-run migration logs out of the measured calls.

## Notes

- `direct` is a baseline runner with no agent framework.
- `langgraph` wraps the same model call in a `StateGraph`.
- `crewai` wraps the same model call in a CrewAI Flow.
- `maf` wraps the same model call in Microsoft Agent Framework functional workflow.
- `langgraph_debate`, `crewai_debate`, and `maf_debate` use the same two-solver-plus-judge topology to test whether multi-agent discussion improves MMLU-Pro reasoning.
- Debate runners emit a `trace` array in JSONL results so solver and judge behavior can be inspected after the run.
- The Docker image installs each framework in its own virtual environment because current CrewAI and MAF releases require incompatible OpenTelemetry versions.
- Cost is marked unavailable for opencode CLI runs because the CLI output does not expose per-call token usage in a stable machine-readable format.
