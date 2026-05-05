---
gate_id: runtime_evidence
display_name: Runtime Evidence Integrity
layer: L5
hardness: hard
purpose: Verify receipt/schema/checker integrity across evidence artifacts
protects_against: "Receipt corruption, schema drift, checker output tampering, stale evidence references"
profiles: ['pr-fast', 'full']
timeout: 60
tags: [governance, verification, dg-pack]
---

# Runtime Evidence Integrity

## Purpose

Verify receipt/schema/checker integrity across evidence artifacts

## Protects Against

Receipt corruption, schema drift, checker output tampering, stale evidence references

## Usage

```bash
python -m ordivon_verify run runtime_evidence
```

## Implementation

See `run.py` for the detection logic.
