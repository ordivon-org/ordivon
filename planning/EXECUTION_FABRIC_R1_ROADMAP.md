# Execution Fabric R1 Roadmap

## EF0 — Contract freeze

Deliverables:

- ordivon-runtime-spi data-only crate;
- machine-checkable Resource, Capability, Provider, Node, Authority, Conflict and Evidence contracts;
- Execution Fabric architecture and ownership laws;
- no Runtime Core dependency on the new crate;
- no live execution behavior change.

Acceptance:

- SPI unit tests pass;
- full existing workspace test suite passes;
- git diff check passes;
- no service restart or deployment is performed.

## EF1 — Kernel/provider boundary

Goal: reduce direct platform knowledge in Runtime Kernel without changing public behavior.

Candidate cuts, in preference order:

1. extract provider contract/snapshot types that are already durable execution commitments;
2. isolate provider-neutral dispatch/observation calls behind one Core-owned seam;
3. leave Linux and Windows evidence platform-specific rather than forcing false equivalence.

Gate: current transactional Runtime fixtures must remain green.

Current EF1 slice (2026-09-18):

- engine physical dispatch now crosses a private `physical_provider` facade instead of calling Linux/Windows raw dispatch functions directly;
- the facade is intentionally mechanical only and does not own provider selection, policy, workflow, retry, or generic effect semantics;
- `ordivon-runtime-spi` contract tests: 5/5 PASS;
- execution-fabric boundary test: 1/1 PASS;
- Runtime Core fast regression: 231/231 PASS with the pre-existing long-running
  `registry_reference_model_properties::request_identity_and_terminal_winner_match_reference_model`
  property test explicitly filtered;
- the unfiltered Core run reached that property test after all prior tests passed, then hit the
  120-second execution Gate before that property test completed; this is recorded as
  NOT-RUN-TO-COMPLETION, not as a full-suite PASS;
- `cargo fmt --all -- --check`: PASS.

## EF2 — Observation model

Project ResourceDescriptor, CapabilityDescriptor, ProviderDescriptor and NodeDescriptor from current real Runtime configuration. Observation is descriptive only.

Gate: descriptor output cannot grant authority or change admission.

Current EF2 slice (2026-09-18):

- `runtime.describe` projects an additive `executionFabric` observation from existing `RuntimeCapabilities`;
- the projection reports current Runtime node identity, configured execution-target resources,
  execution capabilities, current provider snapshots, and observed Windows authority contexts;
- the projection carries `descriptiveOnly=true`, `grantsAuthority=false`, and
  `selectsProvider=false`;
- Runtime Core does not depend on `ordivon-runtime-spi`; projection stays in the MCP adapter layer;
- no AuthorityLease is created and no admission/dispatch path reads the projection;
- MCP regression: 55/55 PASS;
- SPI contracts: 5/5 PASS;
- execution-fabric boundary test: 1/1 PASS;
- `cargo fmt --all -- --check` and `git diff --check`: PASS.

## EF3 — Authority shadow

Introduce AuthorityVector and AuthorityLease evaluation in shadow mode.

Required output per candidate effect:

- wouldAllow;
- conflict classification;
- authority mode;
- OS authority context;
- matching resource/capability scope;
- evidence policy identity.

Gate: shadow decisions never block or alter existing effects.

Current EF3 contract slice (2026-09-18):

- SPI defines AuthorityEffectCandidate and AuthorityShadowDecision;
- pure shadow evaluation compares active leases against exact trust-domain/resource scope,
  principal, capability, OS authority, mode, and conflict mode;
- overlap is classified as none, shared observation, cooperative, exclusive, or adversarial;
- R1 deliberately uses exact resource-scope overlap only; conflict-domain expansion remains a
  later Resource/Controller concern;
- evaluator performs no I/O, mutation, admission, dispatch, renewal, revocation, or policy-provider call;
- the evaluator is not wired into Runtime admission, so a false wouldAllow result cannot block an effect;
- SPI tests: 8/8 PASS.

EF3b live-shadow telemetry slice (2026-09-18):

- each execution MCP surface (workspace.exec, workspace.execBound,
  workspace.execBoundTrusted, workspace.execPlan) derives an AuthorityEffectCandidate from
  the actual bound Runtime execution request before admission;
