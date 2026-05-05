---
gate_id: current_truth_protocol
display_name: Current Truth Protocol
layer: L3A
hardness: hard
purpose: Verify current truth documents are consistent with phase boundaries and governance state
protects_against: "Truth drift, stale boundaries, AGENTS.md vs docs inconsistency"
profiles: ['pr-fast', 'full']
timeout: 60
tags: [governance, verification]
---

# Current Truth Protocol

## Purpose

Verify current truth documents are consistent with phase boundaries and governance state

## Protects Against

Truth drift, stale boundaries, AGENTS.md vs docs inconsistency

## Usage

```bash
python -m ordivon_verify run current_truth_protocol
```
