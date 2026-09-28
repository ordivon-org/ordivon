# Ordivon Monorepo Red-Team R1

Date: 2026-09-27
Status: **CURRENT CANDIDATE FINDING LEDGER — awaiting normal main integration**

## Truth fence

- Current local integration source for this candidate: `d8d5e61e3d7fa3b62781b086a1ea0bd76329d517`.
- Fresh GitHub provider `origin/main` observed during the same campaign: `80c17a3635219fa00c91ee9ea00700918bd14df4`.
- Earlier attack workspace: `838075d839c07ac92d5f31d845dd41a044e65765`.
- Gateway live projection: 0.4.0.
- Host live authority: PostgreSQL schema 9, integrity healthy.

Local integration truth and GitHub provider truth remain separate authorities. This ledger never treats one as proof of the other.

## Red-team LEGO

```text
ENTRY
  -> IDENTITY / AUTHENTICATION
  -> AUTHORIZATION / ADMISSION
  -> OWNER ROUTING
  -> EXECUTION / EFFECT
  -> EVIDENCE / REPLAY
  -> BUILD / RELEASE
  -> PROVIDER GOVERNANCE
  -> RECOVERY / CURRENTNESS
```

Classification: `CONFIRMED_NEW`, `KNOWN_OPEN`, `DRIFT`, `HYPOTHESIS`, or `REJECTED`. A problem is registered only with an exact truth fence, reproducible falsifier, consequence, owner, and acceptance condition.

## RT-SUPPLY-001 — Runtime release tags can bypass protected-main convergence and still mint release attestations

**Class:** `CONFIRMED_NEW`
**Priority:** HIGH
**Owners:** GitHub repository governance + Runtime release authority

`services/runtime/docs/releases.md` calls `.github/workflows/runtime-release.yml` the live monorepo Runtime release authority. It is triggered by `runtime-v*` tag pushes, runs Runtime verification, builds the canonical release set, emits an SPDX SBOM, and creates GitHub attestations.

Fresh provider readback established that the active repository ruleset targets `refs/heads/main` only. No tag-target ruleset was observed, and `git ls-remote --tags origin "runtime-v*"` returned no existing Runtime release tags. The workflow validates the tag/version and derives `owner_commit`, but it does not prove the tagged `GITHUB_SHA` was accepted into protected provider `main` or another explicitly admitted protected release ref.

A non-provider-mutating synthetic probe then created a harmless Runtime-touching child commit in an isolated workspace. Result:

```text
HypotheticalTag                         = runtime-v0.1.0
SyntheticUnreviewedCommit               = f233a71d60947769795047ff46de3a0429ecc2e7
ExistingWorkflowTagNameCheck            = true
ExistingWorkflowOwnerAncestorCheck      = true
ExistingWorkflowOwnerTreeCheck          = true
ExistingWorkflowBindWouldPass           = true
CandidateIsReachableFromProtectedMain   = false
ProtectedMainIsAncestorOfCandidate      = true
```

Thus the current release identity/bind preflight accepts a Runtime-touching child revision that has not passed protected-main convergence. No real tag was created and no release workflow was triggered.

GitHub documents that tag `push` workflows run from the pushed ref/tip commit and can use workflow content not merged to the default branch. SLSA Source v1.2 treats release tags as intended-immutable named references and requires source-control enforcement against tag movement/deletion for its protected source expectations. GitHub Rulesets provide tag-target creation/update/deletion restrictions.

**Impact:** release/provenance integrity bypass for a repository principal capable of tag creation/write. This does not prove unauthenticated access or automatic production deployment; deployment receipts remain separate Runtime authority.

**Acceptance:** provider-native `runtime-v*` tag protection; narrowly scoped tag creation authority; no update/deletion outside reviewed recovery; tagged commit must be proven reachable from the admitted protected provider source ref; release identity records that source ref/revision; repository tests fail if these controls disappear; provider API readback verifies the rule is active.

Evidence: `evidence/RT_SUPPLY_001_SYNTHETIC_TAG_PROBE_R1.json`.

## RT-CI-001 — Runtime release workflow changes escape Runtime affected-owner verification

**Class:** `CONFIRMED_NEW`
**Priority:** MEDIUM
**Owners:** repository mechanics + Runtime release authority

On current local integration source, the exact projection:

```text
python3 tools/repo/convergence_plan.py --changed-file .github/workflows/runtime-release.yml
```

returns:

```text
crossCutting        = false
directOwners        = []
verificationOwners = []
verifyTasks         = []
queueClass          = REPOSITORY_ONLY
```

Provider/current source explains why: the Runtime release workflow is neither inside an owner root nor in `CROSS_CUTTING_PATHS`.

A second non-mutating falsifier removed the `mise run runtime:verify` step from an in-memory copy of the provider-main release workflow. All 11 Runtime-release substrings currently required by `tools/repo/check_github_governance.py` still matched:

```text
OriginalHasRuntimeVerify=true
MutatedHasRuntimeVerify=false
MissingExistingRequiredNeedles=[]
WouldExistingRequiredStringContractPass=true
```

