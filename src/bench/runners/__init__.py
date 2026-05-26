from __future__ import annotations

import os

from bench.runners.base import BaseRunner
from bench.runners.direct import DirectRunner
from bench.runners.subprocess_runner import SubprocessFrameworkRunner


if os.environ.get("BENCH_WORKER") == "1":
    from bench.runners.crewai_adaptive_consensus_debate_runner import CrewAIAdaptiveConsensusDebateRunner
    from bench.runners.crewai_critique_runner import CrewAICritiqueRunner
    from bench.runners.crewai_runner import CrewAIRunner
    from bench.runners.langgraph_adaptive_consensus_debate_runner import LangGraphAdaptiveConsensusDebateRunner
    from bench.runners.langgraph_critique_runner import LangGraphCritiqueRunner
    from bench.runners.langgraph_runner import LangGraphRunner
    from bench.runners.langgraph_selective_critique_runner import LangGraphSelectiveCritiqueRunner
    from bench.runners.maf_critique_runner import MAFCritiqueRunner
    from bench.runners.maf_adaptive_consensus_debate_runner import MAFAdaptiveConsensusDebateRunner
    from bench.runners.maf_runner import MAFRunner
    from bench.runners.maf_selective_critique_runner import MAFSelectiveCritiqueRunner
    from bench.runners.crewai_selective_critique_runner import CrewAISelectiveCritiqueRunner

    RUNNERS: dict[str, type[BaseRunner]] = {
        "direct": DirectRunner,
        "langgraph": LangGraphRunner,
        "langgraph_adaptive_consensus_debate": LangGraphAdaptiveConsensusDebateRunner,
        "langgraph_critique": LangGraphCritiqueRunner,
        "langgraph_selective_critique": LangGraphSelectiveCritiqueRunner,
        "crewai": CrewAIRunner,
        "crewai_adaptive_consensus_debate": CrewAIAdaptiveConsensusDebateRunner,
        "crewai_critique": CrewAICritiqueRunner,
        "crewai_selective_critique": CrewAISelectiveCritiqueRunner,
        "maf": MAFRunner,
        "maf_adaptive_consensus_debate": MAFAdaptiveConsensusDebateRunner,
        "maf_critique": MAFCritiqueRunner,
        "maf_selective_critique": MAFSelectiveCritiqueRunner,
    }
else:

    class LangGraphSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph"

    class LangGraphAdaptiveConsensusDebateSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph_adaptive_consensus_debate"

    class LangGraphCritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph_critique"

    class LangGraphSelectiveCritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "langgraph_selective_critique"

    class CrewAISubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai"

    class CrewAIAdaptiveConsensusDebateSubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai_adaptive_consensus_debate"

    class CrewAICritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai_critique"

    class CrewAISelectiveCritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "crewai_selective_critique"

    class MAFSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf"

    class MAFAdaptiveConsensusDebateSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf_adaptive_consensus_debate"

    class MAFCritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf_critique"

    class MAFSelectiveCritiqueSubprocessRunner(SubprocessFrameworkRunner):
        name = "maf_selective_critique"

    RUNNERS: dict[str, type[BaseRunner]] = {
        "direct": DirectRunner,
        "langgraph": LangGraphSubprocessRunner,
        "langgraph_adaptive_consensus_debate": LangGraphAdaptiveConsensusDebateSubprocessRunner,
        "langgraph_critique": LangGraphCritiqueSubprocessRunner,
        "langgraph_selective_critique": LangGraphSelectiveCritiqueSubprocessRunner,
        "crewai": CrewAISubprocessRunner,
        "crewai_adaptive_consensus_debate": CrewAIAdaptiveConsensusDebateSubprocessRunner,
        "crewai_critique": CrewAICritiqueSubprocessRunner,
        "crewai_selective_critique": CrewAISelectiveCritiqueSubprocessRunner,
        "maf": MAFSubprocessRunner,
        "maf_adaptive_consensus_debate": MAFAdaptiveConsensusDebateSubprocessRunner,
        "maf_critique": MAFCritiqueSubprocessRunner,
        "maf_selective_critique": MAFSelectiveCritiqueSubprocessRunner,
    }
