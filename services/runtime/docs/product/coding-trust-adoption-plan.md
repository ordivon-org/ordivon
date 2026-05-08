# Coding Trust Adoption Plan

Status: **CURRENT** | Date: 2026-05-08
Phase: Coding-Trust-Adoption
Authority: `source_of_truth` | AI Read Priority: 1

## Thesis

CTTS is closed as a foundation. Coding Trust Adoption is the new execution
center for Ordivon Verify's Coding profile.

The product question is no longer "can OV provide project-independent
templates?" It can. The adoption question is:

```text
Can a new project AI use those templates to build a local evidence system that
lets reviewers trust AI coding work claims without OV granting authority?
```

## Target Users

- AI-heavy developers using Cursor, Claude Code, Codex, Copilot, or similar
  tools.
- Project AI agents that need a repeatable evidence-localization flow.
- Reviewers and small-team tech leads deciding whether an AI work claim is
  trustworthy.
- DevEx or platform engineers who need lightweight trust structure before
  larger governance systems exist.

## Core Adoption Loop

```text
Run discovery
-> choose minimal/standard/deep
-> emit template pack
-> project AI localizes
-> owner/reviewer confirms canonical gates
-> rerun vibe/merge/release audit
-> repair evidence or record debt
```

OV provides generic templates, discovery hints, report surfaces, and trust
signals. The target project AI fills project-local evidence. The target project
owner/reviewer confirms canonical gates and authority. OV never authorizes
merge, release, deploy, execution, tool use, skill permission, or business
workflow.

## Adoption Tiers

| Tier | User | Purpose |
|------|------|---------|
| `minimal` | solo / vibe coding | Make AI claims observable and tied to basic evidence |
| `standard` | maintained repo / reviewer workflow | Bind claims to artifacts, tests, receipts, review, gates, docs, and debt |
| `deep` | long-lived agent-heavy repo | Add release claims, skills/tools, memory/content, traces, lessons, and CandidateRule drafts |

## Report UX Contract

- `--summary`: compact newcomer / handoff view with status, top gaps, missing
  evidence, next action, and non-authorization boundary.
- `--markdown`: PR/handoff report with surfaces, top findings, adoption
  boundaries, missing evidence, warnings, and recommended next action.
- `--full`: repair appendix for project AI with claim bindings, release claims,
  skill safety, memory/content, harness/trace, gate candidates, and
  agent-native risk surfaces.

The report must not describe `DEGRADED` as PASS. It must not imply
`READY_WITHOUT_AUTHORIZATION` approves merge, deploy, release, production use,
tool use, skill permission, policy activation, or business action.

## External Dogfood Policy

External dogfood is read-only unless a target project owner explicitly asks OV
to emit templates into a chosen output directory.

Real project observations may appear in `discovery-candidates.json` or runtime
dogfood receipts. They must not become generic template rules. Hermes and other
external repositories remain samples, not sources of project-specific product
logic.

## Boundaries

- No SaaS.
- No GitHub bot.
- No agent runner.
- No MCP server.
- No automatic fixer.
- No Trade/Health/Finance profile in this phase.
- No public schema standard.
- No compliance, certification, partnership, equivalence, or production-ready
  claim.

## Success Criteria

- A newcomer can run discovery, emit a template pack, and understand the next
  project AI task within five minutes.
- A project AI can localize templates without treating candidates as authority.
- A reviewer can paste the Markdown report into a PR/handoff and see blockers,
  missing evidence, and next action.
- Dogfood samples cover tiny, medium, and agent-native adoption shapes without
  adding project-specific rules.

