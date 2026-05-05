---
gate_id: ogap_payload
display_name: OGAP Payload Validation
layer: L6B
hardness: hard
purpose: Validate OGAP JSON payloads against schemas and safety invariants
protects_against: "Schema violations, READY-authorizes-execution, missing authority_note, duplicate keys"
profiles: ['full']
timeout: 30
tags: [governance, verification]
---

# OGAP Payload Validation

## Purpose

Validate OGAP JSON payloads against schemas and safety invariants

## Protects Against

Schema violations, READY-authorizes-execution, missing authority_note, duplicate keys

## Usage

```bash
python -m ordivon_verify run ogap_payload
```
