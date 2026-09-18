# Agent Service R14 -> Current Main Integration R1

Date: 2026-09-18
Status: SOURCE INTEGRATION VERIFIED / PRODUCTION DEPLOYMENT NOT ADMITTED

## Scope

This integration candidate combines:

- current Ordivon Next main source cut:
  `804225e88926840e04a011668bfaf057b16cdf50`
- frozen Agent Service R14 implementation:
  `0721009237365ea61cd975bd187be5171f1dcd52`

The work is performed in isolated Runtime Workspace:

`ws-agent-service-r14-main-integration-r1-20260918`

No production service, systemd unit, provider session, credential store, or external Agent effect is changed by this integration.

## Why this integration exists

Regime-Shift Canary A showed a high-maturity implementation stock outside the main/deployed flow:

`R14 validated implementation -> detached lineage -> legacy live automation remains in production`

A read-only mergeability probe already showed no file-level conflict. This integration closes the next bounded uncertainty: whether the actual combined source passes the current test surface.

## Merge result

R14 merged into the current-main candidate using Git's normal merge semantics.

Observed:
- merge conflicts: 0;
- Agent Service source tree introduced into the current-main candidate;
- 90 files from the R14 lineage became present in the integrated source cut;
- approximately 24.7k R14-lineage lines were introduced by the merge;
- no production deployment action occurred.

## Baseline verification before metadata correction

Immediately after merge, before any corrective edits:

```text
python3 -m compileall -q agent_service tests
python3 -m unittest discover -s tests -p 'test_agent_service*.py'

Ran 181 tests in 95.088s
OK
```

This materially weakens the hypothesis that R14 remained detached because it was mechanically incompatible with the current main cut.

It does not prove deployment readiness or semantic completeness.

## Architecture-evidence correction

The prior destructive review identified a hard R14 architecture metadata defect.

Historical identities:

```text
N40 = CapabilityAdvertisementStore
N42 = DelegationEnvelopeStore
N44 = AgentInterfaceAdvertisementStore
N48 = TransportBindingStore
```

The frozen R14 delta incorrectly referenced:

```text
N40 -> AgentInterfaceAdvertisementStore
N42 -> TransportBindingStore
```

R1 corrects only the architecture evidence:

```text
R14 AgentInterfaceAdvertisementStore refinement -> N44
R14 TransportBindingStore refinement            -> N48
```

The corresponding R14 acceptance receipt is corrected to the same identities.

No runtime Agent Service behavior is changed.

The stale R14 lesson status:

`IMPLEMENTED / FINAL VERIFICATION PENDING`

is also corrected to:

`IMPLEMENTED / ACCEPTANCE PASS`

because the frozen R14 acceptance receipt already records repository verification PASS.

## New graph-identity regression gate

Added:

- `scripts/check_agent_service_graph_identity_r1.py`
- `tests/test_agent_service_graph_identity_r1.py`

The checker replays the R2 -> R14 architecture-delta sequence and fails closed on:

- reuse of an existing NodeId for a different semantic identity;
- refinement of an unknown prior node;
- prior-label mismatch;
- duplicate discovered NodeIds.

One explicitly reviewed compatibility alias is preserved:

```text
N13 EvidenceSemanticVerifier <- historical reference label SemanticVerifier
```

This is narrow allowlisting, not a general permission for label drift.

Observed checker result:

- graph files replayed: 12;
- final node identities: 86;
- hard NodeId collisions: 0;
- standing: PASS.

## Final mechanical verification

After the evidence correction and new regression test:

```text
python3 -m compileall -q agent_service scripts tests
python3 scripts/check_agent_service_graph_identity_r1.py
python3 -m unittest discover -s tests -p 'test_agent_service*.py'
git diff --check

Ran 182 tests in 77.951s
OK
```

Therefore:

`source integration mechanics = VERIFIED`

but:

`source integration verification != production deployment admission`.

## Unresolved semantic gate: authority lifetime

Wave-1 STPA already demonstrated a real semantic ambiguity in R14:

```text
Session OPEN
 -> Delegation / PolicyDecision / TransportBinding created
 -> Session CLOSED
 -> delivery(binding) can still commit
```

This is not classified as a bug until the semantic owner decides the authority-lifetime contract.

The mutually exclusive acceptable directions remain:

1. **historical/bound authority survives Session closure**
   - define an independent Binding/PolicyDecision lifetime and revocation contract; or

2. **effect-time authority must remain current**
   - add an effect-time gate covering the intended Session/delegation/policy revocation sources.

Do not silently choose one through implementation.

This decision remains a deployment gate.

## Current provider gate

The fresh Canary-A read-only provider preflight observed:

- Browserless substrate: healthy;
- provider admission: `CHALLENGE_GATED`;
- provider effect attempted: false.

This does not block source integration.

It does block treating a mechanically healthy Browserless carrier as proof that live Agent end-to-end admission is ready.

## Standing

### Source integration

**READY_TO_INTEGRATE_MAIN**

Evidence:
- conflict-free merge;
- 181/181 baseline Agent Service tests after merge;
- architecture metadata correction;
- graph-identity regression gate PASS;
- 182/182 final Agent Service tests PASS;
- `git diff --check` PASS.

### Runtime semantics

**UNCHANGED BY INTEGRATION CORRECTIONS**

The integration imports frozen R14 behavior. The R1 corrections affect architecture evidence/checking only.

### Production deployment

**NOT_ADMITTED**

Open gates:
1. decide and test authority lifetime / revocation semantics;
2. define the actual Agent Service deployment/API composition rather than assuming source presence creates a service;
3. run a bounded deployment canary against current provider-admission reality;
4. instrument the end-to-end accepted-throughput funnel from intent to semantic acceptance;
5. preserve rollback to the legacy Agent Automation path until the canary is accepted.

## Regime-Lens interpretation

Canary A's diagnosis survives the integration test.

The dominant immediate issue was not a lack of another Agent Service feature. The detached capability stock could be merged into current main without source conflict and passed the existing verification surface.

Therefore the next uncertainty moves downstream:

```text
feature implementation
  -> source integration        [mechanically cleared in this candidate]
  -> semantic authority gate  [OPEN]
  -> deployment composition   [OPEN]
  -> provider admission       [currently CHALLENGE_GATED]
  -> effect evidence
  -> semantic acceptance
  -> accepted E2E throughput
```

That propagation chain is now a more useful control surface than broad R15 expansion.
