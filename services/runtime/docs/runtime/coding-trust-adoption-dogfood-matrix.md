# Coding Trust Adoption Dogfood Matrix

Status: **CURRENT** | Date: 2026-05-08
Phase: Coding-Trust-Adoption-R1
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This matrix defines how Coding Trust Adoption dogfood should be evaluated after
CTTS closure. It is generic by design: dogfood samples may be real or fixture
repositories, but their project-specific gates, workflows, paths, and owners
must not become generic OV template rules.

## Matrix Fields

Every dogfood run records:

| Field | Meaning |
|-------|---------|
| `repo_kind` | tiny fixture, medium AI-heavy repo, or agent-native repo sample |
| `risk_stage` | `vibe`, `merge`, or `release` |
| `template_tier` | `minimal`, `standard`, or `deep` |
| `discovery_result` | what OV discovered without writing target files |
| `template_export_result` | whether explicit `--emit-template-dir` produced a pack |
| `localization_gap` | what the target project AI still needs to fill |
| `top_blockers` | blockers or evidence gaps surfaced by OV |
| `next_action` | evidence repair, claim downgrade, debt entry, or review request |
| `non_authorization_boundary` | confirmation that OV did not authorize action |

## Dogfood Families

### Tiny Fixture Repo

Goal: validate newcomer comprehension and `minimal` adoption.

Expected run shape:

```text
repo_kind: tiny fixture repo
risk_stage: vibe
template_tier: minimal
discovery_result: finds README/tests/claim candidates
template_export_result: emits minimal pack to explicit output directory
localization_gap: project AI fills first claim binding and receipt
top_blockers: missing evidence if claim/test/review is absent
next_action: add evidence or downgrade claim
non_authorization_boundary: READY_WITHOUT_AUTHORIZATION is not approval
```

### Medium AI-Heavy Repo

Goal: validate `standard` adoption with claim binding, gate candidates, and
review evidence.

Expected run shape:

```text
repo_kind: medium AI-heavy repo
risk_stage: merge
template_tier: standard
discovery_result: finds tests/workflows/docs and candidate gates
template_export_result: emits standard pack to explicit output directory
localization_gap: owner/reviewer confirms canonical gates; project AI fills claim bindings
top_blockers: missing claim binding, missing review, unconfirmed gates, open evidence debt
next_action: repair evidence or record debt
non_authorization_boundary: workflow candidates are not canonical gates
```

### Agent-Native Repo Sample

Goal: validate `deep` adoption for skills/tools, memory/content, traces, release
claims, lessons, and CandidateRule drafts.

Expected run shape:

```text
repo_kind: agent-native repo sample
risk_stage: release
template_tier: deep
discovery_result: finds agent-native evidence surfaces
template_export_result: emits deep pack to explicit output directory
localization_gap: project AI separates capability, evidence, review, and authority
top_blockers: release overclaim, skill/tool permission laundering, memory truth laundering, trace approval laundering
next_action: repair boundary, attach evidence, downgrade claim, or record debt
non_authorization_boundary: skill/tool/workflow/trace/memory evidence is not permission, truth, approval, or safe action
```

## Hermes Boundary

Hermes may be used as a read-only dogfood sample only.

Allowed:

- read-only discovery
- read-only summary/Markdown/full reports
- explicit template export to an external review directory
- dogfood receipt describing generic adoption gaps

Not allowed:

- modifying Hermes files without owner request
- promoting Hermes workflows into OV generic template rules
- hard-coding Hermes paths, gates, owners, skills, or release process into OV
- treating Hermes dogfood results as approval of Hermes merge/release/deploy

## Recorded Read-Only Sample: Hermes Agent

Date: 2026-05-08

| Field | Observation |
|-------|-------------|
| `repo_kind` | agent-native repo sample |
| `risk_stage` | `release` for deep discovery; `merge` for trust report |
| `template_tier` | `deep` |
| `discovery_result` | 14 candidate claim/receipt docs, 2 candidate test commands, 10 workflows, 145 `SKILL.md` files, 80 release claim lines sampled |
| `template_export_result` | 16 generic template files emitted to `/tmp/ov-hermes-deep-pack`; target repo not modified |
| `localization_gap` | no agent claim bindings, no OV config, no owner-confirmed gate manifest, no debt/document registry |
| `top_blockers` | merge-stage report BLOCKED on missing claim binding and missing confirmed gate manifest |
| `next_action` | project AI should localize deep pack, bind a concrete claim to artifacts/tests/receipt/review, and ask owner/reviewer to confirm canonical gates |
| `non_authorization_boundary` | read-only sample; no Hermes merge/release/deploy/tool/skill authorization |

UX note: the first Hermes full Markdown report repeated the same missing-evidence
signals under Warnings after they already appeared in Top Findings, Hard
Failures, and Missing Evidence. CTA Round 2 therefore deduplicates Markdown
warnings that are already represented as hard failures or missing evidence.

