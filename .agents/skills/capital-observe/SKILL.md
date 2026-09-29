---
name: capital-observe
description: "Route Ordivon Capital observation work to registered read-only LEGO circuits. Use for public market observation or, only when independently admitted, private read-only account observation. Preserve provider truth/currentness and never infer write authority from data visibility."
compatibility: Requires the Ordivon monorepo Capital registry/contracts. Public observation is effect-free; private observation remains blocked unless current provider/owner admission exists.
metadata:
  source-authority: ordivon-capital-registered-lego-router
---

# Capital Observe

This Skill is an advisory router. It owns no market truth, credential, provider permission, execution authority, or financial effect.

## Procedure

1. Read `domains/capital/config/capital_lego_registry.json`.
2. Bind the requested observation to registered LEGO only.
3. For public descriptive market work, prefer `PUBLIC_MARKET_OBSERVATION_R1` through `ordivon_capital.governance.read_circuit`.
4. Preserve source/provider identity and observation currentness. Supplied/local data is not automatically current provider truth.
5. For private account observation, check `domains/capital/config/private_reality_policy.json` first. If private account data is not currently admitted, stop with the unresolved authority requirement; do not discover credentials or downgrade the requirement.
6. Keep observation separate from recommendation, authorization, reservation and effect.

## Non-claims

- Seeing account/market data does not imply permission to trade.
- Mechanical circuit completion does not establish financial/semantic completion.
- This Skill never initiates an external financial write.

## Stop condition

Stop when the observation circuit is selected/executed with explicit currentness/evidence limitations, or when an authority prerequisite is unresolved.
