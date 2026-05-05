# PGI-3.07 Extended Mind Tooling Map

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.07
Tags: `pgi`, `runtime-evidence`, `extended-mind`, `tooling`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add an ExtendedMindTool object so Ordivon can treat terminals, editors, AI
assistants, notes, git, CI, and validators as cognitive extensions without
granting them authority.

## Constraints

- Does not authorize action.
- Does not make tools source of truth.
- Does not replace human judgment.
- Does not loosen privacy boundaries.

## Actions

Created:

```text
docs/governance/extended-mind-tooling-map-pgi-3.md
scripts/validate_pgi_extended_mind_tool.py
tests/fixtures/pgi_extended_mind_tool/valid/codex.json
tests/fixtures/pgi_extended_mind_tool/invalid/replaces-judgment.json
tests/fixtures/pgi_extended_mind_tool/invalid/no-data-boundary.json
tests/unit/governance/test_pgi_extended_mind_tool.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| Codex local agent map | VALID |
| tool replaces judgment | INVALID |
| missing data boundary | INVALID |

## Review

PGI-3.07 is locally closed as a seed extended-mind map. It lets Ordivon use
tools intensely without worshiping them.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-025: Cognitive tools must declare role, data boundary, failure modes, and
human-retained judgment before being treated as governance surfaces.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.08 - Alpha and Externalization Alignment
```
