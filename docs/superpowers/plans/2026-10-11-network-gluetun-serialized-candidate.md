# Network Gluetun Serialized Candidate Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use the repository plan-execution discipline task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Qualify Gluetun as a serialized upstream replacement candidate for the current Surfshark physical carrier without changing production network effects or consumer semantic contracts.

**Architecture:** Keep Network-v2 as a semantic control/evidence plane. Add a typed source-only carrier-realization registry that declares the current wg-quick implementation active and Gluetun v3.41.3 a non-authoritative serialized candidate. Later tasks build and qualify the upstream candidate behind existing provider/consumer readiness seams before any cutover.

**Tech Stack:** Python/pytest, JSON/JQ, Taskfile, systemd source contracts, Gluetun, WireGuard, sing-box, Linux netns.

**Spec:** platform/network/docs/UPSTREAM_FIRST_CONVERGENCE_R1.md

## Global Constraints

- Current production provider realization remains unchanged until a separate natural-owner effect gate.
- surfshark:linux-shared-r1 remains single-physical-session.
- Candidate and active realizations never run concurrently with the same ClientIdentity.
- Provider secret bytes never enter Git, Host messages, or test fixtures.
- Consumer directFallback=false and unknown-destination rejection semantics remain unchanged.
- Mechanism health is never promoted to consumer consequence readiness.
- Red before Green at existing public source seams.
- Independent Spec and Standards review is required before integration or cutover.

---

### Task 1: Typed carrier-realization registry

**Files:**
- Create: platform/network/providers/schemas/provider-carrier-realizations-v1.schema.json
- Create: platform/network/providers/surfshark/config/carrier-realizations.json
- Create: platform/network/capabilities/gluetun/external/gluetun.lock
- Create: platform/network/tests/test_provider_carrier_realizations.py
- Modify: platform/network/config/provider-egress.json
- Modify: platform/network/Taskfile.yml

**Interfaces:**
- Consumes: existing ProviderProfile, ClientIdentity, and provider-egress semantic definition.
- Produces: source-only ordivon.network-v2.provider-carrier-realizations contract and realizationRegistryRef.

- [ ] **Step 1: Write the failing public-seam test**

    def test_provider_realization_registry_keeps_active_and_candidate_distinct():
        value = load("providers/surfshark/config/carrier-realizations.json")
        assert value["kind"] == "ordivon.network-v2.provider-carrier-realizations"
        assert value["activeRealizationId"] == "legacy-wireguard-r1"
        candidate = by_id(value)["gluetun-v3.41.3-r1"]
        assert candidate["standing"] == "candidate"
        assert candidate["activationMode"] == "serialized-only"
        assert candidate["productionAuthority"] is False
        assert candidate["concurrentWithActive"] is False

The same module asserts that the registry contains no privateKey, assignedAddress, password, token, or secret byte fields and that both realizations point to the existing provider/client identity descriptors.

- [ ] **Step 2: Run the focused test and verify RED**

    cd platform/network
    python -m pytest -q tests/test_provider_carrier_realizations.py

Expected: FAIL because the realization registry and lock do not exist.

- [ ] **Step 3: Add the minimal typed source contract**

The JSON schema uses additionalProperties=false at root and realization object levels. It admits only active/candidate standings and continuous/serialized-only activation modes.

R1 registry:

    activeRealizationId = legacy-wireguard-r1
    candidateRealizationIds = gluetun-v3.41.3-r1

Gluetun source lock:

    repo=https://github.com/passteque/gluetun.git
    version=v3.41.3
    revision=3d1e20c5551e9cae1f9d938dc7b7214a6987f27e

Add realizationRegistryRef to config/provider-egress.json while retaining current compatibility fields until live cutover.

- [ ] **Step 4: Add Taskfile source validation**

provider:surfshark:identity-contract:validate validates the realization registry, active legacy realization, serialized Gluetun candidate, and official source lock without fetching or installing anything.

- [ ] **Step 5: Run focused and existing provider tests**

    cd platform/network
    python -m pytest -q tests/test_provider_carrier_realizations.py tests/test_provider_egress_definition.py tests/test_provider_identity_split.py tests/test_shared_provider_carrier.py
    task provider-egress:validate
    task provider:surfshark:identity-contract:validate

Expected: all PASS with no live service mutation.

- [ ] **Step 6: Commit candidate slice**

    git add platform/network/providers/schemas/provider-carrier-realizations-v1.schema.json
    git add platform/network/providers/surfshark/config/carrier-realizations.json
    git add platform/network/capabilities/gluetun/external/gluetun.lock
    git add platform/network/tests/test_provider_carrier_realizations.py
    git add platform/network/config/provider-egress.json platform/network/Taskfile.yml
    git add platform/network/docs/UPSTREAM_FIRST_CONVERGENCE_R1.md
    git add docs/superpowers/plans/2026-10-11-network-gluetun-serialized-candidate.md
    git commit -m "network: define upstream carrier realization contract"

---

### Task 2: Source-only Gluetun capability qualification

**Files:**
- Create: platform/network/capabilities/gluetun/README.md
- Create: platform/network/capabilities/gluetun/acceptance/source-contract.sh
- Modify: platform/network/Taskfile.yml
- Test: platform/network/tests/test_provider_carrier_realizations.py

**Interfaces:**
- Consumes: Gluetun lock from Task 1.
- Produces: reproducible source/build qualification only; no VPN credential or live provider effect.

