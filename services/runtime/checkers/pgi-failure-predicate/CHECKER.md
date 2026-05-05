---
gate_id: pgi_failure_predicate
display_name: PGI Failure Predicate Validator
layer: L9E
hardness: escalation
purpose: Validate PGI failure predicates: what would make this claim false?
protects_against: "Unfalsifiable claims, missing invalidation conditions, confidence without base rate"
profiles: ['full']
timeout: 30
tags: [governance, verification]
---

# PGI Failure Predicate Validator

## Purpose

Validate PGI failure predicates: what would make this claim false?

## Protects Against

Unfalsifiable claims, missing invalidation conditions, confidence without base rate

## Usage

```bash
python -m ordivon_verify run pgi_failure_predicate
```
