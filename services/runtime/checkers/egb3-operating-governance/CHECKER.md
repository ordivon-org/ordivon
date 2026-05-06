---
gate_id: egb3_operating_governance
display_name: EGB-3 Operating Governance
layer: L10D
hardness: escalation
profiles: [full]
side_effects: false
timeout: 120
purpose: Validate EGB-3 OEP lifecycle, freeze warning, trust-budget interpretation, shadow-first boundaries, and reviewer/approver/owner confusion fixtures
protects_against: Operating governance laundering, shadow checker hard-gate confusion, ownerless approval, freeze authorization, trust-budget expansion after spent budget
---

# EGB-3 Operating Governance Checker

This checker validates the EGB-3 operating governance layer in shadow-first
mode. It is evidence only and does not promote EGB-2/EGB-3 checkers to hard
gate status.

It checks:

- OEP lifecycle statuses stay within the EGB-3 state model.
- `shadow_tested` checker records do not claim hard-gate behavior.
- EGB-3 red-team fixtures trigger their expected violation IDs.
- The EGB-3 operating governance document keeps freeze and trust budget
  language diagnostic, not authorizing.

The checker does not authorize merge, release, deployment, publication,
trading, policy activation, or external action.
