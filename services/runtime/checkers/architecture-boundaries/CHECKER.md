---
gate_id: architecture_boundaries
display_name: Architecture Boundaries
layer: L4A
hardness: hard
purpose: Enforce Core/Pack/Adapter import direction invariants
protects_against: "Core importing Pack business logic, finance fields leaking into Core, trade execution refs in governance"
profiles: ['pr-fast', 'full']
timeout: 30
tags: [governance, verification, dg-pack]
---

# Architecture Boundaries

## Purpose

Enforce Core/Pack/Adapter import direction invariants

## Protects Against

Core importing Pack business logic, finance fields leaking into Core, trade execution refs in governance

## Usage

```bash
python -m ordivon_verify run architecture_boundaries
```

## Implementation

See `run.py` for the detection logic.
