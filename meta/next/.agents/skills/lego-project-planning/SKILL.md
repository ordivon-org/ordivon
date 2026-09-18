---
name: lego-project-planning
description: Convert an already-understood software, research, game, infrastructure, or capability project into an evidence-bound LEGO implementation plan with small replaceable nodes, typed relationships, bounded vertical slices, explicit authority boundaries, and verification criteria. Use after project facts are known, when planning, restructuring, sequencing work, or updating architecture implementation standing. Do not use the plan as a substitute for codebase discovery or domain truth.
compatibility: Cross-platform. Project plans use planning/lego-plan-r1.json.
metadata:
  source-authority: ordivon-next
  planning-contract: docs/LEGO_PROJECT_PLANNING_R1.md
  theory-layer: docs/LEGO_THEORY_LAYER_R1.md
  schema: schemas/project-lego-plan-r1.schema.json
---

# LEGO Project Planning

The LEGO plan is a planning projection, not project truth.

## Workflow

1. Read project-native authority first: README, architecture/ownership docs, source, tests, and current evidence.
2. State the one-sentence project outcome and do-not-own boundary.
3. Identify project-native responsibilities before looking at shared LEGO catalogs.
4. Split nodes until each has one primary responsibility/authority/effect boundary and an independently testable seam where meaningful.
5. Add sharedRefs only when an external coordinate matches exactly. A shared ref is not inheritance or authority.
6. Bind evidence. IMPLEMENTED and VERIFIED nodes require evidence.
7. Add only important typed edges.
8. Choose a bounded vertical slice with observable acceptance. Prefer one to three ACTIVE slices.
9. Record gaps and do-not-own boundaries.
10. Validate structure when the R1 validator is available.
11. After implementation, re-read reality before updating node state.

## Optional mature-theory lenses

Do not run every lens automatically. Activate only when the system shape justifies the extra analysis.

- `lego-systems-engineering`: unclear scope, environment, lifecycle, system-of-systems boundary, or interface ownership.
- `lego-dsm`: dense dependencies, cycles, repeated cross-module changes, unclear replacement seams, or suspected bad decomposition.
- `lego-feedback-control`: dynamic state, feedback, delay, observation, recovery, robustness, or regulation.
- `lego-stpa`: high-consequence loss/security risk, unsafe interactions, control actions, automation, humans/organizations, or failures not reducible to one broken component.

Lens outputs are derived analysis evidence. They alter the plan only through an explicit architecture decision supported by project-native evidence.

Do not expand the project plan schema merely to mirror theory vocabulary.

## State law

DISCOVERED → DESIGNED → IMPLEMENTING → IMPLEMENTED → VERIFIED
Side states: DEFERRED and REJECTED.

IMPLEMENTED is not allowed without evidence. VERIFIED also requires acceptance criteria.

## Domain rule

Do not force a universal ontology.

Runtime may map to shared execution LEGO. Agent Service may map to Task/Session/Service LEGO. Artifact may map to Version/Observation. Game should retain game-native mechanics/products/experiments. Research should retain method/protocol/evidence nodes. Security should retain subject/evidence/policy/standing nodes.

If a shared mapping distorts natural authority, omit it.

## Quality gate

Another Agent should be able to answer from the plan:
- what outcome the project owns;
- which small nodes compose it;
- which node owns each important truth or effect;
- what is implemented versus merely designed;
- what the next bounded slice is;
- what evidence will prove it;
- what the project explicitly refuses to own.

Canonical references:
- docs/LEGO_PROJECT_PLANNING_R1.md
- docs/LEGO_THEORY_LAYER_R1.md
- schemas/project-lego-plan-r1.schema.json
- knowledge/lessons/agent-architecture-lego-catalog-r1.md for optional Agent-architecture coordinates
