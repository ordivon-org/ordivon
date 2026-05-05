---
gate_id: owner_activation
display_name: Owner Activation Gate
layer: L4.3
hardness: hard
purpose: Enforce that Policy activation requires a named Owner with explicit signoff — no ownerless activation, no self-activation without review
protects_against: "Ownerless policies, unapproved policy activation, policy drift without accountability"
profiles: ['full']
timeout: 30
tags: [owner, activation, policy, signoff, rust-fcp-inspired]
---

# Owner Activation Gate

Requires that any PolicyRecord being activated to active_shadow
or active_enforced has:
1. A named owner (PolicyRecord.owner is not None)
2. Owner signoff recorded in policy-activation-ledger.jsonl

Inspired by Rust RFC FCP: any sub-team member can block with ❌.
In Ordivon: activation requires the specific owner's ✅.
