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

### AuthorityVector

Keeps these dimensions independent:

- principal;
- trust domain;
- resource scope;
- capability set;
- operating-system authority;
- Ordivon orchestration mode;
- conflict mode;
- enforcement stage;
- optional budget;
- optional evidence policy.

### AuthorityLease

Adds activation time, expiry and revocation to an AuthorityVector. R1 is a data contract only; no policy engine or lease store is implied.

### EvidenceReference

Content-addressed proof reference with producer identity. It does not normalize platform-specific evidence into false equivalence.

## Compatibility rule

Adding a descriptor to a node or provider does not authorize execution. Authority descriptors do not imply Runtime admission. Runtime execution remains governed by existing Job/Attempt contracts until a later explicitly accepted EF phase wires shadow/enforcement semantics into admission.