- candidate projection binds principal, workspace resource scope, execution capability,
  requested Linux execution profile or Windows authority, open_control mode, and
  observation-only exclusive_write conflict semantics;
- the candidate is evaluated against an operator-supplied in-memory shadow lease set and
  appended to the existing Runtime trace JSONL with the decision and overlap classification;
- production configuration currently supplies an empty lease set, so this is telemetry only;
- a false wouldAllow, evaluator failure, malformed candidate, poisoned trace lock, or trace
  write failure cannot veto, alter, or replace the Runtime execution call;
- MCP regression: 57/57 PASS;
- SPI contracts: 8/8 PASS;
- execution-fabric boundary: 1/1 PASS;
- Runtime Core fast regression: 231/231 PASS with the known long-running property test filtered;
- cargo check, cargo fmt --check, and git diff --check: PASS.

## EF4 — Provider normalization

Migrate physical effects one family at a time:

- Linux process/systemd;
- Windows Job Object/process;
- service lifecycle;
- browser;
- storage;
- network.

Each migration must prove provider replacement does not alter Runtime Job/Attempt truth.

Current EF4 process-lifecycle slice (2026-09-18):

- physical_provider now owns the Engine-facing process-owner observation seam for both Linux
  systemd/cgroup execution and Windows launcher/Job Object execution;
- Linux provider observation returns exact persisted SupervisorIdentity plus current
  SupervisorObservation assembled from systemd, boot, PID-start identity, and result facts;
- Windows provider observation wraps exact launcher PID + process-creation identity observation;
- Linux terminal-unit release now also crosses the physical_provider seam;
- Engine no longer directly calls observe_windows_launcher_owner, supervisor_identity(attempt),
  or release_terminal_unit for these lifecycle paths;
- this deliberately does not introduce a universal provider trait, scheduler, provider selection,
  evidence normalization, or cross-platform false equivalence;
- execution-fabric boundary tests: 2/2 PASS;
- Runtime Core fast regression: 231/231 PASS with the known long-running property test filtered;
- MCP regression: 57/57 PASS;
- SPI contracts: 8/8 PASS;
- cargo check, cargo fmt --check, and git diff --check: PASS.

## EF5 — Controller fabric

Introduce small reconcilers with explicit desired/observed state. Initial controllers:

- RuntimeHealthController;
- WSLController;
- ProviderHealthController.

No mega-controller.

Current EF5 provider-health preview slice (2026-09-18):

- SPI defines ControllerReconcileDisposition, ProviderAvailability,
  ProviderHealthObservation, ControllerPreview, and pure preview_provider_health;
- controller preview explicitly separates desired state, observed state, disposition,
  and reason code;
- dispositions are converged, action_required, and observation_incomplete;
- runtime.describe.executionFabric now projects one ProviderHealthController preview for
  each configured execution target;
- an available local-linux provider projects converged;
- a configured but unavailable provider projects action_required;
- incomplete provider observation projects observation_incomplete;
- the controller preview does not execute, acquire authority, choose a provider, retry,
  wait, mutate Runtime state, or claim semantic completion;
- static action-surface audit: CONTROLLER_PREVIEW_NO_ACTION_SURFACE=PASS;
- SPI tests: 11/11 PASS;
- MCP regression: 58/58 PASS;
- execution-fabric boundary tests: 2/2 PASS;
- Runtime Core fast regression: 231/231 PASS with the known long-running property test filtered;
- cargo check, cargo fmt --check, and git diff --check: PASS.

## EF6 — Workflow composition

Use two existing complex flows as forcing functions:

1. WSL control-plane recovery;
2. D-drive VHD compact.

Replace bespoke orchestration with reusable capabilities/providers/controllers while retaining exact safety/evidence gates.

## EF7 — Dual native nodes

Complete runtime/windows-main and runtime/linux-archlinux as independent node-local authorities with separate mutable Registries and Workspaces.

## EF8 — Routing

Select Node + Provider above Runtime admission from capability requirements, health, load, authority, trust and cost.

## EF9 — Security campaigns

On owned/isolated resources, support explicit Security Lab campaigns with configurable conflict semantics:

- observer;
- shared-read;
- exclusive-write;
- cooperative-write;
- adversarial-lab.

Red, Blue, Observer, Referee and Recovery agents may hold distinct high-authority leases while Evidence records every effect and response.
