from __future__ import annotations

import argparse
import contextlib
import json
import sys

from bench.model import OpencodeModel
from bench.runners import RUNNERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", required=True, choices=sorted(RUNNERS))
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--no-pure", action="store_true")
    args = parser.parse_args(argv)

    prompt = sys.stdin.read()
    model = OpencodeModel(args.model, timeout_s=args.timeout, pure=not args.no_pure)
    runner = RUNNERS[args.framework](model)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            text = runner.answer(prompt)
        print(json.dumps({"text": text, "error": None}))
    except Exception as exc:
        print(json.dumps({"text": "", "error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
