# ORDIVON CORE ELIMINATION R1

Date: 2026-09-19
Status: ACTIVE / destructive-by-default design audit
Source revision: ca9ee9608ce1afbbe4498293ac1efc529686f2d0

## Objective

Attempt to eliminate every Ordivon-specific architectural primitive by replacing it with a mature external standard, protocol, product, or well-established engineering pattern.

Success is not "find the Ordivon kernel". Success is the smallest possible residue, including zero.

## Decision rule

Every local concept receives exactly one disposition:

- DELETE: no independent semantic owner is required.
- REPLACE_WITH_STANDARD: migrate authoritative semantics to an external standard/substrate.
- ADAPTER_ONLY: retain only a thin translation/provider boundary.
- RESIDUAL_CANDIDATE: temporarily survives because no lossless replacement has yet been demonstrated.

A concept is not retained because it has code, tests, historical users, or documentation. Compatibility is migration work, not architectural justification.

## Evidence snapshot

Observed local system on 2026-09-19:

- Host v2: PostgreSQL authority, 2,108 Tasks, 1,838 terminal, 270 open; Doctor healthy.
- Host exposes 13 MCP tools and explicitly separates Host semantic continuity from Runtime physical authority.
- Runtime current Linux node exposes durable Workspace / Job / Attempt / Artifact mechanics and explicit local authority boundaries.
- Runtime repository: 326 tracked files; 115 Markdown, 73 Rust, 43 JSON, 37 Python.
- Harness repository: 581 tracked files; major custom state includes HarnessRun, Assignment, Tool Step checkpoints, WorkingView, skill catalog and Runtime lowering.
- Next repository: 823 tracked files; 397 JSON + 308 Markdown + 111 Python.
- Agent Service currently defines custom AgentDefinition, AgentRevision, AgentInstance, DesiredPlacement, Goal, Task, Assignment, Session, capability advertisements, policy decisions, delivery receipts, evidence bundles, identity proofs, credential bindings, failover/quiescence/replay-safety records, and associated stores/coordinators.

This is enough evidence to reject "concept exists locally" as a reason for keeping it.

## External replacement vocabulary

The elimination pass uses these mature owners first:

- Durable workflow / retries / recovery: Temporal.
- Adaptive knowledge work / case semantics: OMG CMMN; BPMN/DMN where appropriate.
- Desired/observed reconciliation: Kubernetes controller/operator pattern.
- Tool/resource protocol: MCP.
- Agent discovery, communication and collaborative task protocol: A2A.
- Policy decisions: OPA.
- Relationship authorization: OpenFGA.
- Workload identity: SPIFFE/SPIRE; OAuth/OIDC where user/delegated identity is required.
- Event envelope/interchange: CloudEvents.
- Telemetry/correlation: OpenTelemetry.
- Provenance: W3C PROV.
- Data/job/run lineage: OpenLineage.
- Artifact provenance/attestation: SLSA + in-toto.
- Artifact packaging/distribution: OCI artifacts/registries where applicable.
- Source/workspace identity: Git native revision/worktree semantics plus disposable execution environments.
- Effect safety: idempotency keys, transactional outbox/inbox, sagas, reconciliation and provider-native receipts before inventing a new ledger.

## Elimination matrix

