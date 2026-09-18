# LEGO Project Planning R1

Date: 2026-09-18
Status: ACTIVE CONTRACT R1

## Purpose

LEGO Project Planning turns verified project architecture into a small, replaceable, evidence-bound implementation plan.

It is not a project authority, workflow engine, roadmap database, or ontology. The project repository, native standards, code, tests, evidence, and external owners remain authoritative.

The canonical project projection is planning/lego-plan-r1.json and its truth role is always planning-projection-not-project-truth.

## Core flow

understand evidence
→ identify responsibilities
→ split into replaceable LEGO nodes
→ type important edges
→ bind current evidence
→ define the next bounded vertical slice
→ implement
→ verify independently
→ update the plan projection

A planning node never becomes true because it appears in the plan.

## Two-layer model

Shared architecture LEGO may optionally reference knowledge/lessons/agent-architecture-lego-catalog-r1.md and knowledge/graphs/agent-architecture-lego-catalog-r1.json.

Projects are never forced into Core-24. Each project keeps its own domain vocabulary.

Examples:
- Game may use product, mechanic, composition, experiment, and evidence nodes.
- Research may use study routing, method binding, workflow, evidence, and verification nodes.
- Runtime may use Workspace, Job, Attempt, execution ownership, and observation nodes.
- Security may use subject binding, provider evidence, policy decision, and standing projection nodes.

A project-native node is preferred over a misleading shared mapping.

## Plan contract

A plan records project purpose, source evidence, nodes, edges, bounded implementation slices, known gaps, explicit do-not-own boundaries, and review/source revision.

Node states are DISCOVERED, DESIGNED, IMPLEMENTING, IMPLEMENTED, VERIFIED, DEFERRED, and REJECTED.

Rules:
- DISCOVERED means source evidence shows the responsibility exists.
- DESIGNED means authority and replacement boundary are sufficiently clear to implement.
- IMPLEMENTING means admitted current work exists.
- IMPLEMENTED requires implementation evidence.
- VERIFIED requires independent acceptance evidence.
- DEFERRED is intentionally inactive now.
- REJECTED preserves an explicit non-target decision.

The plan does not infer runtime or current-work truth from these labels.

## Node fields

Keep nodes small: id, label, kind, responsibility, authority, state, sharedRefs, evidence, dependencies, replacementContract, mustNotOwn, acceptance, and optional nextAction.

Do not fill optional fields merely for completeness.

## Edge types

Recommended types are DATA, CONTROL, EFFECT, IDENTITY, POLICY, OBSERVATION, EVIDENCE, and DEPENDENCY. Project-native edge types are allowed when the domain genuinely needs another distinction.

## Vertical slices

A slice is the planning unit. It must produce an observable improvement or proof.

Each slice has objective, status, nodeIds, acceptance, evidence, blockers, and optional nextAction.

Prefer one to three ACTIVE slices. Do not turn the plan into a giant backlog. COMPLETE requires evidence.

## Atomicity gate

Split a candidate node when it mixes materially different authorities, such as durable truth, policy choice, external effects, desired/observed reconciliation, semantic verification, and UI/read projections.

Do not split implementation details that have no independent authority, replacement, or acceptance boundary.

## Evidence discipline

IMPLEMENTED and VERIFIED require evidence references. Evidence paths are navigation references; path existence alone does not prove semantic sufficiency or currentness.

## Mandatory non-equivalences

plan state != runtime state
plan node != source authority
plan COMPLETE != domain success
shared LEGO ref != implementation ownership
diagram edge != permission
roadmap priority != execution admission

## Update law

Update the LEGO plan only when architecture-relevant facts change: responsibility/authority shifts, implementation/verification standing changes, slices are admitted or completed, mature external substrates replace local machinery, evidence disproves the decomposition, or a new failure mode forces an Atomicity split.

Ordinary code churn does not require a planning update.

## Adoption law

A project adopts R1 by adding planning/lego-plan-r1.json. It does not copy this contract, schema, validator, catalog, or a global workflow engine.

## Validation

Run:
python3 scripts/check_project_lego_plan_r1.py /path/to/project/planning/lego-plan-r1.json

Validation proves structural consistency only. It does not prove architecture correctness or project completion.
