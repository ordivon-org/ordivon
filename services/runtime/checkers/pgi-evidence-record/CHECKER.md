---
gate_id: pgi_evidence_record
display_name: PGI Evidence Record Validator
layer: L9D
hardness: escalation
purpose: Validate PGI evidence records have source, timestamp, freshness
protects_against: "Evidence without source, stale evidence, unverifiable claims"
profiles: ['full']
timeout: 30
tags: [governance, verification]
---

# PGI Evidence Record Validator

## Purpose

Validate PGI evidence records have source, timestamp, freshness

## Protects Against

Evidence without source, stale evidence, unverifiable claims

## Usage

```bash
python -m ordivon_verify run pgi_evidence_record
```
