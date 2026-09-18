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

## EF2 — Observation model

Project ResourceDescriptor, CapabilityDescriptor, ProviderDescriptor and NodeDescriptor from current real Runtime configuration. Observation is descriptive only.

Gate: descriptor output cannot grant authority or change admission.

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

## EF4 — Provider normalization

Migrate physical effects one family at a time:

- Linux process/systemd;
- Windows Job Object/process;
- service lifecycle;
- browser;
- storage;
- network.

Each migration must prove provider replacement does not alter Runtime Job/Attempt truth.

## EF5 — Controller fabric

Introduce small reconcilers with explicit desired/observed state. Initial controllers:

- RuntimeHealthController;
- WSLController;
- ProviderHealthController.

No mega-controller.

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