**Impact:** a release-workflow change can weaken/remove Runtime owner qualification without the affected-owner planner compensating and without violating the current Runtime-release repository string contract. Protected-main governance reduces likelihood, so priority is below RT-SUPPLY-001.

**Acceptance:** map the release workflow to Runtime/release owner verification; regression-test affected selection; make governance fail if owner verification is removed or bypassed; retain owner-native verification instead of cloning Runtime tests into root mechanics.

## RT-DOC-001 — Gateway README advertises retired Host northbound API

**Class:** `DRIFT`
**Priority:** LOW
**Owner:** Gateway documentation

`services/gateway/README.md` still advertises `continuity.*` / `collaboration.*` compatibility vocabulary and says `host.status` is not exposed. Gateway 0.4 source and canonical architecture instead expose schema-9 Social Work tools (`actor.*`, `work.*`, `space.*`, `topic.*`, `message.*`, `subscription.*`, `attention.*`) plus `host.status`; the compatibility facades are retired.

For an Agent-operated monorepo, README text is executable planning context even though it is not authority. Stale documentation can drive stale tool calls and compatibility reconstruction.

**Acceptance:** align README with the current Gateway contract and add a destroyer/test that rejects retired Host northbound vocabulary as current documentation.

## Known-open reproduction — not double-counted

### RT-CATALOG-001 — consumer MCP catalog freshness

The current client catalog still exposes retired `continuity.*` / `collaboration.*` and direct-Host `task.*` / `board.*`; stale calls return `Unknown tool`. Canonical architecture already records this as a consumer/connector currentness seam. Do not restore aliases.

### AF-S2 — authenticated ingress is not capability-scoped Security authorization

`platform/security/docs/GATEWAY-ADMISSION-R1.md` already records this as OPEN. Cloudflare verification establishes authenticated ingress attribution, not per-capability/effect authority. Gateway execution source does not consume a Security authorization decision, and Linux routing defaults to Runtime `trusted_local` if context is omitted. This is a known architecture gap, not a new finding.

### Gateway Runtime credential lifecycle

Gateway 0.4 currently reports both Runtime execution capabilities configured but unavailable because their bearer files are absent. The credential directory exists with restrictive ACLs but contains no credential files; direct Windows Runtime remains available and Host continuity remains available. Existing repair work already owns this seam. Evidence: `evidence/GATEWAY_RUNTIME_CREDENTIAL_LIVENESS_R1.json`.

## Negative controls / boundaries that held

### Runtime request replay identity

A harmless Windows Runtime command was submitted under `clientRequestId=redteam-r4-replay-control-20260927`. Repeating the identical request returned the same historical Job/Attempt. Reusing the same request ID with changed arguments was rejected before execution with `IDEMPOTENCY_CONFLICT`. No replay finding is registered from this test. Evidence: `evidence/RUNTIME_REPLAY_NEGATIVE_CONTROL_R1.json`.

### Owner-boundary literal scanner

Not a finding by itself. `OWNER_DEPENDENCY_BOUNDARY_R1.md` explicitly scopes the R1 guard to active source owner-root literals and disclaims package-manager, dynamic path, protocol, generated-code, and runtime-network completeness. A future finding requires a concrete current dependency edge that violates the intended owner contract.

### Undirected convergence closure

Currently conservative/over-verifying rather than proven under-verifying. Treat as CI-economics/precision pressure unless a concrete omitted verification edge is demonstrated.

## External baseline mapping

- **NIST SP 800-218 SSDF v1.1 PS.1:** protect code/configuration from unauthorized access and tampering; release-source controls should prevent unaccepted revisions from becoming release authority.
- **NIST SSDF PS.2 / PS.3:** verify release integrity and protect/archive releases and provenance. Runtime already has strong artifact digest/SBOM/attestation mechanics; RT-SUPPLY-001 is about the upstream source-ref admission feeding those mechanics.
- **SLSA Source v1.2:** reliable source change history and protected/immutable consumable tags.
- **GitHub Rulesets:** provider-native branch/tag rules can restrict creation, update, deletion, status, and history operations.
- **OpenSSF Scorecard:** branch/release protection and workflow token/dependency controls are supply-chain controls; Ordivon already pins external Actions by full SHA and uses restricted workflow token permissions, so the red-team focus is the uncovered release-ref admission seam rather than re-reporting controls that already exist.

## Current frontier

1. Close RT-SUPPLY-001 at provider authority, then live-read back tag rules and release ancestry enforcement.
2. Close RT-CI-001 in repository mechanics with a falsification test derived from the exact attack above.
3. Fix RT-DOC-001 and connector catalog currentness without restoring compatibility APIs.
4. When Gateway Runtime credentials recover, quantify AF-S2 consequences across interactive, local-service, and workload identities; do not interpret liveness failure as authorization safety.
5. Continue Runtime effect/cancellation/orphan-recovery attacks while preserving the distinction `execution success != external-effect idempotency != domain completion`.
6. For Social Work, test only claims that exceed its documented HOLD boundary; ActorRef/participation/subscription are explicitly not authentication, confidentiality, assignment, or EffectAuthority.
