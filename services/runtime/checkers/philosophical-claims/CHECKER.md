---
gate_id: philosophical_claims
display_name: Philosophical Claims Check
layer: L9B
hardness: hard
purpose: Verify philosophical claims in docs are grounded in evidence, not rhetorical overreach
protects_against: "Unsupported philosophical assertions, philosophy-as-authority, claim inflation"
profiles: ['full']
timeout: 60
tags: [governance, verification]
---

# Philosophical Claims Check

## Purpose

Verify philosophical claims in docs are grounded in evidence, not rhetorical overreach

## Protects Against

Unsupported philosophical assertions, philosophy-as-authority, claim inflation

## Usage

```bash
python -m ordivon_verify run philosophical_claims
```
