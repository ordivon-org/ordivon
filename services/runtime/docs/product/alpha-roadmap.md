# Alpha Roadmap - Agent Work Trust Flywheel

Status: **ACTIVE** | Date: 2026-05-02
Tags: `alpha`, `roadmap`, `agent-work`, `trust-flywheel`, `red-team`, `blue-team`
Authority: `source_of_truth` | AI Read Priority: 1

## Thesis

Ordivon should not run agents. Ordivon should make agent work trustworthy.

Alpha is an externalization path, not the root meaning of Ordivon. The root
meaning is defined by the companion governance constitution:

```text
docs/architecture/ordivon-companion-governance-constitution.md
```

The Alpha line turns that companion governance system into a
developer-understandable trust layer for agent-native work. It must proceed by
case evidence first, then schemas, then adapters. No stage in Alpha grants
execution authority.

## Alpha Line

| Stage | Name | Primary question | Exit evidence |
|-------|------|------------------|---------------|
| Alpha-0 | Evidence of Governed Work | Can Ordivon verify AI coding work before a team trusts it? | 5-10 casebook entries, one Verify report shape, red/blue backlog |
| Alpha-1 | Trust Casebook Hardening | Can the casebook repeatedly expose trust laundering patterns? | Red-team fixture suite, blue-team repairs, false-comfort regressions |
| Alpha-2 | Skill Safety Review | Can Ordivon review skill-like agent capabilities without executing them? | Skill manifest/readme/script boundary checks, no credential/action authorization |
| Alpha-3 | Memory and Content Hygiene | Can Ordivon catch stale, cross-project, or authority-confused memory/content? | Memory/content fixture set, freshness/source receipt checks |
| Alpha-4 | Harness Evidence Import | Can Ordivon read runtime artifacts without becoming the runtime? | Read-only import contracts for traces/checkpoints/review records |
| Alpha-5 | Public Wedge Readiness | Is the public Verify wedge honest, bounded, and packageable? | No private paths, no release overclaim, install smoke, public docs dry run |

## Execution Flywheel

Every Alpha work unit follows the same loop:

```text
Case -> Red-Team Claim -> Verify Failure/Gap -> Blue-Team Repair
     -> Regression Test -> Trust Report -> Review -> Lesson -> CandidateRule Check
```

Rules:

- Casebook evidence comes before public schema claims.
- `READY` is rendered as `READY_WITHOUT_AUTHORIZATION`.
- DEGRADED must explain missing evidence; it must not become a soft pass.
- Red-team fixtures must stay in the repo as regression assets.
- Blue-team repairs must be small, local, and evidence-backed.
- CandidateRule remains advisory; Policy activation remains NO-GO.

## Alpha-0 Execution Inventory

Current Alpha-0 scope is AI coding agent trust audit with one Verify entry:

```bash
ordivon-verify check .
```

Active surfaces:

| Surface | Current treatment |
|---------|-------------------|
| claims | receipt contradiction scan |
| receipts | configured receipt paths required in standard/strict mode |
| tests | inferred from receipt evidence; structured test schema deferred |
| diff | inferred from receipt/work artifact; structured diff import deferred |
| debt | external debt ledger validator |
| docs | document registry validator |
| gates | gate manifest validator |
| review | receipt/review wording safety scan |

## Red-Team Backlog

| ID | Scenario | Target stage | Status |
|----|----------|--------------|--------|
| A0-RT-01 | Broken config weakens checks | Alpha-0 | Mitigated |
| A0-RT-02 | Standard mode lacks receipt evidence | Alpha-0 | Mitigated |
| A0-RT-03 | Review says READY authorizes merge/deploy | Alpha-0 | Mitigated |
| A0-RT-04 | CandidateRule described as active Policy | Alpha-0 | Mitigated |
| A0-RT-05 | Tests claimed without command/result evidence | Alpha-1 | Planned |
| A0-RT-06 | Stale current_truth document cited as authority | Alpha-1 | Planned |
| A2-RT-01 | Skill requests external credential without boundary | Alpha-2 | Planned |
| A3-RT-01 | Memory lacks source receipt or freshness | Alpha-3 | Planned |
| A4-RT-01 | Harness trace omits failed tool call | Alpha-4 | Planned |

## Blue-Team Backlog

| ID | Repair | Owner stage | Status |
|----|--------|-------------|--------|
| A0-BT-01 | Config fail-closed | Alpha-0 | Done |
| A0-BT-02 | Missing evidence field in trust report | Alpha-0 | Done |
| A0-BT-03 | Authorization laundering receipt patterns | Alpha-0 | Done |
| A0-BT-04 | CandidateRule/Policy confusion patterns | Alpha-0 | Done |
| A1-BT-01 | Structured test evidence requirements | Alpha-1 | Planned |
| A1-BT-02 | Casebook fixture runner | Alpha-1 | Seeded in Alpha-0 |
| A2-BT-01 | Skill boundary scanner | Alpha-2 | Planned |
| A3-BT-01 | Memory/content source receipt scanner | Alpha-3 | Planned |

## Exit Criteria For Alpha-0

Alpha-0 can close when:

- `ordivon-verify check .` is the documented local trust audit entry.
- The trust report includes surfaces, missing evidence, and
  `READY_WITHOUT_AUTHORIZATION`.
- At least 5 casebook entries are completed or intentionally deferred with
  explicit rationale.
- The red/blue backlog has no open P0 trust-laundering repair.
- README, AGENTS, and phase boundaries agree that Alpha-0 is active.

## Local Casebook Runner

Alpha regression fixtures can be checked with:

```bash
uv run python scripts/run_alpha_casebook.py
```

The runner is local-only and read-only. It does not run agents or authorize
actions; it verifies that known red-team fixtures still produce the expected
trust signals.

## Boundary

Alpha is not a public launch. It does not publish a standard, create a server,
activate policy, run agents, execute tools, merge code, deploy code, trade, or
authorize external action.
