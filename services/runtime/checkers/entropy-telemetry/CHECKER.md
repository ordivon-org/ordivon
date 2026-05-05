---
gate_id: entropy_telemetry
display_name: Entropy Telemetry
layer: L4.5
hardness: escalation
purpose: Measure and track system entropy metrics — file count, import edges, doc freshness, debt, checker coverage. Foundation of the anti-entropy system.
protects_against: "Unmeasured system growth, invisible complexity creep, blind accumulation"
profiles: ['full']
side_effects: true
timeout: 60
tags: [entropy, telemetry, measurement, lehman-laws, anti-bloat]
---

# Entropy Telemetry

## Purpose

Measures key entropy metrics on every run and logs them to a structured
JSONL ledger. Calculates velocity (rate of change) from historical data.

This is the **measurement foundation** of the Entropy Governance system.
Without measurement, entropy is invisible. With measurement, it becomes
governable.

## Metrics Tracked

### Size
- total_files, docs_files, src_files, test_files
- checkers_count, total_lines (approximate)

### Complexity
- cross_boundary_imports, unique_import_sources
- doc_registry_entries, cross_references

### Health
- stale_docs, docs_missing_freshness
- debt_entries, checker_findings
- checker_coverage_ratio

### Velocity
- d(metric)/dt normalized to % per 30 days
- escalation when >10%/month on any size metric

## Agent-Friendly

All output is structured JSONL. Each entry has:
- timestamp, metric_name, value, unit
- An agent can query and analyze without NLP.
