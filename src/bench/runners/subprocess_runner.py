from __future__ import annotations

import json
import os
import subprocess
import sys

from bench.model import model_worker_args
from bench.runners.base import BaseRunner


class SubprocessFrameworkRunner(BaseRunner):
    name = "subprocess"

    def answer(self, prompt: str) -> str:
        env = os.environ.copy()
        env["BENCH_WORKER"] = "1"
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in [env.get("PYTHONPATH"), os.path.abspath("src")] if part
        )

        python = self._python_for_framework()
        command = [
            python,
            "-m",
            "bench.worker",
            "--framework",
            self.name,
        ]
        command.extend(model_worker_args(self.model))

        proc = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            if proc.returncode != 0:
                raise RuntimeError((proc.stderr or proc.stdout).strip())
            raise
        self.last_trace = payload.get("trace") or []
        self.last_usage = payload.get("usage")
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout).strip())
        return str(payload["text"])

    def _python_for_framework(self) -> str:
        family = self.name
        for suffix in ("_adaptive_consensus_debate", "_critique", "_debate"):
            if family.endswith(suffix):
                family = family.removesuffix(suffix)
                break
        env_name = f"BENCH_{family.upper()}_PYTHON"
        return os.environ.get(env_name) or sys.executable
