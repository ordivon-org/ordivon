---
gate_id: gate_manifest
display_name: Verification Gate Manifest
layer: L8
hardness: hard
purpose: Gate manifest consistency and baseline integrity
protects_against: "Silent gate removal, downgrade, no-op replacement, manifest/baseline mismatch"
profiles: ['pr-fast', 'full']
timeout: 60
tags: [governance, verification, dg-pack]
---

# Verification Gate Manifest

## Purpose

Gate manifest consistency and baseline integrity

## Protects Against

Silent gate removal, downgrade, no-op replacement, manifest/baseline mismatch

## Usage

```bash
python -m ordivon_verify run gate_manifest
```

## Implementation

See `run.py` for the detection logic.
