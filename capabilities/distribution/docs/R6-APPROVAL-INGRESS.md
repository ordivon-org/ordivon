# Distribution v2 R6 — Exact Approval Ingress

R6 removes the final internal blocker between an explicit user approval artifact and Distribution's existing exact-effect authority gate.

## Production rollout

A dedicated operator-owned InputAuthority named `distribution-effect-approvals` is now configured in both Runtime and Workstation ingress configuration. Runtime external-file ingress allowlists this authority; the older `artifact-golden-r1` ingress remains present and unchanged.

Post-restart verification proved:

- Runtime service active.
- `distribution-effect-approvals` present in `ORDIVON_INPUT_AUTHORITIES_JSON`.
- `distribution-effect-approvals` present in `ORDIVON_INPUT_INGRESS_JSON`.
- `artifact-golden-r1` remains ingress-enabled.
- Workstation ingress config contains `distribution-effect-approvals`.
- authority root exists at `/var/lib/ordivon/distribution-effect-approvals` with mode `0750`.
- authority root contained zero approval objects at verification time.

No approval or provider write was produced by this rollout.

## Narrow authority translator

`scripts/produce_effect_authority.py` is not an approval service. It consumes one exact approval file presented under Runtime `ORDIVON_INPUT_ROOT`, validates `contracts/effect-approval.schema.json`, verifies occurrence equality and validity time, and derives an EffectAuthority whose provider/account/effect fields come from the exact intent rather than the approval file.

This prevents an approval source from rewriting target provider/account/effect metadata while still requiring that the approval bind the exact occurrence (which already includes the canonical effect payload digest).

## Falsification

The R6 tests prove:

1. a synthetic exact approval can translate to a correctly bound EffectAuthority;
2. changing the payload creates a new occurrence and invalidates the old approval;
3. an approval for a different occurrence is rejected;
4. an expired approval is rejected;
5. the CLI refuses ambient approval paths when `ORDIVON_INPUT_ROOT` is absent.

Synthetic approval fixtures exist only inside test execution and are not materialized into the production approval authority.

## Standing

The approval transport and translation path is ready. Real external write remains blocked until a real exact approval is ingested and then frozen through `workspace.execBound`.
