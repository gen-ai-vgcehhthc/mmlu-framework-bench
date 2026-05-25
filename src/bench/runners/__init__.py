from __future__ import annotations

import os

from bench.runners.base import BaseRunner
from bench.runners.direct import DirectRunner
from bench.runners.subprocess_runner import SubprocessFrameworkRunner


if os.environ.get("BENCH_WORKER") == "1":
    from bench.runners.crewai_debate_runner import CrewAIDebateRunner
    from bench.runners.crewai_critique_runner import CrewAICritiqueRunner
    from bench.runners.crewai_runner import CrewAIRunner
    from bench.runners.langgraph_debate_runner import LangGraphDebateRunner
    from bench.runners.langgraph_critique_runner import LangGraphCritiqueRunner
    from bench.runners.langgraph_runner import LangGraphRunner
    from bench.runners.maf_critique_runner import MAFCritiqueRunner
    from bench.runners.maf_debate_runner import MAFDebateRunner
    from bench.runners.maf_runner import MAFRunner

    RUNNERS: dict[str, type[BaseRunner]] = {
        "direct": DirectRunner,
        "langgraph": LangGraphRunner,
        "langgraph_debate": LangGraphDebateRunner,
        "langgraph_critique": LangGraphCritiqueRunner,
        "crewai": CrewAIRunner,
        "crewai_debate": CrewAIDebateRunner,
        "crewai_critique": CrewAICritiqueRunner,
        "maf": MAFRunner,
        "maf_debate": MAFDebateRunner,
        "maf_critique": MAFCritiqueRunner,
    }
else:

    class LangGraphSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph"

    class LangGraphDebateSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph_debate"

    class LangGraphCritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph_critique"

    class CrewAISubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai"

    class CrewAIDebateSubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai_debate"

    class CrewAICritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai_critique"

    class MAFSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf"

    class MAFDebateSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf_debate"

    class MAFCritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf_critique"

    RUNNERS: dict[str, type[BaseRunner]] = {
        "direct": DirectRunner,
        "langgraph": LangGraphSubprocessRunner,
        "langgraph_debate": LangGraphDebateSubprocessRunner,
        "langgraph_critique": LangGraphCritiqueSubprocessRunner,
        "crewai": CrewAISubprocessRunner,
        "crewai_debate": CrewAIDebateSubprocessRunner,
        "crewai_critique": CrewAICritiqueSubprocessRunner,
        "maf": MAFSubprocessRunner,
        "maf_debate": MAFDebateSubprocessRunner,
        "maf_critique": MAFCritiqueSubprocessRunner,
    }
