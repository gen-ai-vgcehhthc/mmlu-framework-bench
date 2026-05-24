# MMLU-Pro Framework Bench Summary

| Framework | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| crewai | 50 | 76.0% | 1 | 2 | 18.90s | 12.06s | 44.19s |
| crewai_debate | 50 | 54.0% | 15 | 1 | 79.70s | 31.13s | 186.75s |
| direct | 50 | 82.0% | 0 | 1 | 10.24s | 6.09s | 27.91s |
| langgraph | 50 | 88.0% | 0 | 1 | 12.47s | 7.79s | 38.56s |
| langgraph_debate | 50 | 68.0% | 0 | 5 | 18.84s | 14.90s | 31.82s |
| maf | 50 | 80.0% | 1 | 4 | 15.31s | 7.36s | 51.65s |
| maf_debate | 50 | 0.0% | 50 | 0 | 181.27s | 181.09s | 182.65s |

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
