from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bench.data import load_questions
from bench.model import OpencodeModel
from bench.parse import clean_output, parse_answer
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
    started = time.perf_counter()
    for framework in args.framework:
        runner_cls = RUNNERS[framework]
        model = OpencodeModel(model=args.model, timeout_s=args.timeout, pure=not args.no_pure)
        if args.prewarm:
            model.complete("Return only the letter A.")
        runner = runner_cls(model)
        print(f"Running {framework} on {len(questions)} questions with {args.model}", file=sys.stderr)
        all_results.extend(run_framework(framework, args.model, runner, questions, args.concurrency))

    write_jsonl(Path(args.output), all_results)
    summary = summarize(all_results)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(summary, encoding="utf-8")
    elapsed = time.perf_counter() - started
    print(summary)
    print(f"Wall time: {elapsed:.2f}s")
    return 0


def run_framework(framework: str, model: str, runner, questions: list[Question], concurrency: int) -> list[RunResult]:
    if concurrency <= 1:
        return [run_one(framework, model, runner, question) for question in questions]

    results: list[RunResult] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(run_one, framework, model, runner, question) for question in questions]
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda item: item.question_id)


def run_one(framework: str, model: str, runner, question: Question) -> RunResult:
    prompt = build_prompt(question)
    started = time.perf_counter()
    try:
        raw = runner.answer(prompt)
        elapsed = time.perf_counter() - started
        predicted = parse_answer(raw)
        return RunResult(
            framework=framework,
            model=model,
            question_id=question.id,
            category=question.category,
            expected=question.answer,
            predicted=predicted,
            correct=predicted == question.answer,
            elapsed_s=elapsed,
            raw_output=clean_output(raw),
        )
    except Exception as exc:
        elapsed = time.perf_counter() - started
        return RunResult(
            framework=framework,
            model=model,
            question_id=question.id,
            category=question.category,
            expected=question.answer,
            predicted=None,
            correct=False,
            elapsed_s=elapsed,
            raw_output="",
            error=str(exc),
        )


def write_jsonl(path: Path, results: list[RunResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result.to_json(), ensure_ascii=False) + "\n")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MMLU-Pro across agent frameworks.")
    parser.add_argument("--framework", action="append", choices=sorted(RUNNERS), default=None)
    parser.add_argument("--model", default="opencode/deepseek-v4-flash-free")
    parser.add_argument("--dataset", default="TIGER-Lab/MMLU-Pro")
    parser.add_argument("--split", default="test")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output", default="results/run.jsonl")
    parser.add_argument("--summary", default="results/summary.md")
    parser.add_argument("--prewarm", action="store_true", help="Run one cheap model call before each framework.")
    parser.add_argument("--no-pure", action="store_true", help="Do not pass --pure to opencode.")
    args = parser.parse_args(argv)
    if args.framework is None:
        args.framework = ["direct", "langgraph", "crewai", "maf"]
    return args


if __name__ == "__main__":
    raise SystemExit(main())
