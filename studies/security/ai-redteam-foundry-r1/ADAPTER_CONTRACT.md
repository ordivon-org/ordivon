# External Red-Team Provider Adapter Contract R1

Status: experimental study contract; does not replace provider-native schemas.

## Principle

Ordivon should normalize *references and evaluation semantics*, not flatten external red-team systems into a
mega-framework. Provider-native artifacts remain authoritative for their own mechanics.

The minimal cross-provider projection is:

```text
ProviderRunRef
  -> ThreatModelRef
  -> AttackSpecRef
  -> TargetSpecRef
  -> ObservationRef
  -> JudgeRef
  -> FindingProjection
  -> RegressionReceiptRef
```

Each `*Ref` must be digest/version bound where the provider exposes stable bytes or identifiers.

## PyRIT mapping

PyRIT already owns orchestration mechanics:

```text
PyRIT Scenario          -> provider campaign/run
PyRIT Seed              -> attack objective/seed artifact
Attack Technique        -> AttackSpec provider implementation
Executor / Attack       -> attack-search execution
Converter               -> input transformation lineage
Target                  -> TargetSpec provider identity
Scorer                  -> JudgeSpec provider identity
Memory / output         -> provider-native evidence artifact
```

Ordivon should not implement a parallel seed/converter/executor hierarchy. The adapter should retain exact
PyRIT run identity, version, scorer configuration, and raw output reference, then project bounded Finding
metadata.

## garak mapping

```text
generator   -> TargetSpec
probe       -> AttackSpec / attack engine
buff        -> transformation lineage
attempt     -> ObservationRef
detector    -> JudgeSignal
evaluator   -> provider evaluation projection
harness     -> provider orchestration
report      -> provider-native evidence artifact
```

A garak detector result is not automatically Ordivon scientific truth. The Foundry records it as a provider
judgment and may require a deterministic or independent judge before closing a finding.

## HarmBench mapping

```text
behavior             -> bounded attack objective
red-team method      -> AttackSpec implementation
generated test case  -> AttackArtifactRef
completion           -> ObservationRef
classifier/evaluator -> JudgeSpec
ASR                   -> metric under exact benchmark configuration
```

The model/chat template/system prompt and generation parameters are part of target identity for replay.

## JailbreakBench mapping

JailbreakBench contributes a useful reproducibility envelope:

- threat model;
- behavior identifier;
- exact attack artifact;
- system prompt/chat template;
- target model/version;
- scoring function;
- query/cost accounting.

Ordivon should preserve these as foreign references rather than silently translating them into local defaults.

## StrongREJECT mapping

StrongREJECT is primarily a Judge provider in this architecture. A StrongREJECT score must retain evaluator
version/configuration and must not be collapsed into `world_state_violation=true`. Its key role is detecting
"empty" jailbreaks where refusal was bypassed but target capability was not actually elicited.

## EasyJailbreak mapping

```text
Selector   -> search policy
Mutator    -> transformation provider
Constraint -> candidate admissibility filter
Evaluator  -> search feedback judge
```

These are attack-search internals. Ordivon should record the selected recipe/version and outputs, not recreate
its component framework.

## AgentDojo mapping

AgentDojo is especially important because it supplies environment semantics:

```text
user task       -> legitimate utility objective
injection task  -> attacker objective
suite/world     -> stateful Target environment
tool execution  -> effect simulation
benchmark check -> deterministic world-state judge
```

This should become the preferred external provider for testing `model compromise != effect compromise`.

## CaMeL mapping

CaMeL is not an attack engine. It is an architecture-level defense comparator. Experiments should compare a
baseline agent and a control/data-separated agent under the same attacker/provider evidence, while preserving
CaMeL's own semantics rather than implementing a superficial prompt wrapper.

## Acceptance requirements for any future adapter

An adapter is not admitted merely because the package installs. It must prove:

1. exact provider/version identity;
2. exact target identity and generation settings;
3. exact attack/search budget;
4. recoverable raw provider evidence;
5. explicit judge identity;
6. deterministic/stable projection into Finding fields;
7. no provider output is silently promoted to production Security standing;
8. replay fixture and schema regression tests exist.


## Provider-currentness hazards

Provider adapters are compatibility seams, not timeless truth. R1 therefore treats provider version and raw
artifact bytes as part of evidence identity.

- **PyRIT:** scenario/result output and framework object surfaces continue to evolve. Consume a documented
  export surface, pin the exact provider version, and retain the raw export rather than depending on the
  provider's internal memory/database schema.
- **garak:** report JSONL has changed across releases and provider-specific detector scores are not one global
  semantic scale. Preserve the exact report, target config, probe/detector identity, and garak version.
- **AgentDojo:** the API and benchmark implementation remain active research software. `utility` and
  `security` booleans are task/version-owned observations; they must remain verbatim until the exact benchmark
  code and task checks establish their meaning. An error or skipped action must never be silently normalized
  into a universal security success/failure bit.

Any adapter must fail closed on missing fields or ambiguous provider semantics. Updating an adapter is a
semantic change requiring replay fixtures and differential regression, not routine parser maintenance.

## Existing Ordivon Evidence waist

`docs/architecture/EVIDENCE_BOUNDARY_CENSUS_R1.md` already closed the cross-owner evidence question: do not
create a universal Evidence object or database. Security v2 already owns a narrow mechanical `EvidenceRef`
with provider, format, path, SHA-256, and byte length.

The Foundry `ProviderArtifactRef` therefore retains provider version as study metadata but exposes only an
explicit projection onto that existing mechanical waist:

```text
ProviderArtifactRef
  provider
  providerVersion
  artifactKind
  artifactDigest
  byteLength
  sourcePath
        |
        v
Security EvidenceRef projection
  provider
  format
  path
  sha256
  byte_length
```

That projection does not admit evidence into production standing and does not import Security owner internals
into the study. Security remains the consumer/authority for any later S02 ProviderEvidence integration.
