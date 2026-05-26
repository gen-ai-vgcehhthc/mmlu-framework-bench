# MMLU-Pro Framework Bench

Compare LangGraph, CrewAI, and Microsoft Agent Framework (MAF) on the same MMLU-Pro prompts and the same model backend.

The default backend is `opencode/deepseek-v4-flash-free` through the local `opencode run` CLI, so it can reuse the free model access already configured on this machine. You can also use OpenAI-compatible HTTP backends such as xAI Grok or Groq.

See [REPORT.md](REPORT.md) for the experiment write-up and framework comparison.

## What This Measures

Quantitative MMLU-Pro run:

- Accuracy
- Parse failures
- Runtime latency: average, median, p95
- Provider-reported token usage for OpenAI-compatible HTTP backends
- Success/error rate
- Concurrency throughput when `--concurrency` is greater than 1
- Adaptive consensus debate and critique trace records for multi-agent runs: solver, critic, judge output, consensus short-circuits, per-call latency, and per-call errors

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

Try xAI Grok through the OpenAI-compatible API:

```powershell
$env:XAI_API_KEY = "<your key>"
python -m bench.cli `
  --backend grok `
  --model grok-4.3 `
  --framework langgraph_adaptive_consensus_debate `
  --limit 5 `
  --output results/grok-smoke.jsonl `
  --summary results/grok-smoke-summary.md
```

Try Groq Free through the same adapter:

```powershell
$env:GROQ_API_KEY = "<your key>"
python -m bench.cli `
  --backend groq `
  --model llama-3.1-8b-instant `
  --framework direct `
  --framework maf_adaptive_consensus_debate `
  --limit 5 `
  --output results/groq-smoke.jsonl `
  --summary results/groq-smoke-summary.md
```

Multiple Groq keys can be rotated automatically:

```powershell
$env:GROQ_API_KEYS = "<key1>;<key2>;<key3>"
python -m bench.cli `
  --backend groq `
  --api-key-env GROQ_API_KEYS `
  --model llama-3.1-8b-instant `
  --framework direct `
  --limit 20
```

Alternatively, set `GROQ_API_KEY_1`, `GROQ_API_KEY_2`, and so on; `--backend groq` auto-detects numbered suffixes from the default `GROQ_API_KEY` prefix.

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
- `--parse-retries 1` retries a question when parsing still fails after trace fallback. This reduces blank-output failures but increases model calls.
- `--http-retries 5` retries OpenAI-compatible HTTP 429/5xx responses with backoff.
- `--backend grok` uses xAI's OpenAI-compatible chat completions endpoint with `XAI_API_KEY`.
- `--backend groq` uses Groq's OpenAI-compatible endpoint with `GROQ_API_KEY`, `GROQ_API_KEYS`, or numbered `GROQ_API_KEY_1` style variables.
- `--backend openai-compatible --base-url ... --api-key-env ...` works for other compatible providers.
- `--max-model-calls 300` aborts before a framework run if the worst-case call count could exceed the budget.
- `--api-key-env GROQ_API_KEYS` rotates across multiple keys when the env var contains comma- or semicolon-separated keys.
- OpenAI-compatible responses that include a `usage` object are written to JSONL rows and trace events, then summarized as prompt, completion, and total tokens.

Re-score an existing JSONL with the current parser and debate trace fallback:

```powershell
python -m bench.rescore results/mmlu-pro-debate50-seed42.jsonl `
  --in-place `
  --summary results/mmlu-pro-debate50-seed42-summary.md
```

## Notes

- `direct` is a baseline runner with no agent framework.
- `langgraph` wraps the same model call in a `StateGraph`.
- `crewai` wraps the same model call in a CrewAI Flow.
- `maf` wraps the same model call in Microsoft Agent Framework functional workflow.
- `langgraph_adaptive_consensus_debate`, `crewai_adaptive_consensus_debate`, and `maf_adaptive_consensus_debate` run two independent solvers first. If both parse to the same answer, the runner records a `consensus` trace step and skips the judge call; otherwise it calls a judge.
- `langgraph_critique`, `crewai_critique`, and `maf_critique` add a critique topology: two solvers, two cross-critiques, then one judge.
- `langgraph_selective_critique`, `crewai_selective_critique`, and `maf_selective_critique` run critique only when the two solvers disagree. If critics converge, the judge is skipped; otherwise a final judge sees the solvers and critiques.
- Multi-agent runners emit a `trace` array in JSONL results so solver, critic, and judge behavior can be inspected after the run.
- The Docker image installs each framework in its own virtual environment because current CrewAI and MAF releases require incompatible OpenTelemetry versions.
- Cost is marked unavailable for opencode CLI runs because the CLI output does not expose per-call token usage in a stable machine-readable format. Groq/Grok/OpenAI-compatible HTTP runs record provider token usage when the provider returns it.
