---
gate_id: path_map_evidence
display_name: Path Map Evidence Verification
layer: L3D
hardness: hard
purpose: Verify every governed path-map node has evidence references. No evidence → BLOCKED.
protects_against: "Unverifiable governance claims, nodes without traceable sources, authority changes without review"
profiles: ['full']
timeout: 30
tags: [governance, path-map, evidence, gos-pm2]
---

# Path Map Evidence Verification

## Purpose

GOS-PM-2: every governed/protected path-map node must carry source_refs and
evidence_refs. Generated nodes must be marked as non-source-of-truth.
Authority changes must have review evidence.

## Finding Codes

| Code | Severity | Meaning |
|------|----------|---------|
| PME-1 | BLOCKING | Governed node without sufficient source_refs |
| PME-2 | BLOCKING | Governed node without route — cannot trace to rules |
| PME-3 | BLOCKING | Generated node missing must_not_be_source_of_truth |
| PME-5 | DEGRADED | Receipt claims status without evidence ID |
| PME-6 | BLOCKING | Evidence hash mismatch |
| PME-7 | DEGRADED | Authority upgrade without review evidence |
