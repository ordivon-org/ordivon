# Verified Reintegration External-owner Dogfood R1

Date: 2026-09-22

Status: **W1 PASS / W2 PASS / W3 PASS_SHADOW_NOT_CONFORMANCE_CLAIM / W5 CLOSED / W6 COMPLETE_R1_DECISION**

## Scope

This dogfood executes the first three waves of
`VERIFIED_REINTEGRATION_EXTERNAL_OWNER_CONVERGENCE_R1` without changing R1/R2/R3.2
authority boundaries and without adding a production dependency.

## W1 — Pacti formal-contract shadow

Selected real seam:

```text
Harness PluginGatewayExecutionGrant.max_timeout_ms
        |
        v
Harness/Gateway timeoutMs pass-through
        |
        v
Runtime max_runtime_ms admission
```

The machine contract is intentionally narrow:

```text
Harness allowed request:
  1 <= timeoutMs <= G

Gateway:
  timeoutMs is preserved

Runtime admission:
  timeoutMs <= M
```

For the complete Harness-granted domain to be Runtime-admissible:

```text
G <= M
```

Source and live values are intentionally separated:

- Harness grant default `G = 300000 ms`;
- Harness/Gateway hard local bound `900000 ms`;
- Runtime source fallback `max_runtime_ms = 900000 ms`;
- live Runtime observation on 2026-09-22: `defaultRuntimeMs = 3600000`, `maxRuntimeMs = 86400000`.

An ephemeral Python 3.14 environment installed exact `pacti==0.3.1` from PyPI.
No project dependency or lockfile changed.

Results:

- source-fallback `G=300000, M=900000`: composition **PASS**;
- live-owner `G=300000, M=86400000`: composition **PASS**;
- deliberate `G=900000, M=600000`: Runtime composition **REJECT**, Pacti
  `IncompatibleArgsError`.

This matches the owner-native Runtime admission contract and demonstrates that the shadow
checker can detect a real cross-owner bound mismatch.

## W2 — quotient / missing LEGO

Top-level requirement: preserve a caller-granted timeout through the seam.

Known subsystem: Harness-to-Gateway timeout pass-through.

Pacti quotient derived the missing subsystem obligation:

```text
input:  t_gateway
output: t_runtime

assume:
  1 <= t_gateway <= 300000

guarantee:
  t_runtime = t_gateway
```

Recomposition satisfies:

```text
compose(existing, quotient) refines(top) = true
```

Both the Runtime 900000 ms source fallback and the live 86400000 ms ceiling are correctly eliminated as redundant under the tighter
300000 ms caller grant. The quotient specifies an obligation only; it does not invent a
Runtime implementation.

## W3 — SACM assurance interchange shadow

Source: the existing R3.2 `gate:research-artifact-carrier`.

The disposable XMI uses SACM 2.3 namespace:

```text
http://www.omg.org/spec/SACM/20220301
```

and only metaclasses observed in the OMG normative machine-readable model:

- AssuranceCasePackage;
- ArtifactPackage / Artifact;
- ArgumentPackage / Claim;
- ArtifactReference;
- AssertedEvidence;
- AssertedContext.

The exact normative model downloaded for the experiment had:

```text
sha256:4bc12020fe38018fe24d39e56ec04f2fc9190fe7cf1161d85452fda5f3fbeb1e
```

Round-trip preserved exactly:

- Circuit/gate/standing/manifest/verifier metadata;
- assumption;
- guarantee;
- supportScope;
- all nonClaims;
- all evidenceRefs.

No standing upgrade, scope expansion, or non-claim loss occurred.

The XMI SHA-256 is:

```text
sha256:2552407d0c39a56ae2b495f00f87a1385fcb0593cdd9d72eee8ae9747ba127ac
```

This is a **shadow interoperability experiment**, not an OMG conformance or certification
claim. No SACM service, database, or canonical assurance store is introduced.

## Admission consequence so far

Pacti has crossed the threshold from `INCONCLUSIVE_NETWORK` to a successful real shadow
experiment, but remains `SHADOW_CANDIDATE`: one seam is not enough to justify a production
dependency or formal-contract registry.

SACM has a successful lossless shadow projection for one real Gate, but remains a projection
candidate only. The Ordivon Gate remains source truth.

W4 remains deferred because there is no explicit requirement for a persisted GSN Human view.

## W5 — temporal pressure and owner selection

Focused source/test census found repeated stateful obligations in three independent owner families: Web/Security, Runtime/Harness, and Capital. This is enough to establish temporal-method pressure, but not enough to justify a second temporal toolchain. Runtime already has a digest-pinned TLA+/TLC model for durable admission, at-most-once dispatch, ambiguity preservation, retry-as-new-Attempt, and terminal evidence. The previously accepted 2026-09-19 bounded run produced 25 states / 20 distinct states / depth 9 with zero invariant violations.

The current isolated Workspace could not freshly rerun TLC because the ignored JAR cache was absent; that is recorded as `NOT_RERUN_CACHE_MISSING`, not as a model failure. OCRA 2.1.0 remains a semantic/reference candidate but its latest binary release is old; Apalache 0.58.3 is an active symbolic candidate only if TLC scaling/SMT pressure becomes real. No new temporal binary is admitted.

## W6 — R1 admission decision

- Pacti: **KEEP_SHADOW_OPTIONAL_PROVIDER** until a second real formalizable seam creates recurring demand.
- TLA+/TLC: **KEEP_EXISTING_OWNER** for bounded concurrent/state-machine verification.
- OCRA: **DEFER_BINARY**; reference semantics only.
- Apalache: **DEFER_UNTIL_SYMBOLIC_PRESSURE**.
- SACM: **KEEP_SHADOW_PROJECTION_TARGET**; no assurance database.
- GSN: **VIEW_ONLY_DEFER_NO_CONSUMER**.
- PROV/OpenLineage/SLSA/in-toto/Sigstore-Cosign: **KEEP_EXISTING_OWNER**.

The result is not a new formal-methods subsystem. It is a narrower thin waist with clearer external semantic ownership.
