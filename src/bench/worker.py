from __future__ import annotations

import argparse
import contextlib
import json
import sys

from bench.model import add_model_args, build_model
from bench.runners import RUNNERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", required=True, choices=sorted(RUNNERS))
    add_model_args(parser, require_model=True)
    args = parser.parse_args(argv)

    prompt = sys.stdin.read()
    model = build_model(args)
    runner = RUNNERS[args.framework](model)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            text = runner.answer(prompt)
        print(json.dumps({"text": text, "error": None, "trace": runner.last_trace}))
    except Exception as exc:
        print(json.dumps({"text": "", "error": str(exc), "trace": runner.last_trace}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
