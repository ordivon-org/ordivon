# M2 single-Agent Host design

## Claim

M2 adds one persistent Engineer Agent above the M1.5 world boundary. Codex, Hermes, and fixtures are replaceable cognition providers; no provider session owns Agent identity or task continuity.

## Execution shape

```text
Goal / Task / Attempt
→ bounded persisted Context
→ replaceable Provider Decision
→ exact Operation admission
→ deterministic Skill
→ Effect / Dispatch
→ World Command
→ Observation / Verification / Fact
→ durable continuation
```

## State ownership

| State | Authority |
|---|---|
| map, resources, health, mission result | World Kernel |
| Goal, Task, Attempt, Context, Decision | Game Host |
| raw model output and usage | immutable Artifact |
| concrete world transition | World Kernel |
| completed action claim | Verification over World Facts |

## Provider boundary

Codex runs ephemerally with read-only sandboxing and JSON Schema output. Hermes runs with invocation-scoped `HOME` and `HERMES_HOME`, no tools, MCP, rules, memory, skills, or retained session. Both consume the same canonical Context and return one exact admitted Operation identity.

## Decision cadence

Models choose strategic Operations such as repair cooling, restore life support, seal the breach, stabilize the casualty, or send distress. The Host expands one Operation into deterministic movement, pickup, and world-action steps. Routine execution does not require another model call.

## Recovery order

A fresh Host verifies its journal, rereads the world, reconciles unresolved Dispatches, continues a recorded Attempt, and calls a Provider only when no deterministic progress remains. Replay never calls a model.

## Scope boundary

M2 keeps one Engineer, one active root Task, and one Intent per world Tick. Multi-Agent conflict, authority approval, hidden observations, and organizational behavior remain M3.
