# Langfuse vs Phoenix — AI Engineering Product-Layer Kernel

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**Langfuse and Phoenix productize the loop from AI execution traces to curated datasets, repeatable evaluation and controlled experiments; Langfuse emphasizes shared production AI-engineering operations, while Phoenix emphasizes a lighter developer/eval workbench with strong OpenInference alignment.**

## Core insight: OpenTelemetry does not make these products redundant

OpenTelemetry answers:

> How do I instrument, correlate and transport telemetry?

These products answer additional workflow questions:

> Which runs were bad?
> Which examples should become regression tests?
> Did candidate B improve over baseline A?
> Which evaluator produced this score?
> Which prompt/model/code version generated this result?
> What should humans review?

That is genuine product-layer value.

## Shared AI engineering loop

Both platforms broadly implement:

```text
PRODUCTION / DEVELOPMENT EXECUTION
          ↓
        TRACES
          ↓
   INSPECT / FIND FAILURES
          ↓
       DATASET
          ↓
 candidate implementation
          ↓
      EXPERIMENT
          ↓
      EVALUATORS
          ↓
 compare / review / decision
          ↓
        DEPLOY
```

This is the main reusable method kernel.

## Mechanism 1: production failures are valuable test cases

A strong AI application improvement loop does not maintain a synthetic benchmark disconnected from reality.

Useful pattern:

```text
production failure
  ↓ human/domain review
curated dataset example
  ↓
future candidate regression test
```

This gradually converts operational unknowns into reusable evaluation assets.

Do not automatically promote every trace into a dataset. Curate cases according to actual failure modes and domain importance.

## Mechanism 2: dataset is a test corpus, not telemetry storage

A dataset should be a deliberate set of examples used for comparison/evaluation.

Trace stores can contain millions of noisy production observations. The useful dataset is a much smaller, reviewed corpus containing representative and critical cases.

Keep the distinction:

```text
trace store
= what happened

dataset
= what we intentionally test against
```

## Mechanism 3: experiment comparison needs identities beyond score

A score alone is not reproducible evidence.

Bind:

```text
dataset version
candidate source/version
prompt version
model/config
retrieval/tool configuration when material
evaluator version
result/scores
```

For non-deterministic systems, repeated runs/variance may also matter.

This is where product experiment management can be valuable beyond raw traces.

## Mechanism 4: evaluators themselves require validation

LLM-as-a-judge is not a magical truth oracle.

Evaluate evaluators against:

- human-reviewed examples;
- known positive/negative controls;
- disagreement/failure analysis;
- judge model/prompt versions;
- robustness to output wording/order;
- domain-specific error severity.

Phoenix's automatic evaluator tracing and Langfuse's evaluator/score workflows are useful because they make evaluator behavior inspectable.

But domain/research methodology owns whether an evaluator is defensible.

## Mechanism 5: deterministic checks should remain deterministic

Do not use an LLM judge when a structural predicate can be checked exactly.

Examples:

```text
valid JSON       -> parser/schema
correct tool name -> exact/code evaluator
contains citation -> structural check
file exists      -> filesystem/provider check
```

Reserve LLM judges for genuinely semantic/subjective dimensions.

## Mechanism 6: online and offline eval are different

### Offline

Use fixed datasets before deployment to compare changes.

### Online

Score selected production traffic to detect drift/failures after deployment.

Do not confuse production monitoring with a controlled benchmark. Online samples expose reality; offline datasets support reproducible comparison.

A mature loop feeds important online failures back into offline datasets.

## Mechanism 7: prompt management is optional configuration authority

Remote prompt management is justified when prompts need:

- collaborative editing;
- labels/staged rollout;
- change history;
- performance comparison;
- no-code/low-code deployment.

Otherwise prompts may remain better owned by repository/code/Skills.

Do not create dual-authority prompt state.

## Mechanism 8: Langfuse vs Phoenix is mainly product/operations shape

### Langfuse

Best fit when the workload becomes a shared production AI-engineering platform:

- many users/apps;
- high trace volume;
- continuous monitoring;
- collaboration/annotation queues;
- shared prompt lifecycle;
- online/offline eval management;
- scalable analytics store;
- production dashboards/alerts.

