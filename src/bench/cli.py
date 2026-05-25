from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bench.data import load_questions
from bench.model import add_model_args, build_model
from bench.parse import clean_output, parse_answer_with_trace
from bench.prompt import build_prompt
from bench.report import summarize
from bench.runners import RUNNERS
from bench.types import Question, RunResult


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    questions = load_questions(args.dataset, args.split, args.limit, args.category, args.shuffle, args.seed)
    if not questions:
        print("No questions matched the requested filters.", file=sys.stderr)
        return 2

    all_results: list[RunResult] = []
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = load_completed(output_path) if args.resume else set()
    if not args.resume:
        output_path.write_text("", encoding="utf-8")
    else:
        all_results.extend(load_existing(output_path))

    started = time.perf_counter()
    enforce_total_call_budget(args.framework, questions, completed, args.parse_retries, args.prewarm, args.max_model_calls)
    for framework in args.framework:
        pending = [question for question in questions if (framework, question.id) not in completed]
        if not pending:
            print(f"Skipping {framework}; all requested questions already exist in {args.output}", file=sys.stderr)
            continue
        runner_cls = RUNNERS[framework]
        model = build_model(args)
        if args.prewarm:
            model.complete("Return only the letter A.")
        print(f"Running {framework} on {len(pending)} questions with {model.model}", file=sys.stderr)
        for result in run_framework_iter(
            framework,
            model.model,
            runner_cls,
            model,
            pending,
            args.concurrency,
            args.parse_retries,
        ):
            append_jsonl(output_path, [result])
            all_results.append(result)
            completed.add((framework, result.question_id))
            print(
                f"{framework} {result.question_id}: predicted={result.predicted} expected={result.expected} "
                f"correct={result.correct} elapsed={result.elapsed_s:.2f}s",
                file=sys.stderr,
            )

    summary = summarize(all_results)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(summary, encoding="utf-8")
    elapsed = time.perf_counter() - started
    print(summary)
    print(f"Wall time: {elapsed:.2f}s")
    return 0


def run_framework_iter(
    framework: str,
    model: str,
    runner_cls,
    model_client,
    questions: list[Question],
    concurrency: int,
    parse_retries: int,
):
    if concurrency <= 1:
        runner = runner_cls(model_client)
        for question in questions:
            yield run_one(framework, model, runner, question, parse_retries=parse_retries)
        return

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(run_one, framework, model, runner_cls(model_client), question, parse_retries)
            for question in questions
        ]
        for future in as_completed(futures):
            yield future.result()


def run_one(framework: str, model: str, runner, question: Question, parse_retries: int = 0) -> RunResult:
    prompt = build_prompt(question)
    total_elapsed = 0.0
    last_result: RunResult | None = None

    for attempt in range(parse_retries + 1):
        runner.last_trace = []
        runner.last_usage = None
        started = time.perf_counter()
        try:
            raw = runner.answer(prompt)
            elapsed = time.perf_counter() - started
            total_elapsed += elapsed
            predicted, prediction_source = parse_answer_with_trace(raw, runner.last_trace or None)
            last_result = RunResult(
                framework=framework,
                model=model,
                question_id=question.id,
                category=question.category,
                expected=question.answer,
                predicted=predicted,
                correct=predicted == question.answer,
                elapsed_s=total_elapsed,
                raw_output=clean_output(raw),
                trace=runner.last_trace or None,
                prediction_source=prediction_source,
                usage=runner.last_usage,
                attempts=attempt + 1,
            )
            if predicted is not None:
                return last_result
        except Exception as exc:
            elapsed = time.perf_counter() - started
            total_elapsed += elapsed
            return RunResult(
                framework=framework,
                model=model,
                question_id=question.id,
                category=question.category,
                expected=question.answer,
                predicted=None,
                correct=False,
                elapsed_s=total_elapsed,
                raw_output="",
                error=str(exc),
                trace=runner.last_trace or None,
                usage=runner.last_usage,
                attempts=attempt + 1,
            )

    if last_result is None:
        raise RuntimeError("unreachable: run_one produced no result")
    return last_result


def append_jsonl(path: Path, results: list[RunResult]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result.to_json(), ensure_ascii=False) + "\n")


def load_existing(path: Path) -> list[RunResult]:
    if not path.exists():
        return []
    rows: list[RunResult] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        rows.append(RunResult(**payload))
    return rows


def load_completed(path: Path) -> set[tuple[str, str]]:
    return {(row.framework, row.question_id) for row in load_existing(path)}


def estimate_model_calls(framework: str, n_questions: int, parse_retries: int, prewarm: bool) -> int:
    per_attempt = 1
    if framework.endswith("_adaptive_consensus_debate"):
        per_attempt = 3
    elif framework.endswith("_critique"):
        per_attempt = 5
    attempts = parse_retries + 1
    return n_questions * per_attempt * attempts + (1 if prewarm else 0)


def enforce_total_call_budget(
    frameworks: list[str],
    questions: list[Question],
    completed: set[tuple[str, str]],
    parse_retries: int,
    prewarm: bool,
    max_model_calls: int | None,
) -> None:
    if max_model_calls is None:
        return
    estimated = 0
    for framework in frameworks:
        pending = [question for question in questions if (framework, question.id) not in completed]
        estimated += estimate_model_calls(framework, len(pending), parse_retries, prewarm)
    if estimated > max_model_calls:
        raise SystemExit(
            f"requested run would use up to {estimated} model calls, exceeding --max-model-calls {max_model_calls}."
        )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MMLU-Pro across agent frameworks.")
    parser.add_argument("--framework", action="append", choices=sorted(RUNNERS), default=None)
    add_model_args(parser)
    parser.add_argument("--dataset", default="TIGER-Lab/MMLU-Pro")
    parser.add_argument("--split", default="test")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--output", default="results/run.jsonl")
    parser.add_argument("--summary", default="results/summary.md")
    parser.add_argument("--prewarm", action="store_true", help="Run one cheap model call before each framework.")
    parser.add_argument("--resume", action="store_true", help="Append to existing output and skip completed rows.")
    parser.add_argument("--parse-retries", type=int, default=0, help="Retry a question when parsing still fails after trace fallback.")
    parser.add_argument("--max-model-calls", type=int, help="Abort when a framework could exceed this many model calls.")
    args = parser.parse_args(argv)
    if args.framework is None:
        args.framework = ["direct", "langgraph", "crewai", "maf"]
    return args


if __name__ == "__main__":
    raise SystemExit(main())
