# Ordivon Model Foundry Knowledge Catalog R2

Status: **NON-AUTHORITATIVE KNOWLEDGE CATALOG**

This directory preserves reusable model/composition knowledge without creating a model runtime, provider registry, planner, scheduler, permission system, deployment authority, or scientific truth owner.

## Core distinction

```text
Cognitive Operator
  != Logical Architecture
  != Model / Checkpoint
  != Provider Binding
  != Serving / Physical Plan
  != Qualification Evidence
```

A logical responsibility may be physically fused with another responsibility, may share a backbone/state/cache, or may execute as an independent specialist. Logical separation therefore does not imply process separation.

## R2 laws

1. **Workload first.** No globally best model family is assumed.
2. **DELETE-CUSTOM-BY-DEFAULT.** Prefer mature external implementations and standards before custom model training.
3. **Evidence is bounded.** A benchmark claim travels with task population, checkpoint, representation, calibration, hardware/runtime, candidate cardinality, context range and measurement boundary.
4. **Confidence is not authority.** Calibration can support selective cognition; it cannot authorize effects or establish domain completion.
5. **Provider diversity is not failure diversity.** Complementarity must be measured on aligned item-level outcomes.
6. **Memory is typed state placement.** Parametric weights, context, KV cache, recurrent latent state, retrieval stores, structured databases and evidence refs are different contracts.
7. **Routing is separately qualified.** Candidate-set quality, oracle gap, capable-model recall and drift are measured before sophisticated routing is promoted.
8. **Composition has multiple planes.** Parameter composition, neural-graph composition and system composition have different compatibility/failure modes.
9. **Logical contracts survive provider replacement.** Physical substitution is valid only inside a current qualification envelope.
10. **AUTHORIZE / EXECUTE / WITNESS / COMMIT are not model operators.** Their natural owners remain outside Model Foundry knowledge.

## Cognitive operator vocabulary

The initial vocabulary is deliberately small and semantic: `PERCEIVE`, `PARSE`, `EMBED`, `RETRIEVE`, `RANK`, `FILTER`, `DECIDE`, `ESTIMATE`, `VERIFY`, `ROUTE`, `ABSTAIN`, `PLAN`, `GENERATE`, `COMPRESS`, `MEMORY_READ`, `MEMORY_WRITE`, `SIMULATE`, `CRITIQUE`, `SYNTHESIZE`.

These are catalog terms, not package/service identities. A consumer may use only the subset justified by its concrete circuit.

## Decision-model example

`DECIDE` is intentionally not synonymous with Jev, Laya, a classifier, or an LLM. Current public implementations span proprietary typed deciders, bidirectional setwise encoders, causal-logit/pointer readouts, dual-encoder/contrastive compatibility models, dynamic-label encoders and deterministic rules.

The catalog therefore stores providers as replaceable physical realizations plus evidence, never as cognitive identity.

## Relationship to current Ordivon architecture

- `packages/composition` remains the owner of generic deterministic task-local Cognitive Circuit / Composition Gate / compatibility mechanics. It does **not** own Model Foundry provider discovery or ranking.
- `catalogs/knowledge` stores this reusable non-authoritative mapping.
- Runtime/Host/Harness/domain owners remain unchanged.
- A future compiler/provider optimizer requires a concrete consumer and separate owner decision; this catalog alone does not create one.

## R1 provenance

The historical R1 work remains at Git revision `eb9755d7a282d8158fd0c714885a7ab17ce9975c` on the retained research line `research/model-foundry-knowledge-r1-20260924`. R2 migrates durable concepts, not the old branch topology. See the migration receipt under `docs/migration/receipts/`.
