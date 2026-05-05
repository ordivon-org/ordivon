# Extended Mind Tooling Map — PGI-3

Status: **CURRENT** | Date: 2026-05-04
Phase: PGI-3.07
Tags: `pgi`, `extended-mind`, `tools`, `ai`, `authority-boundary`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Extended Mind Tooling Map asks:

```text
Which tools extend cognition, and what boundaries keep them from replacing
judgment?
```

## Object

`PGIExtendedMindTool` records:

- tool class
- cognitive role
- data boundary
- failure modes
- governance surface
- what the human retains
- replacement-claim flag
- authority boundary

## Tool Classes

```text
terminal
editor
ai_assistant
knowledge_base
notebook
git
ci
validator
```

## Validator Seed

```text
scripts/validate_pgi_extended_mind_tool.py
```

It rejects:

- claims that tools replace human judgment
- replacement-claim flags
- missing privacy/local/redacted data boundary
- missing human judgment and decision responsibility
- missing "tool is not authority" boundary

## Boundary

Tools can extend cognition. They do not become the creator, the source of truth,
or the authority to act.

Next stage:

```text
PGI-3.08 - Alpha and Externalization Alignment
```
