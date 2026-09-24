# Standard / Provider: OpenInference

Status: **ON-DEMAND AI OBSERVABILITY CONVENTION + INSTRUMENTATION ECOSYSTEM**
Role: OpenTelemetry-compatible AI/LLM/Agent tracing conventions and instrumentation, used when its richer current ecosystem is useful.

## One-sentence understanding

**OpenInference adds AI-application-specific span kinds, structured prompt/model/tool/retrieval attributes, evaluation annotations and privacy controls on top of OpenTelemetry/OTLP so AI traces can be interpreted consistently by compatible observability backends.**

## Current relationship to OpenTelemetry

OpenInference is built on OpenTelemetry. Every OpenInference trace is valid OTLP telemetry; OpenInference adds AI-specific semantic meaning.

However, OpenTelemetry now also maintains a dedicated **GenAI Semantic Conventions** project covering model, Agent, retrieval, MCP and provider-specific telemetry. That OTel GenAI work is currently marked **Development** and evolves quickly.

Therefore Ordivon should not declare OpenInference the permanent universal AI telemetry ontology.

Preferred rule:

```text
OpenTelemetry core + OTLP
        ↓ canonical telemetry substrate
OTel GenAI conventions when supported/useful
        ↓
OpenInference when its instrumentors/richer conventions/backend compatibility
materially improve the workload
```

Keep translation/mapping at instrumentation/export boundaries rather than persisting either convention as domain truth.

## OpenInference span kinds

OpenInference adds semantic role classification such as:

- `LLM`;
- `AGENT`;
- `CHAIN`;
- `TOOL`;
- `RETRIEVER`;
- `RERANKER`;
- `EMBEDDING`;
- `GUARDRAIL`;
- `EVALUATOR`;
- `PROMPT`.

These are **AI operation roles**.

Do not confuse them with OpenTelemetry's native `SpanKind` axis (`CLIENT`, `SERVER`, `PRODUCER`, `CONSUMER`, `INTERNAL`), which describes process/network interaction relationships.

Both axes can coexist.

## Structured AI attributes

OpenInference can capture details such as:

- input/output values;
- input/output MIME types;
- model/provider identity;
- invocation parameters;
- messages/prompts/completions;
- token usage;
- tool definitions/calls/results;
- retrieval documents/scores;
- embedding details;
- prompt templates;
- metadata/session/user/tags;
- human/LLM/code evaluation annotations.

These fields are observability projections. They must not become Ordivon's source of truth for prompts, messages, evaluation datasets or research evidence.

## Privacy boundary

AI telemetry can be substantially more sensitive than ordinary service telemetry because traces may contain complete prompts, responses, images, tool arguments, documents and user data.

OpenInference provides explicit configuration controls to hide/redact classes of content, including inputs, outputs, messages, tool definitions, invocation parameters, images and embedding text/vectors.

Default Ordivon posture should be:

- capture identities, timing, status, model/tool names and bounded usage metadata by default;
- capture raw content only when a concrete debugging/evaluation requirement justifies it;
- redact before export across trust boundaries;
- never place secrets/provider keys in telemetry;
- keep retention purpose-specific.

## Evaluation boundary

OpenInference supports telemetry annotations/evaluations associated with spans/traces/sessions.

This is useful for carrying evaluator results such as relevance/quality/safety scores.

It does **not** define which evaluator is scientifically/business-valid for a task. Evaluation methodology remains with the domain/eval platform.

## Instrumentation ecosystem

OpenInference's practical value includes maintained instrumentation for popular AI SDKs/frameworks and compatibility with OpenTelemetry exporters/backends.

Use an existing instrumentor when it produces useful, inspectable telemetry instead of hand-instrumenting every framework call.

Do not keep an instrumentation package merely because it exists; prefer provider/framework-native OTel GenAI instrumentation when mature and sufficient.

## Conversion / compatibility

OpenInference provides compatibility helpers that can map some OpenTelemetry GenAI attributes into OpenInference attributes. This is useful during ecosystem transition.

Because OTel GenAI conventions are currently moving quickly, keep conversion versioned and testable. Do not mutate long-lived stored telemetry in place without a migration plan.

## Ordivon routing rule

Use OpenInference when at least one is true:

- the selected AI framework has strong maintained OpenInference instrumentation;
- the selected backend expects/renders OpenInference semantics well;
- current OTel GenAI coverage lacks a needed AI trace role/annotation;
- evaluation/annotation interoperability benefits from OpenInference.

Otherwise prefer standard OpenTelemetry/OTel GenAI instrumentation directly.

## Prototype recipe

A minimal proof requires:

1. create an OTel trace for one Agent turn;
2. classify child spans as `AGENT`, `LLM`, `TOOL`, `RETRIEVER` using OpenInference attributes;
3. attach model/token/tool/retrieval metadata;
4. hide raw prompt/output content via privacy configuration;
5. export the same trace through ordinary OTLP;
6. inspect it in an OTel-compatible backend.

The architecture is proven once no proprietary transport/storage is required.

## Prototype readiness gate

**PASS.** OpenInference's role as an OTel-compatible AI semantic/instrumentation layer, and its privacy/evaluation boundaries, are explicit enough to use it selectively without making it an Ordivon-native ontology.
