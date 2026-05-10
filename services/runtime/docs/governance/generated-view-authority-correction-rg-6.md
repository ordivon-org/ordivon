# Generated View Authority Correction — RG-6

**Phase:** RG-6 — Generated View Authority Correction
**Status:** CLOSED
**Date:** 2026-05-09
**Authority:** supporting_evidence (closure receipt)

## Problem

RG-0 identified `checker-coverage-manifest.json` registered with `authority = source_of_truth` despite being a machine-generated view. Generated artifacts must default to `supporting_evidence` or `derived_from_registry`, never `source_of_truth` by default.

## Fix

Changed `checker-coverage-manifest` authority from `source_of_truth` to `supporting_evidence` in `document-registry.jsonl`. Updated notes to clarify auto-generated status.

## Files changed

```
docs/governance/document-registry.jsonl  — 1 line: authority source_of_truth→supporting_evidence
```

## Verification

`verification-gate-manifest.json` was already correctly registered as `supporting_evidence` — no additional fixes needed.

## Invariants preserved

- Generated objects are not source of truth by default
- Auto-generated manifests are evidence, not authority
- No authorization semantics changed

## Validation

```
Registry tests: 140 passed
doc-registry:   1 pre-existing (ctts-3m-stage-summit)
current-truth:  0 blocking
```
