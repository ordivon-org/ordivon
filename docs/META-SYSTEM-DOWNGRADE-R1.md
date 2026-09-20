# Distribution meta-system downgrade R1

Date: 2026-09-20
Status: ACTIVE

## Decision

Distribution is downgraded from a presumed cross-provider control plane to an optional effect-safety/profile capability.

The current architecture no longer requires Runtime, OPA, Temporal, n8n or any provider adapter to appear in every external effect path.

## Consumer census

A cross-repository executable-reference census found:

- R8 `temporal_integration_dispatch_smoke.py`: no executable consumer outside Distribution;
- R10 `distribution_preflight.py` / Steam profile: no executable consumer outside Distribution;
- the only concrete external source coupling found was Workstation's historical n8n adapter smoke reading a frozen Distribution evidence intent;
- historical Research/Paper1 and Media atlas references are provenance/index data, not runtime consumers.

## Retired in this wave

Forward executable R8 surface:

- `scripts/temporal_integration_dispatch_smoke.py`;
- `scripts/test-temporal-integration-boundary.py`.

Forward executable R10 surface:

- `scripts/distribution_preflight.py`;
- `scripts/test-distribution-preflight.py`;
- `contracts/distribution-preflight.schema.json`;
- `profiles/steam-linux-directory-r1.json`.

Historical R8/R10 docs and evidence remain as provenance.

## Retained for destructive review, not promoted as permanent core

- exact occurrence/content binding;
- effect-approval/effect-authority reference contracts;
- provider-observation binding;
- admission examples;
- reconciliation examples;
- provider/tool compatibility observations.

Each still requires a subsequent natural-owner substitution test. Retention in this wave is not promotion to permanent Ordivon semantics.

## Next destroyer

For D01-D05 ask independently:

```text
D01 effect occurrence identity
  -> caller/domain or provider idempotency identity?

D02 effect authority
  -> client/IAM/OAuth/provider approval instead?

D03 execution
  -> provider-native only

D04 read-back
  -> provider-native only

D05 reconciliation
  -> provider/effect owner rather than generic Distribution policy?
```

The likely stable output is a small set of safety laws and provider-specific profiles, not a long-lived central service.
