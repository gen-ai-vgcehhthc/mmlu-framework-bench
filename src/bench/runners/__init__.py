from __future__ import annotations

import os

from bench.runners.base import BaseRunner
from bench.runners.direct import DirectRunner
from bench.runners.subprocess_runner import SubprocessFrameworkRunner


if os.environ.get("BENCH_WORKER") == "1":
    from bench.runners.crewai_runner import CrewAIRunner
    from bench.runners.langgraph_runner import LangGraphRunner
    from bench.runners.maf_runner import MAFRunner

    RUNNERS: dict[str, type[BaseRunner]] = {
        "direct": DirectRunner,
        "langgraph": LangGraphRunner,
        "crewai": CrewAIRunner,
        "maf": MAFRunner,
    }
else:

    class LangGraphSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph"

    class CrewAISubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai"

    class MAFSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf"

    RUNNERS: dict[str, type[BaseRunner]] = {
        "direct": DirectRunner,
        "langgraph": LangGraphSubprocessRunner,
        "crewai": CrewAISubprocessRunner,
        "maf": MAFSubprocessRunner,
    }
