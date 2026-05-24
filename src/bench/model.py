from __future__ import annotations

import os
import subprocess
import tempfile
import time
from dataclasses import dataclass

from bench.types import ModelResult


@dataclass(frozen=True)
class OpencodeModel:
    model: str
    timeout_s: int = 180
    pure: bool = True

    def complete(self, prompt: str) -> ModelResult:
        command = ["opencode", "run"]
        if self.pure:
            command.append("--pure")
        command.extend(["-m", self.model, "--", prompt])

        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="mmlu-opencode-") as workdir:
            env = os.environ.copy()
            env.setdefault("NO_COLOR", "1")
            try:
                proc = subprocess.run(
                    command,
                    cwd=workdir,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_s,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                elapsed = time.perf_counter() - start
                partial = (exc.stdout or "") + (exc.stderr or "")
                return ModelResult(text=partial, elapsed_s=elapsed, error="timeout")

        elapsed = time.perf_counter() - start
        text = (proc.stdout or "") + (proc.stderr or "")
        error = None if proc.returncode == 0 else f"opencode exited {proc.returncode}"
        return ModelResult(text=text, elapsed_s=elapsed, error=error)
