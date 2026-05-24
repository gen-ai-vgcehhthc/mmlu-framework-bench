from __future__ import annotations

import json
import os
import subprocess
import sys

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
            "--model",
            self.model.model,
            "--timeout",
            str(self.model.timeout_s),
        ]
        if not self.model.pure:
            command.append("--no-pure")

        proc = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout).strip())
        payload = json.loads(proc.stdout)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        return str(payload["text"])

    def _python_for_framework(self) -> str:
        family = self.name
        if family.endswith("_debate"):
            family = family.removesuffix("_debate")
        env_name = f"BENCH_{family.upper()}_PYTHON"
        return os.environ.get(env_name) or sys.executable
