# MMLU-Pro Framework Bench Summary

| Framework | N | Accuracy | Errors | Parse Failures | Avg Latency | Median | P95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| crewai | 10 | 70.0% | 0 | 2 | 12.04s | 10.59s | 18.69s |
| direct | 10 | 90.0% | 0 | 0 | 6.84s | 5.61s | 12.33s |
| langgraph | 10 | 70.0% | 0 | 2 | 9.50s | 7.31s | 20.75s |
| maf | 10 | 80.0% | 0 | 0 | 8.80s | 6.31s | 19.88s |

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
