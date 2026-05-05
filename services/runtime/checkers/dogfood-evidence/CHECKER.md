---
gate_id: dogfood_evidence
display_name: Dogfood Evidence Integrity
layer: L7D
hardness: hard
purpose: Verify dogfood records have complete evidence chains: receipt, test, review
protects_against: "Dogfood claims without receipts, PnL without simulated disclaimer, lesson without review"
profiles: ['full']
timeout: 60
tags: [governance, verification]
---

# Dogfood Evidence Integrity

## Purpose

Verify dogfood records have complete evidence chains: receipt, test, review

## Protects Against

Dogfood claims without receipts, PnL without simulated disclaimer, lesson without review

## Usage

```bash
python -m ordivon_verify run dogfood_evidence
```
