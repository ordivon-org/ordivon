# Ordivon Execution Fabric R1

Status: EF0 contract freeze candidate.

## One-line kernel

Ordivon Execution Fabric is a composable physical-capability substrate. Runtime Kernel owns only durable physical execution truth; Nodes, Providers, Sensors, Authority, Controllers, Workflows and routing compose around it without moving their independent authority into Runtime Core.

## Architectural laws

1. Kernel minimality. Job, Attempt, operation/admission identity, dispatch, physical owner, terminal convergence, recovery classification and evidence binding are Runtime Kernel truth.
2. Capability is not authority. Installed capability describes what can be done. Authority describes whether one principal may activate it against one resource now.
3. Authority is not OS privilege. root, Administrator and SYSTEM are operating-system execution contexts. Ordivon Authority separately carries resource scope, mode, conflict semantics, TTL/budget and evidence policy.
4. Node locality. Each native Runtime node owns its own mutable Registry, Workspace and Artifact state.
5. No shared mutable cross-node Registry. Cross-node transfer uses immutable revisions, digests or provider-native immutable identities.
6. Provider replaceability. Linux systemd/cgroup, Windows Job Object, browser engines, storage and network mechanisms remain Provider realizations rather than Kernel meaning.
7. Controllers own convergence. Repeated observe/compare/act/verify loops live outside Runtime Kernel.
8. Workflows own time. Long-lived sequencing, waiting, retry and compensation do not turn Runtime into a workflow engine.
9. Every physical effect binds evidence. Higher capability does not imply opaque execution.
10. Conflict is configurable. Normal operation may use exclusive write while controlled laboratory campaigns may deliberately select cooperative or adversarial semantics.

## LEGO vocabulary

R1 freezes ten composable kinds:

- Resource — the thing being controlled.
- Capability — an operation class that may be realized against a compatible resource.
- Provider — the physical mechanism that realizes one or more capabilities.
- Sensor — an observer that emits facts without owning convergence.
- Authority — a time/context-bound activation of capability for a principal and resource scope.
- Controller — a reconciler of desired and observed state.
- Workflow — a durable multi-step composition across time.
- Node — a native execution/control domain owning local physical truth.
- Identity — the principal/workload/provider/controller identity participating in an action.
- Evidence — immutable proof references bound to intent, authority, dispatch, ownership and result.

The ordivon-runtime-spi crate is the first machine-checkable expression of the subset that crosses Runtime-facing component boundaries. EF0 does not make Runtime Core depend on this crate and does not change admission or execution. Controller, Workflow, policy and Agent implementations remain outside Runtime Core; they gain Runtime contracts only when a real binding requires one.

## Layering

~~~
Agent Service / Agent Swarms
            |
           Host
            |
 Workflow / Controller / Routing
            |
  Identity / Authority / Policy
            |
       Runtime Kernel
       /           \
 Windows Node    Linux Node
      |              |
 Providers/Sensors/Actuators
       \            /
         Physical world
              |
          Evidence
~~~

## Runtime Kernel owns

- Job identity and durable request/operation identity;
- Attempt identity and state transitions;
- admission commitments;
- exact provider binding frozen at admission where applicable;
- physical dispatch boundary;
- physical owner identity;
- terminal compare-and-set convergence;
- physical recovery classification;
- Artifact and evidence binding.

Kernel does not own provider selection policy, domain semantic completion, long-duration workflow orchestration, security campaign logic or machine-wide desired state.

## Authority vector

Authority is multi-dimensional:

~~~
principal
trustDomain
resourceScope
capabilitySet
osAuthority
mode
conflictMode
enforcement
budget
evidencePolicy
time/lease
~~~

Initial enforcement stages:

- shadow — calculate and record decisions; do not block effects.
- permissive — preserve strong capability while arbitrating declared physical conflicts.
- enforcing — policy decisions actively gate admission/effect activation.

Authority modes include open_control, normal, maintenance, recovery, security, security_lab, emergency and strict.

Conflict modes include observer, shared_read, exclusive_write, cooperative_write and adversarial_lab. High OS privilege and conflict semantics are deliberately orthogonal.

## Node law

Windows and Linux are peer execution/control domains rather than master/worker roles.

A future runtime/windows-main and current/future runtime/linux-archlinux may both offer strong native authority. They do not share one mutable Registry. Capability routing occurs above node-local admission.

## Agent, Controller, Provider and Runtime separation

~~~
Agent      = reason
Controller = converge
Provider   = act
Sensor     = observe
Runtime    = prove physical execution truth
Host       = preserve semantic continuity
~~~

Agents may propose desired state or workflows. Controllers own repeated convergence. Providers own concrete platform mechanics. Runtime owns Job/Attempt evidence rather than semantic success.

## Migration sequence

- EF0 — freeze vocabulary/contracts with no behavior change.
- EF1 — make Runtime Kernel/provider boundary explicit without changing Job/Attempt semantics.
- EF2 — expose Resource/Capability/Provider/Node descriptors as observation.
- EF3 — add Authority Fabric in shadow mode.
- EF4 — normalize OS/browser/storage/network effects behind Providers.
- EF5 — introduce small reconciliation Controllers.
- EF6 — replace monolithic recovery/maintenance scripts with Workflow compositions.
- EF7 — complete independent native Windows and Linux nodes.
- EF8 — route capability requests to Node + Provider outside Kernel.
- EF9 — controlled multi-agent security campaigns with explicit adversarial conflict semantics and complete evidence.

## First real validation targets

1. WSL control-plane recovery: decompose the current Windows recovery supervisor into Providers + Controller/Workflow + Evidence.
2. D-drive VHD compact: decompose drain/trim/offline/exclusive-open/compact/recover/verify into reusable capabilities.
3. Browser fast path: prove browser.navigate can change Provider without changing Runtime Kernel semantics.

## Explicit non-goals

EF R1 does not introduce Runtime consensus, leader election, a distributed Runtime scheduler, a shared cross-OS Registry, a universal mega-controller, a custom durable-workflow engine, custom PKI or a new policy language.
