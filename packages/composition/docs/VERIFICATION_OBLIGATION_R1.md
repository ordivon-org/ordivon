# Verification Obligation R1 — Thin Task-local Verifier Binding

Date: 2026-09-23
Status: **R1 CANDIDATE / COMPOSITION-GATE PROJECTION ONLY**

## Decision

Verification Obligation R1 adds the smallest missing representation between an already-authored
Cognitive Circuit and the natural verifier that can discharge one of its existing Composition
Gates.

```text
Cognitive Circuit R1
        |
        v
Composition Gate requirements
        |
        v
Verification Obligation compiler
        |
        v
task-local obligation set
        +
caller-authored verifier bindings
        |
        v
binding resolver / validator
        |
        v
existing natural verifier owner/provider
        |
        v
existing composition-gate-result
```

R1 does **not** introduce a universal verifier, verifier registry, verifier ranker, workflow
engine, proof language, execution engine, or domain truth owner.

## V01 — Obligation carrier

Each existing R1 Composition Gate is projected one-to-one into a verification obligation.
The projection binds:

- exact Circuit ID and manifest digest;
- exact source Gate digest;
- producer and consumer stage identities;
- assumption and guarantee;
- verifier owner;
- support scope;
- required/optional standing;
- the existing `ordivon.composition-gate-result` as the discharge result contract.

The obligation has its own canonical digest. The complete obligation set is also
digest-bound. Mutation therefore fails closed rather than silently reinterpreting a stale
binding.

R1 intentionally compiles only Composition Gates. Runtime evidence obligations, domain
acceptance obligations, reality witnesses, scientific claims, and other future obligation
families remain with their natural owners until repeated real pressure justifies a bounded
adapter.

## V02 — Obligation compilation

`compile_verification_obligations(manifest)` first runs the existing Cognitive Circuit
compiler. It then produces a deterministic, disposable projection:

```text
ordivon.verification-obligation-set
  circuitRef
  obligations[]
  requiredGateIds[]
  obligationSetDigest
```

Compilation does not choose a verifier or grant execution authority.

## V03 — Task-local verifier binding

The caller supplies an exact task-local binding set. A binding identifies:

```text
gateId
obligationDigest
verifierOwnerId
verifierRef { id, digest }
verifierClass
nativeSpecificationRef { id, digest } | null
supportScope
nonClaims
```

`verifierClass` is descriptive only. Examples may include owner-native, policy, temporal
model, theorem prover, contract algebra, test runner, empirical replication, or authoritative
observation. R1 assigns no semantics to those strings.

`nativeSpecificationRef` lets a binding point at a TLA+ module, Rego policy, Pacti contract,
Lean theorem file, test suite, research protocol, or other owner-native specification without
making Composition interpret that language.

## Resolution semantics

"Resolve" means deterministic validation of an already-authored binding. It does not mean
search, ranking, provider discovery, installation, liveness probing, or execution.

Resolution fails closed when:

- Circuit identity differs;
- the obligation-set digest is stale;
- a binding references an unknown Gate;
- the obligation digest differs;
- verifier ownership differs;
- support scope is widened;
- duplicate bindings exist.

Required unbound Gates keep the projection open:

```text
VERIFIER_BINDINGS_OPEN
```

When every required Gate has an exact binding:

```text
VERIFIER_BINDINGS_RESOLVED
mechanicalResolution = true
executionAuthorityGranted = false
domainAcceptanceEstablished = false
```

This is binding closure only.

## Existing verifier relationship

R1 deliberately reuses existing natural owners:

```text
policy consequence      -> OPA/Rego owner
temporal Runtime model  -> TLA+/TLC owner
formal contract algebra -> Pacti when task-local pressure justifies it
artifact properties     -> Artifact family verifiers
scientific validity     -> Research/domain verifier
real-world consequence  -> authoritative observation/witness
future theorem proof    -> Lean/Coq/Isabelle provider when justified
```

No provider becomes universal.

## Anti-growth laws

This package must not grow:

- a global verifier catalog;
- automatic verifier ranking;
- a universal verification language;
- a proof database;
- provider installation/lifecycle management;
- generic verifier execution;
- semantic completion authority;
- domain acceptance authority;
- a second Composition Gate result vocabulary.

The stable thin waist is:

```text
task-local obligation identity
+ exact verifier binding identity
+ exact support scope
+ existing verifier-owned Gate result
```

## Next pressure

The next useful integration is not another formal engine. It is one real end-to-end consumer
that lowers a Circuit Gate to this obligation carrier, binds an existing verifier, executes
through the natural owner, and feeds the existing `composition-gate-result` back into R1
closure without widening authority.
