---
name: capital-reconcile
description: "Guide recovery and reconciliation for an already-existing Ordivon Capital effect identity. Use only after an effect/attempt/ambiguous outcome already exists; never use this Skill to initiate an order or to blind-retry an UNKNOWN financial effect."
compatibility: W4 recovery guidance. Execution remains non-live; W5 circuit contracts remain the executable owner when present.
metadata:
  source-authority: ordivon-capital-reconciliation-router
---

# Capital Reconcile

This Skill is recovery guidance only. It cannot initiate an effect.

## Preconditions

Require an already-existing exact effect/order/intent identity and whatever provider/account observation is currently authorized. If no effect identity exists, stop.

## Procedure

1. Resolve the exact intent/effect identity; never invent a replacement identity for convenience.
2. Use Capital Trading reconciliation semantics: broad snapshot absence is not proof of no effect.
3. `UNKNOWN`, incomplete fill coverage, stale observations, or contradictory terminal history must remain unresolved/no-mutation.
4. Only authoritative positive execution or proven zero-effect/terminal-zero-fill conditions may drive accounting resolution.
5. Apply accounting resolution through the existing reservation identity. Never recreate a missing reservation from external history.
6. A late terminal contradiction must not reopen or rewrite prior terminal accounting history.

## Hard prohibitions

- no order submission;
- no blind resend after response loss;
- no credential discovery;
- no conversion of Runtime/process success into venue truth;
- no production-write admission.

## Stop condition

Stop at an explicit reconciliation standing and accounting instruction/no-mutation boundary.
