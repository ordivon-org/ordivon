---
gate_id: coverage_governance
display_name: Coverage Governance
layer: L4
hardness: hard
purpose: Validate checker coverage manifest completeness
protects_against: "Silent scope decay, enumeration drift, coverage gaps, missing critical checkers"
profiles: ['pr-fast', 'full']
timeout: 60
tags: [governance, verification, dg-pack]
---

# Coverage Governance

## Purpose

Validate checker coverage manifest completeness

## Protects Against

Silent scope decay, enumeration drift, coverage gaps, missing critical checkers

## Usage

```bash
python -m ordivon_verify run coverage_governance
```

## Implementation

See `run.py` for the detection logic.
