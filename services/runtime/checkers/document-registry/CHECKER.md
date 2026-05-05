---
gate_id: document_registry
display_name: Document Registry Governance
layer: L6
hardness: hard
purpose: Document registry consistency and semantic safety validation
protects_against: "Stale docs, dangerous phrases, ontology metadata gaps, missing required fields"
profiles: ['pr-fast', 'full']
timeout: 120
tags: [governance, verification, dg-pack]
---

# Document Registry Governance

## Purpose

Document registry consistency and semantic safety validation

## Protects Against

Stale docs, dangerous phrases, ontology metadata gaps, missing required fields

## Usage

```bash
python -m ordivon_verify run document_registry
```

## Implementation

See `run.py` for the detection logic.
