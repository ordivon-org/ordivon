---
gate_id: oep_governance
display_name: OEP Governance
layer: L10B
hardness: escalation
purpose: Validate Ordivon Enhancement Proposals for required sections, rollback, graduation criteria, security review, and non-authorization boundaries
protects_against: "Unreviewable cross-boundary changes, missing rollback, missing graduation criteria, release authorization laundering"
profiles: ['full']
side_effects: false
timeout: 30
tags: [egb-2, oep, proposal, governance]
---

# OEP Governance

Validates OEP documents under `docs/governance/oep-000*.md`.

This is a shadow-first escalation checker. It validates proposal shape and
authority boundaries without granting any action permission.
