# Cross-domain Verification R3 — Seam-specific Verification Adapters

Date: 2026-09-22
Status: **R3 CANDIDATE / NO UNIVERSAL VERIFIER**

## Purpose

R1 introduced the task-local Cognitive Circuit and verifier-owned Composition Gate.
R2 added currentness-aware Interface Contract evaluation.

R3 answers the next question:

> Can real owner-native facts discharge a cross-owner semantic obligation without
> moving truth authority into a new generic verifier?

R3 deliberately does **not** add another universal result schema. Both adapters emit the
existing R1 `ordivon.composition-gate-result`.

## Architecture

```text
Owner-native facts / evidence
          |
          v
seam-specific verifier adapter
          |
          v
R1 Composition Gate Result
          |
          v
R1 Gate Projection
          |
          +-- mechanicalClosure
          `-- domainAcceptanceEstablished = false
```

The generic layer remains R1. R3 owns only two concrete dogfood adapters.

## Seam A — Research ↔ Artifact publication carrier

This is not a current production source dependency from Research code into Artifact code.
It is a composition-profile and evidence seam:

```text
Study authority
    |
    v
Research publication closure profile
    |
    v
Artifact carrier mechanics / contract evaluation
    |
    v
Research consumes bounded carrier evidence
```

Current owner rules:

- scientific truth stays with Study authority;
- carrier mechanics belong to `capabilities/artifact`;
- venue policy remains an external dated authority;
- distribution/submission effect remains outside Artifact;
- machine carrier PASS is not Human perceptual signoff.

The real Paper3 dogfood remains:

```text
machineStanding = PASS
standing = PENDING_HUMAN
humanGates = [HUMAN_PERCEPTUAL_SIGNOFF]
```

R3 treats that as a satisfied **carrier-machine seam** because its support scope explicitly
excludes scientific correctness, Human perceptual closure, venue authority, and submission
completion.

A mutation that moves `scientificTruth` to Artifact, removes the truth-boundary nonclaims,
or changes the Artifact machine result to FAIL makes the Gate UNSATISFIED.

## Seam B — Web ↔ Security delegated-Agent authority

The repository already declares two current public source seams:

```text
apps/web/src/security-agent-verifier.ts
    -> platform/security/contracts/agent-request-verifier-v1/

apps/web/src/agent-authority.ts
    -> platform/security/contracts/agent-admission-v1/
```

Security owns:

- OAuth/JWT/DPoP request verification;
- bounded Agent Admission + Effect Admission policy evaluation.

Web owns:

- local DPoP replay state substrate;
- Agent Grant storage/resolution/revocation;
- effect-bound approval state;
- effect transaction/replay/conflict behavior;
- Web effect receipts.

The adapter requires:

1. both public seams remain declared in the repo dependency contract;
2. Web source consumes the public Security contracts;
3. Web source does not directly import Security policy/lab internals;
4. WebStore still exposes the expected local replay/Grant/approval state primitives;
5. the real Agent-native E2E preserves the expected fail-closed/replay matrix.

Current real E2E evidence includes:

```text
noProof                      401
wrongKey                     401
proofReplay                  401
firstCreate                  201
exactReplay                  200
conflict                     409
publishStepUp                428
approval                     201
publishApproved              200
revoke                       200
newEffectAfterRevoke         403
historicalReplayAfterRevoke  200
```

The adapter also requires current dogfood to remain explicitly non-production:
`productionEligible=false` and `productionHumanPresenceClaim=false`.

## R3 acceptance results

### Research ↔ Artifact

```text
gate = SATISFIED
manifestDigest =
  sha256:33e299e93b6e114af9a1610fb6fff9bb2dcdadc26b8f74e0a499c0dc16e906a2

R1 projection:
  mechanicalClosure = true
  domainAcceptanceEstablished = false
  projectionDigest =
    sha256:50a3e351377f27d38dea18c5062216217709ce57613af253d02eb157655b3890
```

### Web ↔ Security

```text
gate = SATISFIED
manifestDigest =
  sha256:161391b0c7b831d999a3976acba24f743a6a0d838a348fa9472dc9f7c5f0e6ca

R1 projection:
  mechanicalClosure = true
  domainAcceptanceEstablished = false
  projectionDigest =
    sha256:c04bc1eecbab8c60d0865e6fe0001d8d1d22de1111d8850e635a4bfdd9fc5bfb
```

## Falsifiers

Focused R3 tests require the following mutations to fail closed:

- Research scientific-truth ownership moves to Artifact;
- Artifact machine publication result becomes FAIL;
- Research/Artifact nonclaim boundary is removed;
- one Web→Security public seam declaration disappears;
- Web imports Security policy internals directly;
- Web no longer owns the DPoP replay-state primitive;
- native E2E proof replay becomes accepted;
- production eligibility is smuggled into the canary evidence.

## Anti-growth laws

R3 does not introduce:

- a universal cross-domain ontology;
- a universal semantic verifier;
- a global evidence registry;
- a second Composition Gate schema;
- a Research→Artifact production dependency that does not exist;
- Security ownership of Web durable state;
- Artifact ownership of scientific truth.

The reusable architecture remains:

```text
Domain/owner-native verifier
        -> R1 gate result
        -> task-local composition closure
```

New seams should add narrow adapters only when a real composition requires them.


## R3.1 boundary repair — task-local binding

Post-merge requalification against the stricter owner-boundary checker exposed a separate
physical-coupling defect: the R3 adapters and tests embedded cross-owner repository locators
directly in active Python source.

R3.1 removes that coupling without changing either seam's semantic standing.

The exact task-local binding is:

```text
meta/next/evidence/acceptance/cross-domain-verification-r3-bindings.json
byteDigest =
  sha256:fc83cd8977a69d309283522d23042605de2d0db2685188acd6a57a79648c5964
canonicalBindingDigest =
  sha256:65f8a6ba330c62239bb2d6e7c2c0ab46b44c4515aeef6ee23f5d50dfbc1734a7
```

The repaired structure is:

```text
owner-native facts / locators
          |
          v
Next-local task binding evidence
          |
          v
seam-specific adapter
          |
          v
R1 Composition Gate Result
```

The verifier therefore knows the **seam contract**, while physical repository topology is
provided as bounded task-local evidence. This does not make the binding an owner authority or
a global registry.

The semantic projections are unchanged:

```text
Research <-> Artifact:
  gate = SATISFIED
  mechanicalClosure = true
  domainAcceptanceEstablished = false

Web <-> Security:
  gate = SATISFIED
  mechanicalClosure = true
  domainAcceptanceEstablished = false
```

R3.1 additionally requires the repository owner-boundary checker to report zero undeclared
active cross-owner source-path seams from the R3 adapters/tests. No blanket dependency seam
or checker exemption is introduced.
