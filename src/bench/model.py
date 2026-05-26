from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import threading
import tempfile
import time
from dataclasses import dataclass
from typing import Protocol
from urllib import error, request

from bench.types import ModelResult


_KEY_LOCK = threading.Lock()
_KEY_COUNTERS: dict[str, int] = {}


class ModelClient(Protocol):
    model: str
    timeout_s: int
    pure: bool

    def complete(self, prompt: str) -> ModelResult: ...


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
                partial = _coerce_text(exc.stdout) + _coerce_text(exc.stderr)
                return ModelResult(text=partial, elapsed_s=elapsed, error="timeout")

        elapsed = time.perf_counter() - start
        text = (proc.stdout or "") + (proc.stderr or "")
        error = None if proc.returncode == 0 else f"opencode exited {proc.returncode}"
        return ModelResult(text=text, elapsed_s=elapsed, error=error)


@dataclass(frozen=True)
class OpenAICompatibleModel:
    model: str
    base_url: str
    api_key_env: str
    timeout_s: int = 180
    max_tokens: int = 512
    temperature: float = 0.0
    http_retries: int = 3
    pure: bool = True

    def complete(self, prompt: str) -> ModelResult:
        if not list_api_keys(self.api_key_env):
            return ModelResult(
                text="",
                elapsed_s=0.0,
                error=f"missing API key env var(s): {self.api_key_env}",
            )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        url = self.base_url.rstrip("/") + "/chat/completions"

        start = time.perf_counter()
        raw = ""
        for attempt in range(self.http_retries + 1):
            api_key = resolve_api_key(self.api_key_env)
            req = request.Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "mmlu-framework-bench/0.1",
                },
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=self.timeout_s) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                    break
            except error.HTTPError as exc:
                elapsed = time.perf_counter() - start
                details = exc.read().decode("utf-8", errors="replace")
                if exc.code == 429 or 500 <= exc.code <= 599:
                    if attempt < self.http_retries:
                        time.sleep(_retry_delay(exc, attempt, details))
                        continue
                return ModelResult(text=details, elapsed_s=elapsed, error=f"HTTP {exc.code}")
            except Exception as exc:
                elapsed = time.perf_counter() - start
                return ModelResult(text="", elapsed_s=elapsed, error=str(exc))

        elapsed = time.perf_counter() - start
        try:
            data = json.loads(raw)
            text = data["choices"][0]["message"]["content"] or ""
        except Exception as exc:
            return ModelResult(text=raw, elapsed_s=elapsed, error=f"invalid response JSON: {exc}")
        usage = data.get("usage")
        return ModelResult(text=text, elapsed_s=elapsed, error=None, usage=usage if isinstance(usage, dict) else None)


@dataclass(frozen=True)
class RoleRoutedModel:
    primary: ModelClient
    secondary: ModelClient
    secondary_roles: tuple[str, ...] = ("solver_b", "critic_b")

    @property
    def model(self) -> str:
        roles = ",".join(self.secondary_roles)
        return f"{self.primary.model}+{self.secondary.model}@{roles}"

    @property
    def timeout_s(self) -> int:
        return self.primary.timeout_s

    @property
    def pure(self) -> bool:
        return self.primary.pure

    def complete(self, prompt: str) -> ModelResult:
        return self.primary.complete(prompt)

    def for_role(self, role: str) -> ModelClient:
        return self.secondary if role in self.secondary_roles else self.primary


def add_model_args(parser: argparse.ArgumentParser, *, require_model: bool = False) -> None:
    parser.add_argument(
        "--backend",
        choices=["opencode", "openai-compatible", "grok", "groq"],
        default="opencode",
        help="Model backend. grok and groq are OpenAI-compatible shortcuts.",
    )
    parser.add_argument("--model", required=require_model, default=None)
    parser.add_argument("--base-url", help="OpenAI-compatible base URL, for example https://api.x.ai/v1.")
    parser.add_argument(
        "--api-key-env",
        help=(
            "Environment variable containing one key, multiple comma/semicolon-separated keys, "
            "or comma-separated env var names. Numbered suffixes like GROQ_API_KEY_1 are auto-detected."
        ),
    )
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--http-retries", type=int, default=3, help="Retry OpenAI-compatible HTTP 429/5xx responses.")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--no-pure", action="store_true", help="Do not pass --pure to opencode.")
    parser.add_argument(
        "--secondary-backend",
        choices=["opencode", "openai-compatible", "grok", "groq"],
        help="Optional secondary model backend for role-routed multi-agent runs.",
    )
    parser.add_argument("--secondary-model", help="Model name for the secondary role-routed model.")
    parser.add_argument("--secondary-base-url", help="OpenAI-compatible base URL for the secondary model.")
    parser.add_argument("--secondary-api-key-env", help="API key env spec for the secondary model.")
    parser.add_argument(
        "--secondary-roles",
        default="solver_b,critic_b",
        help="Comma-separated trace roles routed to the secondary model. Default: solver_b,critic_b.",
    )


