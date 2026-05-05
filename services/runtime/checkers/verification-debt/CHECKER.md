---
gate_id: verification_debt
display_name: Verification Debt Ledger
layer: L7A
hardness: hard
purpose: Verification debt tracking and expiry enforcement
protects_against: "Hidden debt, overdue debt, unregistered skipped verification, debt candidate discovery gaps"
profiles: ['pr-fast', 'full']
timeout: 120
tags: [governance, verification, dg-pack]
---

# Verification Debt Ledger

## Purpose

Verification debt tracking and expiry enforcement

## Protects Against

Hidden debt, overdue debt, unregistered skipped verification, debt candidate discovery gaps

## Usage

```bash
python -m ordivon_verify run verification_debt
```

## Implementation

See `run.py` for the detection logic.
