# Provider: Microsoft Agent Framework

- Upstream: `microsoft/agent-framework`
- Installed version: `agent-framework==1.18.0`
- Role: multi-agent orchestration provider
- Migration mode: external replaceable library/provider
- Local standing: mechanics accepted; real ChatGPT participant integration pending

## Capabilities

Sequential orchestration, concurrent fan-out/fan-in, handoff, group collaboration, checkpoint/restart patterns, human-in-the-loop, multi-provider agent abstraction, observability, and MCP/A2A integration direction.

## Boundary

MAF owns one agentic workflow/run and its orchestration state. It does not own Plane work-item truth, Temporal macro-process truth, Runtime execution truth or domain semantic acceptance.

Use MAF first for standard multi-agent collaboration patterns such as sequential/concurrent fan-out, handoff and group collaboration. Use LangGraph instead when the application requires a bespoke checkpointed Agent state machine with explicit reducers, cycles, dynamic interrupts or checkpoint forking/time-travel. Do not maintain equivalent orchestration state in both frameworks.

## Local acceptance

Environment:
`/root/.local/share/ordivon/agent-framework-1.18.0/.venv`

Python 3.12.13. A deterministic `ConcurrentBuilder` run executed participants `A01` and `A02`, observed `A01:probe` and `A02:probe`, and completed framework fan-in.

## Current integration gap

Agent Automation can birth and continue ChatGPT occurrences but does not yet expose an accepted assistant-output observation/retrieval operation; submit evidence records `assistantOutputRead=false`. A minimal provider-result observer plus MAF participant adapter remains required.
