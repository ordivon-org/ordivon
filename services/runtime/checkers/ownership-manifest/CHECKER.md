---
gate_id: ownership_manifest
display_name: Ownership Manifest
layer: L10C
hardness: escalation
purpose: Validate path-native ownership manifest coverage, reviewer/approver split, owner roles, staleness windows, and non-authorization wording
protects_against: "Ownerless governance surfaces, stale owner records, reviewer/approver confusion, approval-language laundering"
profiles: ['full']
side_effects: false
timeout: 30
tags: [egb-2, ownership, reviewer, approver]
---

# Ownership Manifest

Validates `docs/governance/ownership-manifest.jsonl`.

This is a shadow-first escalation checker. It makes ownership visible without
turning approval roles into external action authority.
