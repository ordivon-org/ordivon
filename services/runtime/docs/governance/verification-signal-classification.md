# Verification Signal Classification

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: Post-DG-H2
Authority: `current_status` | AI Read Priority: 1

## The Rule

**A failed verification command is an observation, not a verdict.**

Before acting on any checker failure, classify the signal source.
Do not assume the checked object is broken.

## Four Questions Before Every Fix

When a checker fails, answer in order:

1. **Source**: Is the failure from the object, the tool, the command, the environment, or the spec?
2. **Class**: Which failure class does this belong to? (see below)
3. **Authority**: Would "fixing" this change a source-of-truth document? If yes, stop and escalate.
4. **Closure**: How should the debt (if any) be closed?

## Eight Failure Classes

| Class | Meaning | You should |
|-------|---------|------------|
| `object_defect` | The checked object has a real defect | Fix the object |
| `tool_limitation` | Tool doesn't support the feature yet | Use correct flags; do NOT fix the object |
| `command_mismatch` | The verification command is wrong | Fix the command |
| `environment_mismatch` | Path, shell, or platform mismatch | Fix the environment |
| `spec_mismatch` | The checker is checking the wrong thing | Fix the spec |
| `historical_noise` | Pre-existing, not from current work | Classify as out-of-scope; do not hide |
| `misclassification` | Previous debt classification was wrong | Reclassify |
| `expected_negative_control` | Checker is expected to fail | Document as intentional |

## The Hardest Rule

> **Do not mutate authoritative documents to satisfy a misclassified checker.**

If a checker says AGENTS.md is broken but the real issue is a tool
feature gate, do NOT change AGENTS.md. Close the debt by reclassification.

This applies to all source-of-truth documents: AGENTS.md, Stage Summits,
ontology registry, governance contracts.

## Seven Ways to Close Debt

Debt can be closed by:
1. `fixed_by_code_change` — the object was actually broken
2. `fixed_by_doc_change` — the doc had a real defect
3. `fixed_by_command_correction` — the verification command was wrong
4. `closed_by_reclassification` — the debt was misclassified
5. `closed_as_tool_limitation` — the tool doesn't support the feature
6. `closed_as_out_of_scope` — not in current phase scope
7. `superseded_by_tool_update` — the tool matured and the issue vanished

## VD-001: The Case That Proved This

- `ruff format --check AGENTS.md` → FAIL. "Markdown formatting is experimental."
- `ruff format --check --preview AGENTS.md` → PASS. "Already formatted."

The checker was measuring ruff's feature gate, not AGENTS.md.
AGENTS.md had zero formatting issues.
VD-001 was closed by reclassification. No file was changed.

## Relationship

This document is the actionable companion to `verification-debt-policy.md` §8.
That document defines the framework; this document is the reminder you read
before making a fix decision.

**External tool output is evidence, not authority.**
**Checker failure is an observation, not a verdict.**
