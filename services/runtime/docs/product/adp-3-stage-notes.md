# ADP-3 Stage Notes — Detector Hardening

Status: **current** | Date: 2026-05-02 | Phase: ADP-3
Tags: `adp-3`, `stage-notes`, `detector`, `structure`, `registry`, `pv`, `debt`
Authority: `source_of_truth` | AI Read Priority: 2

## Purpose

ADP-3 extends the ADP detector from line/window regex scanning toward local,
deterministic, structure-aware governance analysis using HAP-3 structured
objects, DG document registry metadata, and PV public/package surface artifacts.

## What ADP-3 Is

- A local static detector that parses HAP-3 TaskPlan/ReviewRecord JSON, DG
  document-registry.jsonl entries, and PV public-surface markdown files.
- 22 detection rules across four surfaces: structure (8), registry (5), PV (5),
  red-team debt (1), plus broader path discovery.
- Inherits ADP2R red-team debt lessons and partially remediates the
  highest-value detector-facing portions.

## What ADP-3 Is Not

- Not a runtime enforcer.
- Not a CI gate.
- Not an API, SDK, MCP server, or SaaS endpoint.
- Not a package release, public standard, or public repo.
- Not an action authorization mechanism.
- Not a replacement for human review.

## Relationship to Other Phases

- HAP-3 provides the structured objects (TaskPlan, ReviewRecord).
- DG provides the registry metadata (freshness, supersession, authority, AI read priority).
- PV provides the public-surface boundaries (wedge vs core, package safety, release overclaim).
- ADP-2R provides the red-team debt lessons inherited by ADP-3.

## Output

Detector produces Findings with severity (blocking/degraded/warning/info),
pattern IDs, evidence snippets, and recommended fixes. Findings are review
evidence only — not automatic approval or authorization.

## Status

CLOSED — sealed via ADP-3-S.
Next recommended: DG-1 / DGP-1 (Document Governance Pack hardening).