- [ ] **Step 1:** extend the test to require capability:gluetun:source:accept and prove that core:install, core:converge, and production consumer dependencies do not invoke it.
- [ ] **Step 2:** run the focused test and verify RED.
- [ ] **Step 3:** implement source-contract.sh so it clones/fetches the exact revision into a temporary directory, proves the exact HEAD, Dockerfile, and go.mod, and never reads /etc/network-v2/providers, starts systemd network units, or opens a VPN session.
- [ ] **Step 4:** run task capability:gluetun:source:accept and verify PASS with no production state change.
- [ ] **Step 5:** commit as "network: qualify pinned gluetun source".

---

### Task 3: Serialized canary harness, source only

**Files:**
- Create: platform/network/providers/surfshark/acceptance/gluetun-serialized-canary.sh
- Modify: platform/network/Taskfile.yml
- Test: platform/network/tests/test_provider_carrier_realizations.py

**Interfaces:**
- Consumes: realization registry and existing production readiness scripts.
- Produces: a fail-closed effect script that can run only after explicit owner admission; creating the source does not execute it.

Required source fences:

    active realization = legacy-wireguard-r1
    candidate activationMode = serialized-only
    no running Agent Automation workflow using the carrier
    exact current provider preimage captured
    rollback trap installed before active session stop
    candidate stopped before legacy restart
    provider-carrier-ready and production-path run after restore

The harness exits before any effect unless NETWORK_V2_GLUETUN_SERIALIZED_CANARY=AUTHORIZED is present. That value is necessary but not sufficient; all currentness/preimage fences must also pass. No Taskfile dependency invokes this task automatically.

Static gate:

    bash -n providers/surfshark/acceptance/gluetun-serialized-canary.sh
    python -m pytest -q tests/test_provider_carrier_realizations.py

Do not execute the canary in Task 3.

---

### Task 4: Consequence differential contract

**Files:**
- Create: platform/network/providers/surfshark/acceptance/gluetun-differential.sh
- Modify: platform/network/Taskfile.yml
- Test: platform/network/tests/test_provider_carrier_realizations.py

**Interfaces:**
- Consumes: existing provider-carrier-ready, Browserless production-path, Finance, Supply Chain, Model Provider, Discord/X/Claude readiness surfaces.
- Produces: a bounded parity report with no production authority.

The differential invokes existing owner readiness commands rather than duplicating destination logic. It records owner-command exit status and exact candidate/legacy realization IDs. It holds no credentials and performs no financial, account, submission, or other writes.

Test with fixture executables or command injection only. Do not run a production carrier change in Task 4.

---

### Task 5: Review and retirement decision

**Files:**
- Modify: platform/network/docs/UPSTREAM_FIRST_CONVERGENCE_R1.md
- Modify: platform/network/providers/surfshark/README.md

**Interfaces:**
- Consumes: fixed candidate commits and test/evidence receipts.
- Produces: reviewed KEEP / DELETE_AFTER_GATE / HOLD dispositions only.

- [ ] Run platform/network source validation and complete pytest suite.
- [ ] Run independent Standards review for upstream reuse, secret boundaries, naming/source layout, and absence of a new custom controller.
- [ ] Run independent Spec review for single-session enforcement, no implicit production effect, consequence-readiness separation, rollback, and migration-gate coverage.
- [ ] Resolve every executable blocker. Any counterexample keeps cutover HOLD.
- [ ] Publish owner decision. Only the natural Network owner may move Gluetun from candidate to active; until that separate decision, live legacy realization remains unchanged.


---

## Execution revision after Task 2

### Task 3A: Compatibility topology contract — source only

Status: implemented as a candidate slice; production effect remains zero.

Files:
- Create platform/network/capabilities/gluetun/external/gluetun-image.lock
- Create platform/network/capabilities/gluetun/config/serialized-candidate.env
- Create platform/network/consumers/browserless/config/provider-carrier-gluetun-candidate.json
- Create platform/network/capabilities/gluetun/acceptance/compatibility-hop.sh
- Modify platform/network/tests/test_provider_carrier_realizations.py
- Modify platform/network/Taskfile.yml
- Modify platform/network/docs/UPSTREAM_FIRST_CONVERGENCE_R1.md

Decision:

    consumers
      -> existing 10.252.246.2:19680 seam
      -> sing-box compatibility HTTP outbound
      -> host-veth 10.252.246.1:19682
      -> future Gluetun HTTP proxy

The Gluetun container/network namespace owns the eventual VPN/firewall/DNS mechanism. The existing Network-v2 namespace does not receive a new pre-VPN default route.

Validation:
- candidate image index and linux/amd64 OCI digests are pinned;
- non-secret Gluetun environment contains no provider identity material;
- candidate sing-box config has no direct outbound;
- existing consumer-facing listen address/port is unchanged;
- compatibility hop source contains no provider material access and no production unit stop/restart;
- bounded host-veth reachability feasibility passed separately.

### Task 3B: Serialized live canary — still HOLD

Do not implement or run a provider-identity canary until:
1. independent M1/M2/M3A review is resolved;
2. exact container materialization/teardown command is fixed to the pinned image digest;
3. workflow drain/currentness proof is available;
4. rollback preimage and order are executable and reviewed;
5. tool/environment policy admits the bounded canary.

If any condition is missing, keep the legacy active realization unchanged.


### Pre-review hardening after Task 3A

The fixed candidate must additionally satisfy these source-truth fences before independent review:

- the Gluetun realization points to the immutable OCI image lock, while the active legacy realization has no OCI artifact reference;
- source qualification fetches refs/tags/v3.41.3 and proves that the tag resolves to the pinned revision;
- candidate Gluetun runtime disables the extra public-IP lookup and binds its control server to loopback;
- compatibility-hop source is read-only preflight only: no sing-box run, curl, temporary listener, namespace creation, provider secret access, or systemd mutation;
- preflight explicitly reports twoHopExecutionProven=false. A later serialized canary, not source preflight, owns that proof.
