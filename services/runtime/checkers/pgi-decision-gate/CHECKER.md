---
gate_id: pgi_decision_gate
display_name: PGI Decision Gate Validator
layer: L9C
hardness: escalation
purpose: Validate PGI-2 decision gate payloads have required fields and sound reasoning
protects_against: "Missing evidence, insufficient confidence, missing reversibility assessment"
profiles: ['full']
timeout: 30
tags: [governance, verification]
---

# PGI Decision Gate Validator

## Purpose

Validate PGI-2 decision gate payloads have required fields and sound reasoning

## Protects Against

Missing evidence, insufficient confidence, missing reversibility assessment

## Usage

```bash
python -m ordivon_verify run pgi_decision_gate
```
