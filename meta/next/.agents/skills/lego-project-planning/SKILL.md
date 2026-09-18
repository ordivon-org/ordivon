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

If the real target, decision, state, mechanism, or evidence boundary is still unclear, use `lego-question-compiler` first. Do not turn unresolved questions into invented planning nodes.

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

## Optional analysis/theory routing

- `lego-question-compiler`: pre-planning or mid-analysis framing when the problem is vague, overloaded, solution-shaped, or insufficiently falsifiable. Its output is questions, not plan truth.

## Optional mature-theory lenses

Do not run every lens automatically. Activate only when the system shape justifies the extra analysis.

- `lego-systems-engineering`: unclear scope, environment, lifecycle, system-of-systems boundary, or interface ownership.
- `lego-dsm`: dense dependencies, cycles, repeated cross-module changes, unclear replacement seams, or suspected bad decomposition.
- `lego-feedback-control`: dynamic state, feedback, delay, observation, recovery, robustness, or regulation.
- `lego-stpa`: high-consequence loss/security risk, unsafe interactions, control actions, automation, humans/organizations, or failures not reducible to one broken component.
- `lego-regime-shift`: candidate turning point, stock/flow divergence, buffers/delays, constraint migration, reflexive adaptation, or a partly irreversible decision under deep uncertainty.
- `lego-compositional-contracts`: independently developed/replaceable components, assume-guarantee seams, local-to-global correctness, or substitutability questions.
- `lego-causal-intervention`: causal/mechanism claims, intervention decisions, confounding, ablation, identifiability, or observation-versus-cause ambiguity.
- `lego-fmea-fta`: explicit component/process failure modes, failure propagation, top undesired events, reliability barriers, recovery, or fault-injection planning.
- `lego-information-flow`: sensitive/untrusted information crossing prompts, credentials, logs, artifacts, telemetry, model/tool/provider boundaries, or declassification points.
- `lego-exploration-policy`: repeated uncertain choices, experiment/search budget allocation, adaptive routing, pure exploration, or exploration-exploitation trade-offs.
- `lego-ck-design`: open-ended invention where the desired object is not fully known and concepts/knowledge must expand together.
- `lego-evolutionary-search`: large/discrete/non-differentiable candidate populations, variation/selection, diversity, lineage, or bounded search under independent evaluation.
- `lego-organizational-cybernetics`: multi-agent/team autonomy, coordination, internal control, environment/future intelligence, policy/identity, recursion, or variety mismatch.

### Wave 3 routing guard

Do not stack the generative/search lenses by default.

- Desired object/concept is not yet known: prefer `lego-ck-design`.
- Known comparable options repeat under attributable feedback: consider `lego-exploration-policy`.
- Candidate representation + evaluator are already meaningful and population variation is the task: consider `lego-evolutionary-search`.
- Multi-agent/team autonomy, coordination, environment sensing or policy/identity is the task: use `lego-organizational-cybernetics`.

Bandit/evolutionary algorithms are not admitted merely because a search space exists. Exploration policy requires repeated comparable feedback; evolutionary search requires a trustworthy evaluator.

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
- docs/LEGO_QUESTION_COMPILER_R1.md
- docs/LEGO_THEORY_LAYER_R1.md
- schemas/project-lego-plan-r1.schema.json
- knowledge/lessons/agent-architecture-lego-catalog-r1.md for optional Agent-architecture coordinates
