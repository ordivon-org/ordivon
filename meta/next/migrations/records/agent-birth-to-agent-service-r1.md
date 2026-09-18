# Agent Birth -> Agent Service migration proposal R1

Status: **PROPOSED / NOT YET CUT OVER**
Registered: 2026-09-17

## Historical standing

Current Ordivon classification/migration material records Agent Birth as an Agent provisioning/orchestration enabling capability associated with the retained Harness semantic core and its historical execution/provisioning responsibilities.

That historical record remains valid evidence of the previous architecture and is not rewritten in place.

## New target boundary

The Agent Service decomposition wave proposes splitting the historical Harness responsibility:

```text
Agent Service owns
- Agent definition/revision identity
- Agent Birth request/lifecycle
- first-class Agent identity binding
- capability/plugin profile binding
- desired placement / retirement
- cluster reconciliation

Harness owns
- context/model loop
- skill disclosure
- tool selection
- subagent delegation inside the loop
- cognitive termination/replanning

Host owns
- local continuity/presence/wake/re-entry

Runtime owns
- physical execution and Job/Attempt/Artifact evidence
```

## Why move Birth upward

External Agent Service architectures consistently place agent definition/version/deployment/identity/lifecycle above the execution runtime/harness. Birth is therefore better modeled as a Service provisioning protocol whose implementation may invoke Host and Runtime providers rather than as a model-loop responsibility.

## Cut-over gate

Do not retire the historical Birth ownership until a real vertical slice proves:

1. immutable Agent revision identity;
2. identity/capability binding;
3. durable desired placement before provider effects;
4. reconciliation after Service restart;
5. Host/Runtime evidence mapped without identity collapse;
6. retirement/re-provisioning without duplicate semantic Agent identity;
7. at least one real workload uses the new path.

Until then, this record is a target migration contract, not production authority.
