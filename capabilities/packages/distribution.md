# Package: Distribution

Last census: 2026-09-13
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Deliver an exact intended artifact/payload to an exact destination/provider/account and obtain authoritative evidence about the external result.

Distribution is consequential-effect handling, not merely file copying. Provider acceptance/read-back is distinct from local upload/API success.

## Mature external knowledge owners

- provider-native publishing/upload APIs and destination rules;
- provider-native account, identity and authorization mechanisms;
- OAuth/OIDC or other established authorization protocols where applicable;
- OCI Distribution Specification for OCI/content-registry use cases;
- HTTP/provider idempotency and reconciliation semantics where supported;
- platform-specific rollout, moderation, withdrawal and publication rules.

There is no benefit in inventing a universal Ordivon transport protocol over mature provider APIs.

## Observed local capability

Existing Distribution v2 (`/root/projects/ordivon-distribution-v2@03ccc562160b`) already provides useful bounded capability/evidence:

- authenticated GitHub observation/read-back proven;
- durable workflow -> integration-edge paths proven for non-effectful/read-only cases;
- exact approval ingress exists;
- exact intent/account/payload binding rules exist;
- ambiguous-result retry rules are retained;
- real provider writes remain authority-gated.

Runtime, n8n, Skopeo/OCI tooling and provider-native clients/APIs can be composed as required.

## Concrete current gaps

No generic distribution engine gap is proven.

Each new destination may expose a task-local adapter/authentication/read-back gap. Real writes require explicit effect authority; credentials alone are not sufficient authority.

## Acceptance workload

When a real publish/write is explicitly authorized:

`exact intent + account + payload -> provider-native effect -> provider acceptance/read-back -> reconcile exact occurrence -> retain evidence`

If the external result is ambiguous, do not blindly retry unless provider idempotency or authoritative absence evidence makes the retry safe.

## External references

- OCI Distribution Specification: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