Cost: heavier infrastructure and some enterprise-gated operational/governance features.

### Phoenix

Best fit when the workload is a developer/internal AI quality workbench:

- local trace debugging;
- OpenInference instrumentation;
- evaluator development;
- datasets/experiments;
- prompt replay/playground;
- one team/tenant;
- lightweight SQLite/PostgreSQL deployment.

Cost: ELv2 licensing constrains offering substantial Phoenix functionality as a third-party hosted service.

## Mechanism 9: do not deploy both by default

Feature overlap is high:

```text
tracing
scores/evals
datasets
experiments
prompt tooling
```

Operating two platforms fragments traces, datasets, scores and prompt identities.

Select one when a workload proves the need; maintain OTel/OTLP-compatible instrumentation so replacement remains possible.

## Mechanism 10: current Ordivon does not yet justify either

Current local Operations intentionally has no trace backend. Logs/metrics already have mature storage. No Langfuse/Phoenix installation exists.

Therefore installing either now would simultaneously introduce:

- a trace backend/product UI;
- AI datasets/eval platform;
- prompt/product state;
- new retention/privacy responsibility.

That should be triggered by a real AI quality/debugging workflow, not architecture completeness.

## Mechanism 11: first-use selection heuristic

If a real workload arrives today:

```text
Need quick local/internal Agent debugging + evals
        -> Phoenix first candidate

Need shared/team-scale production AI engineering,
collaboration, prompt lifecycle, continuous monitoring
        -> Langfuse first candidate
```

License can override the technical choice:

- Phoenix ELv2 is suitable for internal self-host but constrains third-party managed-service exposure;
- Langfuse core MIT is more permissive, while enterprise-only features require separate terms.

## Relationship to OpenTelemetry / OpenInference

Both should be treated as replaceable products above standards-native telemetry.

```text
Application
  ↓
OTel / OpenInference instrumentation
  ↓ OTLP
Langfuse OR Phoenix
```

Avoid platform-specific instrumentation when equivalent standard attributes exist.

## Relationship to Inspect AI / domain V&V

Neither platform replaces an evaluation methodology.

For research/model-agent benchmarks, Inspect AI or another dedicated harness may own scenario execution/scoring methodology, while Langfuse/Phoenix can optionally collect traces/experiment artifacts for inspection.

For domain tasks, the domain's acceptance criteria remain authoritative.

## What Ordivon should retain

1. Convert important production failures into curated regression examples.
2. Keep datasets distinct from raw trace stores.
3. Bind dataset/candidate/prompt/model/evaluator identities to experiment decisions.
4. Validate evaluators; do not trust judges merely because they return a number.
5. Use deterministic evaluators for deterministic properties.
6. Connect online monitoring to offline regression datasets.
7. Introduce remote prompt management only when it has a clear authority/use-case.
8. Choose one AI engineering product for a proven workload rather than deploying overlapping platforms.
9. Keep instrumentation standards-native to preserve backend replaceability.
10. Treat platform scores/traces as evidence, not domain truth.

## What Ordivon should not copy

- another trace UI/store;
- private datasets/experiment database;
- custom prompt-management platform;
- bespoke LLM-as-judge scheduler;
- annotation queue infrastructure;
- AI-specific dashboarding/analytics engine;
- duplicate deployment of both Langfuse and Phoenix without distinct measured workloads;
- eval score as semantic completion truth.

## Prototype readiness gate

### One-sentence test

PASS: both platforms turn AI traces into reusable evaluation/experiment workflows; Langfuse is the heavier shared production platform, Phoenix the lighter developer/eval workbench.

### Prototype test

PASS: trace -> curate dataset -> run two candidates -> apply evaluators -> compare regression -> inspect failing trace is sufficient to reproduce the core product loop.

## Verdict

**PASS — KEEP BOTH AS ALTERNATIVE ON-DEMAND PRODUCTS; DEPLOY NEITHER UNTIL A REAL TRACE/EVAL WORKLOAD EXISTS. PHOENIX IS THE LIGHTER FIRST INTERNAL CANDIDATE; LANGFUSE IS THE STRONGER SHARED PRODUCTION PLATFORM CANDIDATE.**