| Local concept | Current owner | Preferred replacement | Disposition | Migration proof required |
|---|---|---|---|---|
| Host Task lifecycle | Host | CMMN case/work semantics + Temporal execution | REPLACE_WITH_STANDARD | recover/re-enter same semantic work without Host Task state |
| WorkingCheckpoint | Host | CMMN case file / durable workflow state / domain record | REPLACE_WITH_STANDARD | preserve established/unresolved/constraints without custom checkpoint schema |
| Host task revisions | Host | event-store/version/CAS semantics of chosen substrate | REPLACE_WITH_STANDARD | stale-write fencing and replay tests |
| Host Board | Host | A2A/message/event substrate + disposable projection | REPLACE_WITH_STANDARD | rebuild projection without Board authority |
| task route anchors | Host | stable task/resource identifiers + standard routing/correlation | DELETE | prove routing without deterministic Board anchor |
| attention.delta | Host | event cursor/subscription + exact object re-entry | REPLACE_WITH_STANDARD | no lost/double-consumed navigation |
| Host News | Host | separate application/service | DELETE | zero dependency from work-control path |
| Runtime Workspace abstraction | Runtime | Git worktree/revision + disposable execution environment | ADAPTER_ONLY | source identity and dirty-state parity |
| Runtime Job | Runtime | Temporal Activity/Workflow or provider Job | REPLACE_WITH_STANDARD | interruption/reconnect/retry parity |
| Runtime Attempt | Runtime | Temporal Activity attempt / provider execution attempt | REPLACE_WITH_STANDARD | attempt history and terminal ambiguity parity |
| Runtime reconciliation | Runtime | Temporal recovery + controller pattern | REPLACE_WITH_STANDARD | crash/restart and unknown-outcome suite |
| Runtime WorkflowPlan | Runtime SPI | Temporal/BPMN/CMMN | DELETE | structured multi-step execution parity |
| AuthorityVector / AuthorityLease | Runtime SPI | OPA + OpenFGA + SPIFFE + OS/provider authority | REPLACE_WITH_STANDARD | deny/allow and identity-bound execution tests |
| ProviderDescriptor / CapabilityDescriptor | Runtime SPI | MCP/A2A/Kubernetes/provider-native discovery | ADAPTER_ONLY | discovery remains non-authoritative |
| EvidenceReference | Runtime SPI | PROV/OpenLineage/SLSA/in-toto references | REPLACE_WITH_STANDARD | provenance graph round-trip |
| Runtime Artifact metadata | Runtime | OCI/SLSA/in-toto + object store/CAS | ADAPTER_ONLY | digest, provenance and retrieval parity |
| custom terminal evidence schema | Runtime | provider receipts + OTel + provenance/attestation | ADAPTER_ONLY | preserve exact terminal ambiguity semantics |
| HarnessRun identity/state | Harness | harness-native run + OTel trace + Temporal external continuity | ADAPTER_ONLY | swap harness implementation without semantic loss |
| Harness Assignment | Harness | service/case task assignment or A2A Task | REPLACE_WITH_STANDARD | reassignment/retry history parity |
| Tool Step checkpoint | Harness | Temporal activity/workflow state + MCP/A2A/OTel correlation | REPLACE_WITH_STANDARD | resume after crash at tool boundary |
| WorkingView | Harness | ephemeral context projection | DELETE | rebuild from authoritative sources |
| custom run store | Harness | Temporal/event store/provider-native state | REPLACE_WITH_STANDARD | restart/reconnect parity |
| skill catalog semantics | Harness/Skill MCP | Agent Skills-compatible package metadata + standard registry/signing/scanning | ADAPTER_ONLY | snapshot/fence/trust tests survive |
| custom skill trust vocabulary | Skill MCP | package signing/SBOM/scanning + policy engine | REPLACE_WITH_STANDARD | deny poisoned/untrusted skill without custom trust state |
| AgentDefinition | Agent Service | A2A Agent Card + deployable artifact metadata | REPLACE_WITH_STANDARD | versioned definition interoperability |
| AgentRevision | Agent Service | immutable Git/OCI revision + Agent Card version | REPLACE_WITH_STANDARD | historical revision resolution |
| AgentInstance | Agent Service | workload/deployment instance + SPIFFE identity | REPLACE_WITH_STANDARD | instance identity and restart semantics |
| DesiredPlacement | Agent Service | Kubernetes desired state / scheduler | REPLACE_WITH_STANDARD | convergence/failover tests |
| PlacementReconciler | Agent Service | Kubernetes controller/operator | DELETE | controller parity |
| Goal | Agent Service | CMMN case/milestone or domain objective record | REPLACE_WITH_STANDARD | acceptance semantics remain explicit |
| AgentTask | Agent Service | A2A Task + CMMN/Temporal/domain task | REPLACE_WITH_STANDARD | semantic task != execution attempt preserved |
| Assignment | Agent Service | scheduler/work queue/A2A/case assignment | REPLACE_WITH_STANDARD | who/where/what identities remain separate |
| SemanticSession | Agent Service | A2A context/task/message semantics | REPLACE_WITH_STANDARD | multi-message continuity |
| CapabilityAdvertisement | Agent Service | A2A Agent Card + MCP capabilities | DELETE | discovery parity |
| AgentInterfaceAdvertisement | Agent Service | A2A supported interfaces | DELETE | protocol negotiation parity |
| PolicyDecision store/coordinator | Agent Service | OPA decision + decision log | REPLACE_WITH_STANDARD | policy replay/audit |
| relationship/authority model | Agent Service | OpenFGA | REPLACE_WITH_STANDARD | delegated/group/object relation checks |
| AgentIdentity / identity proof | Agent Service | SPIFFE/SPIRE + OIDC/OAuth as applicable | REPLACE_WITH_STANDARD | cryptographic identity proof |
| credential reference/binding | Agent Service | secret manager + workload/user identity federation | REPLACE_WITH_STANDARD | credentials never enter model context |
| TransportBinding | Agent Service | A2A/MCP/HTTP/gRPC bindings + service discovery | DELETE | route portability |
| DeliveryCoordinator/Receipt | Agent Service | protocol/provider receipts + Temporal orchestration | ADAPTER_ONLY | duplicate delivery and response-loss suite |
| EvidenceBundle | Agent Service | PROV/SACM/SLSA/in-toto bundle/profile | REPLACE_WITH_STANDARD | claim-evidence traceability |
| VerificationRecord | Agent Service | SACM/assurance record + domain verifier result | ADAPTER_ONLY | final semantic decision remains domain-owned |
| TaskCompletionReconciler | Agent Service | domain verification + workflow/case transition | DELETE | process success never implies semantic success |
| quiescence protocol | Agent Service | provider lifecycle + cancellation/termination observation | ADAPTER_ONLY | no duplicate irreversible effect |
| replay-safety decision | Agent Service | idempotency + outbox/inbox + provider receipt reconciliation | ADAPTER_ONLY | response-loss destructive tests |
| execution claim transfer | Agent Service | lease/fencing token/controller ownership pattern | REPLACE_WITH_STANDARD | split-brain/failover tests |
| service event model | Agent Service | CloudEvents + domain schema registry | REPLACE_WITH_STANDARD | exact event correlation and replay |
| Board projection | Agent Service | materialized view over authoritative events | DELETE | destroy/rebuild test |
| custom telemetry | any | OpenTelemetry | DELETE | cross-system trace correlation |
| LEGO lens registry | Next | documentation/Skill/research corpus | DELETE_FROM_CORE | no runtime dependency |
| capability package prose | Next | thin profile over external providers | ADAPTER_ONLY | every capability has external owner |
| Ordivon-specific policy language | any | OPA/Rego | DELETE | policy conformance |
| Ordivon-specific wire protocol | any | MCP/A2A/HTTP/gRPC/CloudEvents | DELETE | protocol conformance |

