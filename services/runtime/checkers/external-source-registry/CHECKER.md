---
gate_id: external_source_registry
display_name: External Source Registry
layer: L10A
hardness: escalation
purpose: Validate EGB-2 external benchmark source registry freshness, allowed use, forbidden use, and safe-language boundaries
protects_against: "Stale external benchmark claims, compliance overclaim, certification overclaim, endorsement overclaim, partnership overclaim, public-standard laundering"
profiles: ['full']
side_effects: false
timeout: 30
tags: [egb-2, source-registry, benchmark, safe-language]
---

# External Source Registry

Validates `docs/governance/external-benchmark-source-registry.jsonl`.

This is a shadow-first escalation checker. It reports unsafe benchmark source
drift and external-framework overclaim risks without entering `pr-fast`.
