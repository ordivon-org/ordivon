# Package: Distribution

Last census: 2026-09-13
Standing: **READY_FOR_REAL_WORK**

Current source owner: `capabilities/distribution/`

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

## Current owner and historical observations

The package-level `READY_FOR_REAL_WORK` label is a broad *capability census*
classification defined in `packages/README.md`: provider-native delivery
can be started for a real task. It is **not** an assertion that Ordivon has a
currently installed general-purpose distribution/approval service.

The current `capabilities/distribution/` Owner retains optional external
provider observations, effect-safety guidance and one Workstation-consumed
negative R7 publication-intent fixture. Its previous internal approval /
EffectAuthority producer, bound-input admission and reconciliation code
were retired from current source; the R7 fixture does not restore them.

**Historical only** — the separate Distribution v2 snapshot
`/root/projects/ordivon-distribution-v2@03ccc562160b` observed authenticated
GitHub readback, bounded read-only Temporal → integration paths, and an exact
approval ingress. This evidence is useful as research provenance, but does not
establish present availability, production write authority or delivered effects.

For a current delivery, combine Runtime execution where needed, n8n workflow
or provider-native clients/APIs, the provider's own IAM/OAuth, and exact
provider acceptance/readback. Do not rebuild the retired generic admission
system merely to satisfy this package card.

## Concrete current gaps

No generic distribution engine gap is proven.

Each new destination may expose a task-local adapter/authentication/read-back gap. Real writes require explicit effect authority; credentials alone are not sufficient authority.

## Acceptance workload

When a real publish/write is explicitly authorized:

`exact intent + account + payload -> provider-native effect -> provider acceptance/read-back -> reconcile exact occurrence -> retain evidence`

If the external result is ambiguous, do not blindly retry unless provider idempotency or authoritative absence evidence makes the retry safe.

## External references

- OCI Distribution Specification: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
