---
gate_id: document_freshness
display_name: Document Freshness Audit
layer: L6A
hardness: hard
purpose: Detect stale documents in the document registry based on freshness windows
protects_against: "Stale source_of_truth docs, expired freshness windows, untracked last_verified gaps"
profiles: ['full']
timeout: 120
tags: [governance, verification, dg-pack]
---

# Document Freshness Audit

## Purpose

Detect stale documents in the document registry based on freshness windows

## Protects Against

Stale source_of_truth docs, expired freshness windows, untracked last_verified gaps

## Usage

```bash
python -m ordivon_verify run document_freshness
```

## Implementation

See `run.py` for the detection logic.