def build_model(args: argparse.Namespace) -> ModelClient:
    primary = build_backend_model(
        backend=args.backend,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        args=args,
    )
    if not args.secondary_backend:
        return primary

    secondary = build_backend_model(
        backend=args.secondary_backend,
        model=args.secondary_model,
        base_url=args.secondary_base_url,
        api_key_env=args.secondary_api_key_env,
        args=args,
    )
    secondary_roles = tuple(role.strip() for role in args.secondary_roles.split(",") if role.strip())
    return RoleRoutedModel(primary=primary, secondary=secondary, secondary_roles=secondary_roles)


def build_backend_model(
    *,
    backend: str,
    model: str | None,
    base_url: str | None,
    api_key_env: str | None,
    args: argparse.Namespace,
) -> ModelClient:
    if backend == "opencode":
        model = model or "opencode/deepseek-v4-flash-free"
        return OpencodeModel(model=model, timeout_s=args.timeout, pure=not args.no_pure)

    if backend == "grok":
        base_url = base_url or "https://api.x.ai/v1"
        api_key_env = api_key_env or "XAI_API_KEY,XAI_API_KEYS"
        model = model or "grok-4.3"
    elif backend == "groq":
        base_url = base_url or "https://api.groq.com/openai/v1"
        api_key_env = api_key_env or "GROQ_API_KEY,GROQ_API_KEYS"
        model = model or "llama-3.1-8b-instant"
    else:
        if not base_url:
            raise SystemExit("--base-url is required for --backend openai-compatible")
        api_key_env = api_key_env or "OPENAI_COMPATIBLE_API_KEY"
        if not model:
            raise SystemExit("--model is required for --backend openai-compatible")

    return OpenAICompatibleModel(
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        timeout_s=args.timeout,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        http_retries=args.http_retries,
        pure=not args.no_pure,
    )


def model_worker_args(model: ModelClient) -> list[str]:
    if isinstance(model, RoleRoutedModel):
        args = model_worker_args(model.primary)
        args.extend(secondary_model_worker_args(model.secondary))
        args.extend(["--secondary-roles", ",".join(model.secondary_roles)])
        return args
    if isinstance(model, OpencodeModel):
        args = ["--backend", "opencode", "--model", model.model, "--timeout", str(model.timeout_s)]
        if not model.pure:
            args.append("--no-pure")
        return args
    if isinstance(model, OpenAICompatibleModel):
        return [
            "--backend",
            "openai-compatible",
            "--model",
            model.model,
            "--timeout",
            str(model.timeout_s),
            "--base-url",
            model.base_url,
            "--api-key-env",
            model.api_key_env,
            "--max-tokens",
            str(model.max_tokens),
            "--temperature",
            str(model.temperature),
            "--http-retries",
            str(model.http_retries),
        ]
    raise TypeError(f"unsupported model client: {type(model)!r}")


def secondary_model_worker_args(model: ModelClient) -> list[str]:
    if isinstance(model, OpencodeModel):
        args = ["--secondary-backend", "opencode", "--secondary-model", model.model]
        if not model.pure:
            args.append("--no-pure")
        return args
    if isinstance(model, OpenAICompatibleModel):
        return [
            "--secondary-backend",
            "openai-compatible",
            "--secondary-model",
            model.model,
            "--secondary-base-url",
            model.base_url,
            "--secondary-api-key-env",
            model.api_key_env,
        ]
    raise TypeError(f"unsupported secondary model client: {type(model)!r}")


def resolve_api_key(env_spec: str) -> str | None:
    keys = list_api_keys(env_spec)
    if not keys:
        return None
    with _KEY_LOCK:
        start = _KEY_COUNTERS.setdefault(env_spec, os.getpid())
        index = start % len(keys)
        _KEY_COUNTERS[env_spec] = start + 1
    return keys[index]


def list_api_keys(env_spec: str) -> list[str]:
    keys: list[str] = []
    env_names = [part.strip() for part in env_spec.split(",") if part.strip()]
    for env_name in env_names:
        keys.extend(_split_keys(os.environ.get(env_name, "")))
        keys.extend(_numbered_env_keys(env_name))
    return _dedupe(keys)


def _numbered_env_keys(prefix: str) -> list[str]:
    keys: list[str] = []
    for index in range(1, 21):
        keys.extend(_split_keys(os.environ.get(f"{prefix}_{index}", "")))
    return keys


def _split_keys(value: str) -> list[str]:
    normalized = value.replace(";", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _retry_delay(exc: error.HTTPError, attempt: int, details: str = "") -> float:
    retry_after = exc.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass
    match = re.search(r"try again in ([0-9.]+)s", details, flags=re.IGNORECASE)
    if match:
        return max(float(match.group(1)) + 0.25, 0.0)
    return min(2.0 ** attempt, 30.0)


def _coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
