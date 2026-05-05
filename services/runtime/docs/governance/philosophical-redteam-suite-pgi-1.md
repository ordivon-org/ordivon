# Philosophical Red-Team Suite — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.09
Tags: `pgi`, `red-team`, `philosophy`, `misuse`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This suite red-teams philosophy itself.

Core rule:

```text
Philosophy is a governance layer, not a rationalization engine.
```

## Misuse Patterns

| Rule | Misuse | Governance response |
|------|--------|---------------------|
| PGI-MISUSE-001 | Long-termism justifies overwork/body neglect. | Anti-overforce + Body/Energy review. |
| PGI-MISUSE-002 | Freedom justifies gambling/high leverage. | Finance risk gate + FOMO/self-proof screen. |
| PGI-MISUSE-003 | Discipline suppresses fatigue/emotion. | Constraint intake before more effort. |
| PGI-MISUSE-004 | Meaning/destiny bypasses evidence. | EvidenceRecord + uncertainty review. |
| PGI-MISUSE-005 | Non-attachment avoids responsibility. | Review/refusal receipt. |
| PGI-MISUSE-006 | Pragmatism excuses shortcuts. | Constitution boundary + evidence check. |

## Checker Seed

```text
scripts/check_philosophy_misuse.py
```

## Fixtures

```text
tests/fixtures/pgi_philosophy_misuse/clean/boundary.md
tests/fixtures/pgi_philosophy_misuse/unsafe/misuse.md
```

## Boundary

The checker is intentionally narrow. It catches high-signal phrases, not all
possible philosophical self-deception.

Next stage:

```text
PGI-1.10 - PGI-1 Summit and Closure Seal
```
