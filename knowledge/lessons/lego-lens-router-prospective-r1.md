# LEGO Lens Router — Prospective Validation R1

Date: 2026-09-18
Status: PROSPECTIVE VALIDATION COMPLETE / R1

## Purpose

Test whether the Lens Router can reduce theory sprawl while preserving the lenses that materially changed prior decisions.

The comparison is not against a numerical optimum. It asks:

- can the router choose fewer lenses than the whole catalog?
- does each selected lens own a distinct decision question?
- are rejected lenses rejected for explicit prerequisites/overlap/domain-owner reasons?
- can the router return NO_LENS?
- can a validated composite profile prevent redundant stacking of its component lenses?

## Case 1 — Runtime reconciliation feedback

Prior evidence:
- knowledge/lessons/lego-wave1-prospective-validation-r1.md
- Runtime correction integrated at cf0e0adf118d4f143fd7117d6a9592343261d8e0

Decision:
Does the Runtime planning graph represent the control loop needed for recovery/reconciliation correctly?

Problem signature:
- dynamic state: yes;
- feedback/reconciliation: yes;
- high-consequence safety claim: not required for this bounded graph correction;
- component failure tree: not required;
- causal intervention: not required;
- information boundary: no.

Router result:

Selected MSTS:
1. feedback-control

Rejected:
- STPA: no unacceptable-loss/control-safety decision was needed to detect the missing return edge;
- FMEA/FTA: no explicit failure-mode/top-event analysis was required;
- Systems Engineering: system boundary was already explicit;
- DSM: graph was sparse and decomposition was not disputed.

Result:
- PASS — 1 lens preserved the actual model correction.

## Case 2 — Harness provider replacement

Prior evidence:
- knowledge/lessons/lego-wave2-prospective-validation-r1.md
- Harness correction integrated at e29def339995c20ed4f0022d502b557d13a4359d

Decision:
Can a second Harness provider replace the first without silently strengthening environment/authority assumptions or weakening guarantees?

Problem signature:
- replacement/substitutability: yes;
- components and required guarantees: explicit;
- dynamic regulation: secondary;
- causal claim: no;
- information visibility: no.

Router result:

Selected MSTS:
1. compositional-contracts

Rejected:
- Systems Engineering: broad system boundary was not the disputed issue;
- DSM: no dense coupling decomposition question;
- FMEA/FTA: replacement correctness was the primary issue, not failure enumeration.

Result:
- PASS — 1 lens preserved the actual contract correction.

## Case 3 — Game open-ended concept generation

Prior evidence:
- knowledge/lessons/lego-wave3-prospective-validation-r1.md
- validated detached Game correction 4ea0979313cf7ebed4b5450ad75f520d5ac8a3b2

Decision:
Should MechanismLibrary precedent bound the concepts that CompositionPlanner is allowed to propose?

Problem signature:
- desired object/design not fully known: yes;
- concept generation beyond precedent: yes;
- repeated comparable arms: no;
- trustworthy whole-product fitness: no;
- organization/control topology: no.

Router result:

Selected MSTS:
1. ck-design

Rejected:
- exploration-policy: repeated comparable feedback prerequisite absent;
- evolutionary-search: trustworthy product evaluator prerequisite absent;
- organizational-cybernetics: wrong problem object.

Result:
- PASS — the router reproduces the Wave 3 phase separation with one lens instead of activating three search/generative methods.

## Case 4 — Agent Security workspace/egress/effect pipeline

Prior evidence:
- knowledge/lessons/agent-security-lego-r1.md
- knowledge/lessons/agent-security-cross-system-destroyer-r1.md
- knowledge/lessons/agent-security-cross-domain-destroyer-r1.md

Decision:
Are read/derive/network/persist/effect authority and controls aligned across an agentic capability?

Problem signature:
- agent/plugin/tool authority pipeline: yes;
- data visibility/egress: yes;
- dynamic control/effect commit: yes;
- unsafe-control/security consequence: yes;
- persistence/reconciliation: yes.

Router result:

Selected MSTS:
1. agent-security composite profile

Suppressed component lenses by overlap:
- information-flow;
- feedback-control;
- STPA.

Reason:
The validated Agent Security profile explicitly consumes these components and adds cross-domain authority/effect/persistence laws. Selecting all four by default would duplicate analysis.

Escalation rule:
If the profile exposes a novel subquestion beyond its validated coverage, route that subquestion to the owning primitive lens/domain method.

Result:
- PASS — composite-profile routing reduces context cost without deleting primitive intellectual ownership.

## Case 5 — Agent Service R16 read-only deployment canary

Prior evidence:
- knowledge/lessons/ordivon-agent-service-readonly-deployment-r16.md

Decision:
Does the bounded R16 MCP deployment expose exactly the intended four read-only tools and preserve the stated no-effect boundary?

Available direct evidence:
- source/deployment contract tests;
- exact returned tool-set check;
- graph regression;
- repository test suite;
- explicit statement that later live systemd canary is a separate deployment action.

Problem signature:
- bounded implementation verification;
- no unresolved architecture, causal, generative, safety-model, information-flow, or organization question required for the stated acceptance decision.

Router result:

Selected MSTS:
- none.

Handoff:
- DOMAIN_METHOD / existing deployment tests and acceptance evidence.

Rejected:
- Systems Engineering: boundary already explicit;
- STPA: no additional system-loss decision required for the bounded read-only acceptance;
- Information Flow: no unresolved secret/data visibility claim in this acceptance;
- Compositional Contracts: no provider replacement decision;
- all generative/search lenses: wrong phase/object.

Result:
- PASS — NO_LENS is a valid and useful output.

## Cross-case result

Selected lens counts:
- Runtime feedback: 1
- Harness replacement: 1
- Game concept generation: 1
- Agent Security pipeline: 1 composite profile
- R16 deployment canary: 0

No case required >1 lens for its bounded decision.

This does not imply one-lens analysis is generally sufficient. It demonstrates that prior successful cases can be recovered without catalog-wide activation.

## Router standing

PROSPECTIVELY_VALIDATED_MINIMUM_SUFFICIENT_ROUTER_R1

What is validated:
- explicit prerequisite rejection;
- overlap/dominance pruning;
- composite-profile suppression of duplicate component lenses;
- NO_LENS/domain-method handoff;
- preservation of previously decision-changing lenses.

What is not validated:
- global optimality of selected lens sets;
- automated semantic classification from arbitrary natural language;
- quantitative value-of-information scoring;
- correctness for every future discipline.

## Retention gate

The router itself must be retired or revised if prospective use shows:
- repeated omission of a lens that later changes the decision materially;
- routine selection of >3 lenses;
- frequent manual override because registry prerequisites are wrong;
- composite profiles hiding important primitive-lens distinctions;
- routing cost exceeding the analysis cost it saves.
