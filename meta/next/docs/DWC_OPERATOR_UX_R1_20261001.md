# DWC Operator UX R1 — 2026-10-01

Status: CANDIDATE / PROJECTION-ONLY / DW11

## Purpose

DW11 turns bounded Defense-Window Convergence owner outputs into a fast re-entry surface for humans and Agents. It does not create a dashboard authority, security verdict owner, scheduler, policy engine, or effect-authority service.

## Recursive LEGO R2.1 decomposition

| LEGO | Input owner | Output | Explicit non-ownership |
| --- | --- | --- | --- |
| Source Horizon | DW01-DW10 / owner projections | sourceSetDigest, horizons, coherent/mixed standing | no currentness minting |
| Security Axis Projector | applicability, exposure, protection, compromise, recovery owners | five independent axis states + CLOSED/OPEN/UNKNOWN | no global green/PASS |
| Workflow Separator | Host/Temporal/workflow owner | phase, running/pending/completed refs, blockers | workflow progress is not security standing |
| Policy Clock | DW03 policy owner | policy/version/decision/deadline projection | no deadline invention or priority grant |
| Attention Deduper | Host/domain update carriers | groups by caseRef + subjectRef + updateRef | no rank/suppression; conflicting variants remain visible |
| Effect Review Lens | effect/authority/verifier owners | action, target, actuator/provider, authority standing, blast radius, commit point, reversibility, verifier | no authorization or effect |
| Re-entry / Next-safe-action Lens | owner-supplied candidate actions + dependency refs | unranked safe-action surface | no scheduling, winner selection, or hidden priority |
| Progressive Disclosure | all above | compact -> plan -> evidence -> raw refs | presentation changes no authority/policy/access |

These LEGO compose as a view pipeline, not a control plane:

owner truth -> bounded DWC bundle -> source-horizon fence -> independent axes/workflow split -> attention/effect/re-entry lenses -> disclosure renderer

## Machine contract

Input kind: ordivon.security-dwc-operator-bundle-r1.

Output kind: ordivon.security-dwc-operator-view-r1.

The view always carries sourceSetDigest, sourceHorizons, observationStanding, five independent security axes, a separate workflowProgress section, policyClock when supplied by a policy owner, effectReviewSummary, attentionSummary, and explicit projectionSemantics.

No global security verdict is emitted. An axis remains UNKNOWN/OPEN even when another axis is CLOSED or verified. Deadline data is shown only when an explicit policyRef, policyVersion, policyOwnerRef, decisionRef, sourceRef, and deadlineAt are supplied.

## Progressive disclosure

1. compact: case identity, subject set, horizons, five axes, workflow counts/blockers, policy clock, authority/approval standing summary.
2. plan: compact + exact blockers, dependency edges, unranked next-safe actions, effect-review cards.
3. evidence: plan + source index, per-axis evidence/source refs, deduplicated attention groups.
4. raw: evidence + raw provider artifact references. Raw artifacts remain owned by their providers and are not copied into the view.

Every level binds the same sourceSetDigest. Disclosure changes representation only.

## Re-entry rule

A fresh Agent must be able to answer from Host + owner truth, without chat history: what case/subjects are in scope; which axes are known/open/unknown; whether source horizons are coherent; what workflow is running or blocked; who owns each blocker; whether a policy-grounded deadline exists; what effect is proposed and where its commit/reversal/verifier boundaries are; and which candidate next actions are currently owner-reported READY/BLOCKED/UNKNOWN.

## Attention semantics

Attention is grouped by (caseRef, subjectRef, updateRef). Exact duplicates collapse to one update group. Materially different variants under the same key are retained as MULTIPLE_VARIANTS rather than silently selecting a winner. The view never ranks attention.

## Effect review semantics

Before an effect is presented for approval, the view requires targetRefs, actuatorRef, providerRef, authorityBindingRef and owner-reported authorityStanding, blastRadius, commitPoint, reversibility, verifierRef, approvalPromptStanding, and sourceRef. Missing fields fail closed at projection time. The view never converts these fields into authorization.

## Measurement

Mechanical compile/runtime latency can be measured by the CLI and Runtime evidence. Human operator decision latency and unnecessary-approval-prompt rate require a timed human/Agent re-entry trial with labeled prompts; this R1 does not fabricate those measurements. The fixture and tests establish the instrumentation surface and negative controls needed for that trial.

## CLI

JSON:

python3 meta/next/scripts/dwc_operator_ux_r1.py meta/next/evidence/acceptance/dwc-operator-ux-r1-reentry-fixture-20261001.json --disclosure compact

Text re-entry surface:

python3 meta/next/scripts/dwc_operator_ux_r1.py meta/next/evidence/acceptance/dwc-operator-ux-r1-reentry-fixture-20261001.json --disclosure plan --format text

## Acceptance boundaries

- PASS requires unit/negative tests, real CLI execution on the fixture, and read-back evidence.
- Synthetic fixture acceptance proves projection mechanics only; it does not prove live Exchange security standing, live owner currentness, effect authority, or human decision-time improvement.
- A future live dogfood must build the bundle from actual DW01-DW10 owner outputs and current Host work re-entry coordinates.
