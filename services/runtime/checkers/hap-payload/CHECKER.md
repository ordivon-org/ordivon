---
gate_id: hap_payload
display_name: HAP Payload Validation
layer: L6C
hardness: hard
purpose: Validate HAP (Harness Adapter Protocol) payloads
protects_against: "Schema violations, task plan structure errors, review record completeness"
profiles: ['full']
timeout: 30
tags: [governance, verification]
---

# HAP Payload Validation

## Purpose

Validate HAP (Harness Adapter Protocol) payloads

## Protects Against

Schema violations, task plan structure errors, review record completeness

## Usage

```bash
python -m ordivon_verify run hap_payload
```
