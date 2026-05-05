---
gate_id: entropy_gate
display_name: Entropy Gate
layer: L4.5A
hardness: hard
purpose: Enforce structural entropy ceilings — file count limit, import depth, freshness SLO, coverage minimum, growth velocity
protects_against: "Unchecked system growth, unsustainable file accumulation, documentation rot, checker coverage erosion"
profiles: ['pr-fast', 'full']
timeout: 30
tags: [entropy, gate, structural-constraint, anti-bloat, lehman-laws]
---

# Entropy Gate

## Purpose

Enforces hard structural constraints that prevent entropy from growing
beyond governable thresholds. Based on Lehman's Laws of Software Evolution.

This checker runs in **pr-fast** — it blocks PRs that would push the
system beyond its entropy ceiling.

## Gates

| Gate | Threshold | Hardness |
|------|-----------|----------|
| File ceiling | total_files < 2500 | BLOCKED |
| Import depth | max_import_depth < 6 | BLOCKED |
| Freshness SLO | stale_pct < 10% | DEGRADED |
| Coverage minimum | checkers/sqrt(files) > 0.5 | DEGRADED |
| Growth velocity | < 10%/month on total_files | BLOCKED |

## Integration

Gate violations create Lesson entries. When a gate BLOCKs a PR, it
automatically creates a CandidateRule proposal for human review.
