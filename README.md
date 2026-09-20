# Ordivon Distribution v2

Distribution is an **optional effect-safety and delivery profile**, not a mandatory Ordivon control plane.

Its purpose is to preserve a small set of cross-provider safety lessons when a task actually needs them:

1. model/caller intent is not execution authority;
2. one consequential external effect should be bound to the exact payload/account/effect occurrence that was authorized;
3. local transport/workflow success is not provider acceptance;
4. ambiguous external outcomes must be reconciled by the provider/effect owner before unsafe retry.

These are composition laws. They do not imply one mandatory Distribution runtime stack.

## Current architecture

The default route is the thinnest adequate natural owner:

```text
task/domain
  -> provider-native API / client / CLI / connector
  -> provider IAM / OAuth / policy
  -> provider-native effect identity/read-back
  -> claim-specific verification
```

Use a Distribution-owned reference contract or reconciliation helper only when a concrete cross-provider workload demonstrates that direct provider semantics leave a real gap.

In particular, there is **no canonical path** requiring:

```text
Runtime input.ingest
-> Distribution EffectAuthority
-> OPA
-> Temporal
-> n8n
-> provider
```

Runtime, OPA, Temporal, n8n and provider adapters are independently selectable capabilities. A caller may use none, one, or several of them.

## Residual forward surface

The repository currently retains bounded reference implementations for:

- exact occurrence/content binding;
- provider-observation binding;
- explicit effect-authority translation where a caller cannot use its native IAM/approval surface directly;
- admission examples over those bindings;
- reconciliation examples that preserve UNKNOWN and require provider idempotency or authoritative absence before retry.

These implementations are **reference/profile mechanisms**, not universal domain truth or a required service.

Natural owners remain:

| Concern | Natural owner |
| --- | --- |
| caller/user identity | identity provider / client |
| credentials | provider / secret store |
| authorization | IAM / OAuth / caller policy |
| provider capability | provider |
| physical execution | provider / Runtime only when exact local evidence is required |
| durable process | Temporal-class workflow only when needed |
| integration automation | n8n / provider-native integration |
| provider acceptance/read-back | provider |
| semantic acceptance | consuming domain |

## Retired forward surfaces

### R8 Temporal integration smoke — retired

The former Distribution-owned Temporal Activity smoke had no cross-repository executable consumer. Durable invocation is generic workflow infrastructure and remains with Temporal/integration owners. Historical R8 documentation/evidence remains provenance only.

### R10 Steam local preflight — retired

The former Steam-oriented local directory lifecycle preflight had no cross-repository executable consumer. It was a provider/product-specific validation experiment, not a cross-provider Distribution primitive. A future real Steam release should use SteamPipe/SteamCMD and the product/release owner directly. Historical R10 documentation/evidence remains provenance only.

## Provider/tool observations

Postiz, rclone, OpenAPI Generator, provider-native APIs and similar systems are candidate providers, not components of a Distribution platform. Their presence in historical observations or compatibility tests does not make them mandatory dependencies.

Prefer:

```text
native provider interface
  -> deterministic connector/workflow
  -> provider-specific adapter
  -> cross-provider abstraction only after demonstrated duplication
```

## Historical R2-R7 material

R2-R7 document the path by which the repository learned to separate caller intent, provider observation, exact effect authority, Runtime-bound input experiments, Artifact release standing and provider read-back.

Those documents remain useful provenance. Their historical composition is not a required current topology.

## Verification rule

```text
local command success
!= workflow success
!= provider acknowledgement
!= provider effect
!= domain success
```

Evidence must come from the owner appropriate to the claim.

## Repository direction

This repository should shrink as provider/client standards improve.

A retained custom mechanism must answer:

1. Which real cross-provider workload uses it?
2. Which natural owner cannot express the needed semantic?
3. Why is a direct provider/client solution insufficient?
4. Can the mechanism be a profile/Skill/reference instead of executable infrastructure?

No demonstrated residual means retire or externalize.