## Provisional residue

No concept is currently accepted as an irreducible Ordivon primitive.

The only temporary residual research questions are cross-standard composition questions:

1. Canonical identity mapping across case/workflow/agent/execution/provenance objects.
2. Cross-boundary effect reconciliation when an external provider cannot offer idempotency or transactional observation.
3. Semantic completion binding: ensuring execution success cannot be mistaken for domain/claim success.
4. Conformance profiles that state which external semantics must survive adapter replacement.

These are RESIDUAL_CANDIDATE questions, not retained products or object models. They must themselves be eliminated if existing standards/patterns cover them.

## Mandatory conformance tests before deleting local semantics

A replacement is only accepted when the external-first stack passes:

1. Crash after admission, before execution.
2. Crash during execution.
3. Response lost after real external effect.
4. Retry after ambiguous result.
5. Agent/harness replacement mid-project.
6. Provider replacement with stable semantic work identity.
7. Policy deny before side effect.
8. Workload identity rotation.
9. Task reassignment without duplicated irreversible effect.
10. Artifact provenance round-trip.
11. Board/projection destruction and rebuild.
12. Domain verification remains independent from process exit.
13. Historical revision remains resolvable.
14. Observability correlation survives protocol/provider boundaries.
15. No Ordivon-only identifier is required at an external interoperability boundary.

## Immediate deletion priorities

P0:
- Stop creating new Ordivon ontology names when an external owner exists.
- Freeze expansion of Agent Service object vocabulary.
- Treat LEGO registries as research/docs, never kernel.
- Move Host News out of Host core.
- Treat Board as a projection, never authority.

P1:
- Build a translation profile for Task/Run/Attempt/Artifact/Agent identities using CMMN + Temporal + A2A + PROV/OpenLineage.
- Replace custom policy/identity semantics with OPA/OpenFGA/SPIFFE adapters.
- Replace custom event envelope with CloudEvents and telemetry with OTel.
- Define SLSA/in-toto provenance emission for produced artifacts.

P2:
- Run behavioral differential tests between current Host/Runtime/Harness and the external-first candidate.
- Delete local state machines only after parity is demonstrated.
- If parity cannot be demonstrated, record the smallest failing semantic invariant; do not restore the whole subsystem.

## Stop conditions

This audit is complete only when either:

A. Ordivon-specific residue is empty; or
B. every remaining primitive has:
   - a precise semantics,
   - a counterexample showing why mature alternatives fail,
   - executable conformance tests,
   - at least two independent implementations or adapters,
   - measurable value beyond integration convenience.

Until then, "Ordivon core" is a hypothesis, not an architectural fact.
