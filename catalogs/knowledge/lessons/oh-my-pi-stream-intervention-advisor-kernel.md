# Oh My Pi Stream Intervention + Advisor Kernel — extracted experimental design

Status: **REGISTERED / EXPERIMENTAL / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Keep corrective/reviewer cognition outside the primary prompt until evidence says it is needed, then inject a provenance-visible intervention without granting the sidecar hidden execution authority.**

## Why this is experimental

Unlike LSP, DAP or MCP, there is no settled industry standard for:

- mid-stream rule intervention;
- independent advisor/watchdog models;
- when reviewer context should become primary cognition;
- whether intervention improves outcomes enough to justify extra model calls and control complexity.

OMP provides two useful mechanisms to study:

1. **TTSR-like stream rules** — pattern triggers during streaming, interrupt/retry with a corrective rule;
2. **Advisor/watchdog** — a second model reviews the primary trajectory and can inject advice.

Ordivon should preserve these as experimental Harness mechanisms, not core laws.

# Part A — stream intervention

## Problem

Some rules are important only when the Agent enters a known failure pattern. Permanently injecting them into every prompt wastes tokens and may distract reasoning.

Desired model:

```text
primary stream
   -> detector sees trigger
   -> abort/stop current generation at controlled boundary
   -> persist intervention event
   -> add corrective rule to current control/cognition state
   -> retry/resume according to provider semantics
```

## Minimum data model

```ts
type StreamRule = {
  ruleId: string;
  pattern: string;             // regex or deterministic detector id
  reminder: string;
  maxTriggersPerRun: number;
  persistence: "attempt" | "run";
};

type InterventionEvent = {
  interventionId: string;
  runId: string;
  ruleId: string;
  sourceAttemptId: string;
  matchedDigest: string;
  timestamp: string;
  action: "abort_and_retry";
};
```

Do not persist private chain-of-thought content merely to record why a rule fired; store bounded trigger metadata and allowed output fragments/digests.

## Stream-rule flow

```text
1. Turn begins with active rule detector set but reminders absent from prompt.
2. Provider stream emits allowed visible/tool-call data.
3. Deterministic detector matches rule.
4. Harness requests provider-stream cancellation.
5. Persist intervention event before new retry authority.
6. Add reminder to explicit current control/cognition projection.
7. Start a new Provider attempt under the same logical Agent turn or a clearly linked successor attempt.
8. Prevent unbounded loops with per-rule/run trigger limits.
```

The exact retry identity must remain inspectable. Do not pretend the interrupted and replacement Provider calls are one physical Provider call.

## Compaction interaction

If a triggered rule is meant to survive compaction, store its activation as explicit Run control/cognition state. Do not rely on the reminder text remaining somewhere in old transcript history.

This follows Ordivon's `History != Cognition` law.

## Failure modes

- trigger false positive;
- repeated intervention loop;
- provider cannot cleanly abort stream;
- effectful Tool call already emitted before trigger;
- partial assistant output incorrectly replayed as complete;
- compaction drops active intervention state.

Rule: **stream intervention can modify future cognition; it cannot erase an already-admitted Tool effect.**

# Part B — advisor/watchdog

## Problem

A primary executor may miss architectural constraints, regressions or evidence gaps. A reviewer with independent context can inspect periodically without occupying every primary-token position.

## Minimum advisor contract

```ts
type AdvisorRequest = {
  runId: string;
  transcriptProjectionRef: string;
  workspaceRef?: string;
  reviewPolicyRef: string;
};

type AdvisorResult = {
  advisorAttemptId: string;
  severity: "note" | "warning" | "blocker";
  message: string;
  evidenceRefs: string[];
};
```

Advisor output is **observation/cognition input**, not authority.

## Default Tool policy

Start read-only:

- source read/search;
- Runtime/Workspace projections;
- diagnostics/tests already produced;
- explicit `advise` yield.

Do not grant mutation/execution by default. If a future advisor can mutate, it should become a normal separately authorized Harness Run, not a magical sidecar exemption.

## Advisor scheduling

Candidate policies:

- after every N turns;
- after source mutation;
- before completion proposal;
- when verification fails;
- when stagnation/repetition detector fires.

This is an experimental policy surface. Benchmark rather than canonize one schedule.

## Injection policy

Advisor result may be:

- injected immediately into next primary turn;
- stored as optional current cognition;
- escalated to caller/domain when severity is blocker.

The primary Agent is not automatically forced to accept advisor semantics, unless a higher-level Host/Domain policy explicitly treats a finding as a gate.

## Separation from independent verification

Advisor != verifier.

An advisor saying “tests likely pass” is not a test result. Independent V&V uses actual build/test/domain evidence under the relevant owner.

## Minimum prototype

### Stream rules

- one deterministic regex trigger;
- provider streaming mock or supported real streaming provider;
- abort + linked retry;
- explicit intervention event;
- loop cap;
- context reconstruction proving activated rule survives compaction simulation.

### Advisor

- second model call after source mutation;
- read-only Workspace context;
- structured `{severity,message,evidenceRefs}`;
- inject into next primary context as labeled advisor observation;
- no direct Tool execution.

## Acceptance experiment

Use paired tasks with mechanism on/off.

Measure:

- task/test success;
- primary model tokens;
- sidecar model tokens;
- correction latency;
- false intervention rate;
- number of duplicate/aborted Provider calls;
- effect safety violations;
- whether advisor findings lead to independently verified improvement.

Promote only when benefit survives ablation and does not create hidden authority.

## Mandatory falsifiers

1. Rule fires after a Tool effect was already admitted: system must not erase/repeat effect.
2. Same rule fires repeatedly: loop cap stops recurrence.
3. Compaction occurs after intervention: active rule remains explicit if configured Run-persistent.
4. Advisor hallucinates a defect: no mutation/Task failure occurs solely from unsupported advice.
5. Advisor process/model fails: primary Run continues unless caller policy explicitly requires advisor gate.

## Project-study acceptance

### One-sentence test

PASS: OMP demonstrates plausible ways to keep corrective cognition off the hot prompt path until needed, but the optimal policy is not settled.

### Prototype test

PASS: a provenance-visible stream rule and a read-only advisor can be prototyped without changing Runtime authority or silently granting sidecars execution rights.

## Verdict

**PASS AS EXPERIMENTAL DONOR — PROTOTYPE AND ABLATE; DO NOT PROMOTE TO CORE WITHOUT MEASURED VALUE.**
