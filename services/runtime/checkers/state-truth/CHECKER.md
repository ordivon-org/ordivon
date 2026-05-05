---
gate_id: state_truth
display_name: State Truth Verification
layer: L3
hardness: hard
purpose: Verify current truth declarations match actual system state
protects_against: "Stale state declarations, phase status drift, authority mismatch"
profiles: ['full']
timeout: 60
tags: [governance, verification]
---

# State Truth Verification

## Purpose

Verify current truth declarations match actual system state

## Protects Against

Stale state declarations, phase status drift, authority mismatch

## Usage

```bash
python -m ordivon_verify run state_truth
```
