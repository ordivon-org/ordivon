# PGI-3.08 Alpha and Externalization Alignment

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.08
Tags: `pgi`, `runtime-evidence`, `alpha`, `externalization`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add an ExternalizationAlignment object so Alpha remains an AI coding agent trust
audit wedge while preserving Ordivon's companion-governance root.

## Constraints

- Does not approve release.
- Does not publish schemas.
- Does not release adapters, SDKs, MCP servers, or platform claims.
- Does not turn trust signal into action permission.

## Actions

Created:

```text
docs/governance/alpha-externalization-alignment-pgi-3.md
scripts/validate_pgi_externalization_alignment.py
tests/fixtures/pgi_externalization_alignment/valid/alpha0.json
tests/fixtures/pgi_externalization_alignment/invalid/platform-claim.json
tests/fixtures/pgi_externalization_alignment/invalid/no-casebook.json
tests/unit/governance/test_pgi_externalization_alignment.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| Alpha-0 alignment | VALID |
| platform/public standard claim | INVALID |
| no casebook refs | INVALID |

## Review

PGI-3.08 is locally closed as an Alpha alignment layer. It lets Ordivon prepare
external surfaces without confusing externalization with origin or authority.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-026: Externalization claims must preserve companion-governance root,
casebook evidence, no release approval, and no public standard/platform/adapter claims.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.09 - Public Philosophy Boundary
```
