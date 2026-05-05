# Ordivon Source-Doc Consistency Audit and Red-Team Repair Map

Status: **current** | Date: 2026-05-02
Tags: `source-doc-audit`, `red-team`, `ordivon-verify`, `trust-signal`
Authority: `supporting_evidence` | AI Read Priority: 2

## Summary

Ordivon remains a governance operating system. The current external wedge,
`ordivon-verify`, is a read-only trust verification CLI: it emits trust signals
(`READY`, `DEGRADED`, `BLOCKED`) and does not authorize execution.

The main red-team risk is trust-signal laundering: incomplete, contradictory, or
ambiguous evidence producing a softer signal than the governance boundary
intends.

## Finding Classification and Repair Map

| ID | Class | Severity | Main Risk | Repair Files | Test Files | Status |
|----|-------|----------|-----------|--------------|------------|--------|
| RT-01 | Config fail-open | High | Broken or missing config silently degrades to defaults | `src/ordivon_verify/cli.py`, `src/ordivon_verify/config.py` | `tests/unit/product/test_ordivon_verify_cli.py` | Mitigated for missing explicit config, invalid explicit config, invalid auto config |
| RT-02 | Minimum coverage gap | Medium-High | `DEGRADED` becomes normalized when required checks are unconfigured | `src/ordivon_verify/cli.py`, `src/ordivon_verify/runner.py`, `src/ordivon_verify/schemas/ordivon.verify.schema.json` | `tests/unit/product/test_ordivon_verify_cli.py`, external fixture tests | Open |
| RT-03 | Receipt semantic evasion | Medium | Natural-language receipt contradictions evade regex windows | `src/ordivon_verify/checks/receipts.py`, receipt schemas | `tests/unit/product/test_ordivon_verify_external_fixture.py`, new adversarial receipt fixtures | Open |
| RT-04 | Lightweight shell/registry/debt validation | Medium | Structurally valid but semantically hollow evidence passes | `src/ordivon_verify/checks/debt.py`, `src/ordivon_verify/checks/docs.py`, `src/ordivon_verify/checks/gates.py` | checker-specific unit tests and strict-mode fixture tests | Open |
| RT-05 | Phase fact-source drift | Medium | Agents select stale status documents as authority | `AGENTS.md`, `README.md`, `docs/ai/current-phase-boundaries.md`, `docs/governance/document-registry.jsonl` | `scripts/check_document_registry.py`, status consistency checker if added | Partially mitigated in `AGENTS.md`; README and boundaries still need sync |

## P0 Repair Detail

RT-01 is the immediate fail-closed repair. The CLI now treats these as config
errors with exit code `3`:

- Explicit `--config` path does not exist.
- Explicit `--config` exists but cannot be parsed.
- Auto-discovered `ordivon.verify.json` exists but cannot be parsed.

This prevents a malformed config from silently becoming `{}` and weakening the
mode or configured check set.

## Remaining Repair Queue

1. RT-02: add `minimum_required_checks` or equivalent mode policy so standard
   mode can require receipts/gates/docs explicitly.
2. RT-03: add structured receipt fields or fixture-backed semantic cross-checks
   beyond local keyword windows.
3. RT-04: strengthen strict-mode registry/debt/gate validators with path
   existence, authority enums, command templates, and duplicate detection.
4. RT-05: finish status synchronization for `README.md` and
   `docs/ai/current-phase-boundaries.md`, then consider a single generated
   phase-status source.

## Boundary

No item above grants execution authority. `READY` remains evidence only.
Broker write access, live trading, policy activation, package publication, and
public standard claims remain NO-GO unless a future stage explicitly opens them.
