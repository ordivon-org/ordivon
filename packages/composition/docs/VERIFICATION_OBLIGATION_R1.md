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

When **at least one** required Gate exists and every such Gate has an exact binding:

```text
VERIFIER_BINDINGS_RESOLVED
mechanicalResolution = true
executionAuthorityGranted = false
domainAcceptanceEstablished = false
```

This is binding closure only. If no required Gates exist (including
an optional-only manifest), the result stays VERIFIER_BINDINGS_OPEN with
mechanicalResolution=false rather than reporting vacuous proof. Optional
bindings remain valid and unbound optional Gates never become errors.

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

### C06: native Gateway `reconciliation_required` source semantics (2026-11-14)

Actual Gateway `ExecutionObservation` and Harness `runtime_bridge.py` recognize
`deliveryDisposition=reconciliation_required` as a reason to inspect or
reconcile the **original** operation. Composition `C06` now consumes this
fourth Runtime delivery state rather than reporting a protocol error. The
result is still read-only and has `automaticRetryAdmissible=false`,
`providerEffectEstablished=false` and `proofReuseAdmissible=false`. Gateway's
native route owners are `runtime.linux`, `runtime.windows`, and
`runtime.harness`; C06's older `external.pull` fixture is **caller-shaped
synthetic** and is not a native Gateway route claim.

The existing finite TLA+ `EffectReplayFence.tla` has four delivery variants.
The pinned TLC gate includes one new deliberately false fourth-state
reachability probe and the existing unsafe retry mutation. The native Python
correspondence checks 288 bounded combinations; Gateway's real Pydantic
projection independently tests three owner routes. These are finite
source/model tests, **not** an installed PG/physical/provider effect proof.
The cross-module Golden Road is
`../../../docs/AGENT_EXECUTION_CAUSAL_CHAIN_R2.md`.

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

### Source namespace membership is a distinct readset edge (R1 extension)

For the existing task-local `impact-readsets` path, an Owner-supplied readset
item can optionally declare `dependsOnScopeMembership: true` alongside its
`sourcePaths` and `dependenciesComplete`. This explicitly subscribes to the
**exact Git prefix member-set identity** already returned by the native
`source_membership_delta` (`membershipRef`). A new/removal member is therefore
reported as `RECHECK_REQUIRED` for that enumerating consumer, while an
unrelated file-specific consumer remains a `REUSE_CANDIDATE` only when its
caller-supplied readset is separately claimed complete. The bridge rejects
non-boolean values or an absent/mismatched membership reference. Omitting the
field preserves existing direct-file queries; it is not proof that a real
consumer ignores missing or newly discovered files.

The model remains a read-only *selection* with `proofReuseAdmissible: false`.
This is not a graph database, new Source owner or proof/installed acceptance.
The actual Agent Golden Road is
`../../../docs/AGENT_NATIVE_SOURCE_CAUSAL_GRAPH_R1.md`.

### C06 R4: native-stop-only LOST is a real counterexample

On a real PG Runtime cancellation, `job.observe` showed
`executionDisposition=lost`, `executionTerminal=true`,
`deliveryDisposition=committed`, `resultAvailable=false` and only one
`native_stop_evidence` Artifact. That `committed` described a durable
control resolution, not an original Runner result. C06 must recover the
original operation for `lost/orphaned` even if an older installed producer
still labels delivery `committed`. Native Composition tests include both
legacy-contradictory and corrected `unknown` delivery. The finite
EffectReplayFence model includes nine source states, 288 representative
Python cases and one deliberately false LOST+committed reachability property.
An exited/timeout/cancelled process can already have caused a partial effect.
Do not derive `automaticRetryAdmissible=true` or owner effect completion.
