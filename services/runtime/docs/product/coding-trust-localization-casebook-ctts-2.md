# Coding Trust Localization Casebook — CTTS-2

Status: **CURRENT** | Date: 2026-05-08
Phase: CTTS-2
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

CTTS-2 proves that the Coding Trust Template System can be localized by a
target project AI without Ordivon Verify becoming the target project's
authority.

```text
Claim -> Evidence -> Review -> Decision Boundary -> Receipt
      -> Debt/Lesson -> CandidateRule or no-rule rationale -> next cycle
```

OV provides templates, discovery hints, and trust signals. Project AI fills
project-local evidence. Project owner/reviewer confirms canonical authority.
OV never grants merge, release, deploy, execution, tool, skill, or business
workflow permission.

## Minimal Case

Use `minimal` for newcomer or vibe-coding projects.

```text
Claim: AI added a small helper.
Evidence: changed file + test command + receipt.
Review: lightweight note that evidence was inspected.
Decision boundary: READY_WITHOUT_AUTHORIZATION.
Receipt: records evidence sufficiency only.
```

Proper downgrade:

```text
Claim: "tests passed"
Missing: no test command or output
Signal: BLOCKED or DEGRADED
Action: attach test evidence or downgrade the claim
```

## Standard Case

Use `standard` for merge-stage trust structure.

Required localized surfaces:

- agent claim binding
- receipt
- test evidence
- review evidence
- owner-confirmed gate manifest
- debt ledger
- document registry

Workflow candidates are hints. They become canonical gates only after local
owner/reviewer confirmation. Evidence without review must not become
`Reviewed` or `Gate-Checked`.

Proper downgrade:

```text
Claim: AI completed a merge-stage task.
Evidence: artifact + test command exist.
Missing: review evidence.
Signal: BLOCKED at merge stage.
Action: add review evidence or record debt; do not claim Gate-Checked.
```

Debt conversion:

```text
DEGRADED finding: stale or missing evidence.
Debt entry: owner, source claim, reason, next action, status.
Receipt: records whether the debt remains open or was repaired.
```

## Deep Case

Use `deep` for long-lived, agent-heavy projects with release, skill, tool,
memory, lesson, and CandidateRule surfaces.

Proper downgrades:

```text
Release claim has evidence refs but no owner release decision
-> evidence is not release permission

Skill declares allowed tools
-> skill capability is not permission

Tool trace exists
-> trace is not consent

Memory source exists
-> memory is not current truth without source, freshness, and scope review

Lesson proposes CandidateRule
-> CandidateRule remains advisory unless separately promoted by project policy
```

## Safe Wording

Use these phrases:

- `READY_WITHOUT_AUTHORIZATION` means evidence sufficiency only.
- `DEGRADED` means an evidence gap or review boundary remains.
- `BLOCKED` means missing evidence, contradictory evidence, or authority leakage.
- Discovery candidates are hints, not canonical gates.
- Evidence is not approval.
- CandidateRule is not policy.
- Skill/tool/workflow/trace existence is not permission.

## Blocked Wording

Do not write these as current truth:

- "ready to merge"
- "approved to deploy"
- "release authorized"
- "skill allowed-tools permits action"
- "candidate rule draft equals binding rule"

If a project needs those decisions, they must come from the target project's
own owner/reviewer process outside OV.

## CandidateRule No-Rule Rationale

Not every lesson should become a CandidateRule.

Use no-rule rationale when:

- the issue is one-off cleanup
- evidence is too weak
- the lesson is project-specific
- the rule would overfit one fixture
- the owner/reviewer has not accepted a policy path

Example:

```text
Lesson: release wording was too strong.
CandidateRule: none.
Rationale: one fixture is insufficient; keep as debt guidance until repeated.
```

## Hermes Dogfood Boundary

Hermes may be used as a read-only dogfood sample. OV did not modify Hermes,
did not promote Hermes-specific gates into templates, and did not make
project-specific authorization decisions. Hermes observations belong in
`discovery-candidates.json` style evidence hints only.
