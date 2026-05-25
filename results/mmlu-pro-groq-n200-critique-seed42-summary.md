# MMLU-Pro Framework Bench Summary

| Framework | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 | Prompt Tokens | Completion Tokens | Total Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crewai | 200 | 35.5% | 0 | 0 | 7.05s | 6.92s | 7.95s | 51,541 | 400 | 51,941 |
| crewai_adaptive_consensus_debate | 200 | 37.5% | 0 | 0 | 7.14s | 7.08s | 7.88s | 124,452 | 1,081 | 125,533 |
| crewai_critique | 200 | 36.0% | 0 | 0 | 7.64s | 7.56s | 8.36s | 356,236 | 32,427 | 388,663 |
| direct | 200 | 35.5% | 0 | 0 | 0.45s | 0.24s | 1.42s | 51,541 | 400 | 51,941 |
| langgraph | 200 | 35.5% | 0 | 0 | 1.97s | 1.94s | 2.37s | 51,541 | 400 | 51,941 |
| langgraph_adaptive_consensus_debate | 200 | 37.5% | 0 | 0 | 2.25s | 1.84s | 3.99s | 124,452 | 1,119 | 125,571 |
| langgraph_critique | 200 | 36.0% | 0 | 0 | 4.62s | 3.07s | 12.09s | 356,243 | 32,435 | 388,678 |
| maf | 200 | 35.5% | 0 | 0 | 1.37s | 1.19s | 3.29s | 51,541 | 400 | 51,941 |
| maf_adaptive_consensus_debate | 200 | 37.5% | 0 | 0 | 1.62s | 1.22s | 3.43s | 124,452 | 1,081 | 125,533 |
| maf_critique | 200 | 36.0% | 0 | 0 | 3.00s | 2.72s | 5.93s | 356,248 | 32,440 | 388,688 |

## Framework Scorecard

| Area | LangGraph | CrewAI | MAF |
|---|---|---|---|
| Runtime & efficiency | Fine-grained graph control; good for explicit parallel branches and retries. | Higher-level orchestration; convenient but heavier runtime surface. | Workflow-first model with async functional workflows and checkpointing. |
| Cost control | Easy to centralize model calls and add budget gates per node. | Cost depends on crew/task design; hidden extra planner/manager calls can matter. | Step boundaries make expensive calls explicit; good place for budgets/retries. |
| Parallel processing | Strong graph fan-out/fan-in patterns. | Flows and crews support structured work, but less transparent for micro-benchmarks. | Native async workflows make parallelism direct with `asyncio.gather`. |
| Control flow & determinism | Best fit for deterministic state machines. | Best fit for role/task collaboration, less ideal when every edge must be explicit. | Strong workflow control; API is newer and still moving. |
| State & memory | Checkpointers/stores are mature and explicit. | Built-in memory features are convenient, with more framework policy. | Checkpointing is a first-class production concern. |
| Multi-agent topology | Supervisor/swarm/graph topologies are flexible. | Natural crew/team mental model. | Sequential, concurrent, handoff, and group workflow patterns. |
| Developer experience | More code, more control. | Fastest conceptual start for role-based tasks. | Clean production story, but newest API among the three. |
| Observability & debug | LangSmith ecosystem, node-level traces. | Observability integrations exist; abstractions can hide calls. | OpenTelemetry-oriented production debugging. |
| Tool calling | Strong via LangChain/LangGraph tool ecosystem. | Tool API is central to agents/tasks. | Supports agent skills/tools, Microsoft ecosystem leaning. |
| Human approval | Interrupts/checkpointing fit approval gates. | Human feedback features in flows/tasks. | HITL is part of workflow context patterns. |
| Commercial support | LangChain/LangSmith/LangGraph platform. | CrewAI platform and enterprise offering. | Microsoft-backed, Azure/Foundry/GitHub Copilot alignment. |
| Cloud deployment | LangGraph Platform or self-host. | CrewAI Enterprise/AMP or self-host. | Azure/Foundry and local/cloud workflow hosting patterns. |
