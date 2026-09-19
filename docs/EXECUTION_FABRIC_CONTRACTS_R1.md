# Execution Fabric Contracts R1

Status: EF0 machine-contract companion.

## Ownership

ordivon-runtime-spi contains portable data contracts only. It must stay free of:

- process spawning or termination;
- Runtime Registry reads/writes;
- controller reconciliation loops;
- provider implementation;
- scheduling/routing decisions;
- policy evaluation;
- network I/O.

This boundary permits Host, Harness, Workstation, future Agent Service and Runtime to share names without sharing authority. The crate is not Runtime Kernel state: Core does not depend on it in EF0, and descriptor presence cannot authorize or classify an effect.

Not every architectural LEGO kind needs a Runtime wire object. Sensor, Controller and Workflow implementations remain in their owning systems until a concrete Runtime binding is required; EF0 deliberately avoids creating a generic workflow/controller framework merely to mirror the architecture diagram.

## Stable contract families

### FabricId

Opaque slash-friendly logical identity. Namespace meaning remains owner-defined.

Examples:

~~~
machine/windows-main
runtime/linux-archlinux
provider/windows/job-object
capability/browser.navigate
agent/windows/red/03
~~~

### ResourceDescriptor

Describes one addressable resource, its kind, optional native node and zero or more physical conflict domains.

### CapabilityDescriptor

Describes an operation class and compatible resource kind. observationOnly classifies semantic observation; it is not an authorization statement.

### ProviderDescriptor

Binds a provider identity to a node/platform and the capabilities it can physically realize.

### NodeDescriptor

Projects native control-plane identity, trust domain, providers, capabilities and available OS authority contexts.

### Identity / authorization boundary — superseded

The former AuthorityVector, AuthorityLease, AuthorityEffectCandidate and
AuthorityShadowDecision contracts were retired on 2026-09-19.

They mixed workload/principal identity, authorization, OS privilege, resource conflict,
orchestration mode, budget and evidence policy into one Ordivon-native structure while
production configured no leases and the evaluator only emitted non-enforcing shadow telemetry.

Standards-first routing is now:

- workload identity / trust-domain semantics -> SPIFFE/SPIRE when deployed;
- delegated HTTP authorization -> OAuth and its current security BCPs;
- policy decision -> OPA (or another explicit PDP), with enforcement at the natural PEP;
- OS execution privilege -> Runtime provider contracts (ExecutionProfile, WindowsAuthority);
- resource concurrency/conflict -> the resource/execution coordinator, not identity/authentication;
- semantic ownership -> the domain bounded context, not an authorization token.

NodeDescriptor no longer carries a local trustDomain field. SPIFFE trust-domain semantics
must come from a real SPIFFE identity deployment, not an Execution Fabric label.
The former authorityContexts field is now executionContexts because it describes concrete
OS/provider execution contexts rather than authorization.

### EvidenceReference

Content-addressed proof reference with producer identity. It does not normalize platform-specific evidence into false equivalence.

## Compatibility rule

Adding a descriptor to a node or provider does not authorize execution. Authority descriptors do not imply Runtime admission. Runtime execution remains governed by existing Job/Attempt contracts until a later explicitly accepted EF phase wires shadow/enforcement semantics into admission.


## Provider execution locality versus resource-home locality

ProviderDescriptor.nodeId names the node on which the Provider executes. It does not imply that
the Provider may only control resources homed on that node.

ProviderDescriptor.targetNodeIds is an explicit cross-node reachability declaration:

- an empty set means local-node-only;
- the Provider's own node is always reachable;
- any additional resource-home node must be named explicitly;
- resolver binding fails closed for unknown target nodes.

This distinction is required for recovery paths such as a Windows control-edge Provider operating
on Linux services inside WSL after the Linux Runtime control plane is unavailable.
