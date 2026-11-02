# Agent Security LEGO R1

Date: 2026-09-18
Status: CROSS-DOMAIN VALIDATED / STABLE SECURITY LENS / NO MANDATORY SCHEMA EXPANSION
Owner: Ordivon Security capability package
Core standing: NOT PROMOTED INTO SHARED LEGO KERNEL

## 1. Purpose

Agent Security LEGO R1 is a reusable analysis layer for agent applications, IDE agents, harnesses, MCP-backed systems, plugins, browser agents, and long-running automation that possess ambient authority over files, tools, identity, network, or durable state.

The lens exists because a user-visible action such as "send a prompt" can trigger hidden side effects that cross several authority boundaries:

intent -> trigger -> capture -> derive -> persist -> egress -> remote persist -> observe/control.

The framework does not assume malicious software. It asks whether authority, data flow, persistence, control, and disclosure are structurally aligned.

## 2. Activation

Use this lens when at least one of the following is true:

- an agent can read a workspace, repository, browser profile, mailbox, cloud drive, or account;
- a local action can cause outbound network traffic or remote persistence;
- a plugin/tool has broader authority than the immediate user-visible task;
- security depends on where a control is placed in a multi-stage pipeline;
- data can be transformed before crossing a trust boundary;
- a system has hidden sidecars, telemetry, indexing, snapshot, sync, wiki, cache, or upload channels;
- deleting local state may not imply deletion of remote state.

Do not use this lens as a generic vulnerability checklist when the system has no meaningful authority/dataflow problem.

## 3. Core analytical objects

### AS01 — Principal / Identity Authority

Question: Which identity or credential grants access to downstream capabilities?

Examples:
- login token;
- OAuth grant;
- API key;
- local OS identity;
- runtime service account;
- browser profile/session.

Non-claim: authentication does not imply authorization for every downstream data action.

### AS02 — Trigger

Question: What event causes the security-relevant behavior?

Examples:
- prompt submit;
- workspace open;
- task completion;
- timer;
- file change;
- startup;
- explicit user command;
- background retry.

A trigger must be modeled separately from the capability it invokes.

### AS03 — Capture / Read Scope

Question: What data can the component actually read or collect?

Represent as a READ SET, not a vague "workspace access" boolean.

Examples:
- current file;
- source tree;
- .git objects;
- reflog;
- LFS objects;
- ignored files;
- browser storage;
- secrets/config.

### AS04 — Derivation

Question: What new representation is computed from captured data?

Examples:
- archive;
- manifest;
- hash;
- embedding;
- summary;
- index;
- repository wiki;
- screenshot;
- model context.

Derived data remains security-relevant even when raw source is not transmitted.

### AS05 — Local Persistence

Question: What state is retained locally, where, for how long, and under whose authority?

Examples:
- checkpoint;
- cache;
- snapshot;
- retry queue;
- temporary archive;
- credentials;
- audit state.

### AS06 — Egress Path

Question: What data crosses the machine/process/trust boundary, through which path, and to which destination?

Represent as a NETWORK SET plus data class and purpose.

The important distinction is:
- model context egress;
- tool/provider egress;
- telemetry egress;
- snapshot/sync egress;
- update/auth egress.

Do not collapse all network traffic into one channel.

### AS07 — Remote Persistence

Question: What survives remotely after the immediate action completes?

Examples:
- object-store snapshot;
- model/provider logs;
- vector index;
- task artifact;
- conversation attachment;
- remote cache.

Remote persistence is distinct from transit.

### AS08 — Cryptographic / Key Authority

Question: Who can decrypt or otherwise recover protected data?

Encryption-at-rest/in-transit is not equivalent to data minimization.

Record:
- key generator;
- key holder;
- wrapping authority;
- decrypting principal;
- rotation/deletion semantics.

### AS09 — Capability Actuator

Question: Which user/policy control actually stops which stage?

Treat each stage as separately controllable where relevant:

capture -> derive -> persist-local -> egress -> persist-remote -> index/use.

A control that disables indexing but not capture/upload is not a snapshot-off control.

### AS10 — Side-Effect Ledger / Observation

Question: Can the system make the behavior observable without reverse engineering?

Minimum useful event classes:
- FILE_READ;
- FILE_WRITE;
- SNAPSHOT_CREATE;
- ARCHIVE_CREATE;
- DERIVATION_CREATE;
- NETWORK_CONNECT;
- NETWORK_UPLOAD;
- REMOTE_PERSIST;
- SECRET_ACCESS;
- POLICY_DENY;
- RETRY.

Observation does not itself prove semantic legitimacy.

### AS11 — Retention / Deletion Semantics

Question: What event deletes which copy?

Distinguish:
- local deletion;
- conversation deletion;
- workspace deletion;
- account deletion;
- retention expiry;
- remote object deletion;
- derived-index deletion.

Deletion must be modeled as a state transition, not a UI promise.

### AS12 — Disclosure / Mental-Model Contract

Question: Does the user-visible explanation match the real data-flow graph?

Compare:
- what the UI says;
- what policy says;
- what the user action reasonably implies;
- what the implementation actually reads, derives, sends, and persists.

This node detects control-surface and disclosure mismatches without requiring a claim about malicious intent.

## 4. Five explicit sets

Every audited capability should be describable with at least:

```text
READ SET
WRITE SET
DERIVE SET
NETWORK SET
PERSIST SET
```

Optional sixth set when external effects matter:

```text
IRREVERSIBLE EFFECT SET
```

A generic plugin/workload declaration can therefore be reviewed as:

```yaml
read:
  allow: [...]
  deny: [...]

write:
  allow: [...]

derive:
  allow: [...]

network:
  allow: [...]

persist:
  local: [...]
  remote: [...]

effects:
  irreversible: [...]
```

This is an analytical contract. It is not yet a new portable Agent Plugin field or standard.

## 5. Typed security graph

Recommended edge types:

- IDENTITY — a principal/credential binds an action;
- CONTROL — an event or actuator can cause/prevent a transition;
- DATA — information moves between nodes;
- DERIVATION — data is transformed into another representation;
- PERSISTENCE — state is retained across time;
- EGRESS — data crosses a trust/machine boundary;
- OBSERVATION — evidence about state/effect is emitted;
- POLICY — a declared rule constrains another node;
- DISCLOSURE — a user-facing statement describes a behavior.

The important property is typed separation. A single "agent -> cloud" arrow is not sufficient.

## 6. Canonical pipeline

```text
AS01 Identity
   |
   v
AS02 Trigger
   |
   v
AS03 Capture Scope
   |
   v
AS04 Derivation
   |
   +----> AS05 Local Persistence
   |
   v
AS06 Egress
   |
   v
AS07 Remote Persistence
   |
   v
downstream use/index/restore

AS08 Key Authority spans AS04/AS06/AS07.
AS09 Capability Actuator must bind to the exact stage it claims to control.
AS10 Observation should witness relevant side effects.
AS11 Retention/Delete governs persisted copies.
AS12 Disclosure must correspond to the real pipeline.
```

## 7. Failure patterns

### F1 — Ambient Authority Expansion

The system has broad workspace/account authority while the user action appears narrow.

### F2 — Trigger/Intent Mismatch

A benign-looking action triggers additional security-relevant behavior not represented in the user's mental model.

### F3 — Scope Inflation

The capture set is broader than the task-relevant data set.

### F4 — Derived-Data Escape

Raw data appears protected, but embeddings, manifests, archives, summaries, hashes, screenshots, or indexes cross boundaries.

### F5 — Actuator Misplacement

The visible switch controls a downstream stage while upstream capture/egress continues.

### F6 — Hidden Egress Plane

A sidecar/backend channel bypasses the network path the user believes governs the product.

### F7 — Persistence Ambiguity

Transit, cache, object storage, indexes, and backups are conflated.

### F8 — Key-Authority Ambiguity

"Encrypted" is presented as a privacy boundary without identifying who can decrypt.

### F9 — Unobservable Side Effect

The behavior is discoverable only through packet capture, filesystem forensics, or reverse engineering.

### F10 — Disclosure Drift

Policy/UI language and implementation scope diverge.

## 8. Control-theory interpretation

A user-facing toggle is an actuator. It must be attached to the stage that the label implies.

If a control labeled "snapshot off" only changes downstream indexing, the control structure is unsafe because:

reference state: no snapshot leaves machine
actuator location: index/use stage
plant behavior: capture + upload continue

The correction is not merely better wording. Either:
- move the actuator upstream; or
- rename/scope the control precisely; and
- expose separate controls for capture, egress, retention, and downstream use where those are independent capabilities.

## 9. Information-flow interpretation

This lens is compatible with information-flow reasoning without pretending that every flow can be reduced to confidentiality labels.

For each edge record:
- source principal/domain;
- source data class;
- transform;
- destination principal/domain;
- persistence;
- reversibility;
- user/policy authorization;
- evidence.

A useful minimal tuple is:

```text
<source, data-class, transform, destination, persistence, authority, evidence>
```

## 10. STPA interpretation

Security losses can emerge even when every component behaves "as designed."

Candidate losses:
- proprietary data leaves intended trust boundary;
- deleted historical data becomes remotely persistent again;
- a user cannot stop a claimed optional flow;
- an operator cannot determine what data crossed a boundary.

Candidate unsafe control actions:
- trigger capture without task-relevant scope;
- provide upload credentials when egress is disabled;
- label indexing-off as snapshot-off;
- delete local state without deleting remote state;
- retry egress without visible standing.

## 11. Runtime / Agent Plugin implications

Agent Plugin remains a portable assembly boundary. Do not invent private portable fields merely because this lens needs richer security semantics.

Preferred ownership:

```text
Agent Plugin
  -> packages Skill/MCP connection

Skill
  -> teaches procedure

MCP/tool
  -> exposes capability

Runtime/provider/domain owner
  -> owns execution/data/effect truth

Security policy/observer
  -> constrains and witnesses authority + egress
```

Security declarations may initially remain Ordivon-local policy/evidence until an upstream standard naturally owns them.

## 12. Acceptance protocol

A prospective case passes this lens when it can produce:

1. exact system boundary;
2. authority graph;
3. trigger graph;
4. READ/WRITE/DERIVE/NETWORK/PERSIST sets;
5. local and remote persistence map;
6. actuator-to-stage mapping;
7. side-effect observability map;
8. disclosure-vs-implementation comparison;
9. evidence standing for each major claim;
10. non-claims and unresolved questions;
11. at least one falsification test;
12. repair/mitigation routing by responsible node.

## 13. Promotion law

Do not promote AS01-AS12 wholesale into the shared LEGO kernel.

Promotion requires repeated evidence across multiple unrelated systems that omitting one concept causes systematic decomposition or control loss.

Likely promotion candidates to test:
- explicit authority graph;
- trigger as first-class relation;
- READ/WRITE/DERIVE/NETWORK/PERSIST sets;
- actuator placement;
- remote persistence;
- side-effect observability;
- disclosure alignment.

## 14. Stop condition

Stop analysis when:
- all material trust-boundary crossings have typed evidence;
- controls are mapped to exact stages;
- major persistence copies are accounted for;
- remaining unknowns no longer change a concrete architecture/control decision.

Do not continue adding security vocabulary after the model stops changing decisions.

## 15. First prospective validation

Reference case:
- `catalogs/knowledge/lessons/zcode-workspace-snapshot-security-lego-r1.md`
- `catalogs/knowledge/graphs/zcode-workspace-snapshot-security-lego-r1.json`

The ZCode case is used to test whether the lens captures a hidden workspace-snapshot/egress pipeline without relying on motive attribution.


## 16. Cross-system and cross-domain extension

Validation records:
- `catalogs/knowledge/lessons/agent-security-cross-system-destroyer-r1.md`
- `catalogs/knowledge/lessons/agent-security-cross-domain-destroyer-r1.md`

The original AS01-AS12 model survived six coding-agent products and five unrelated execution/effect domains. Cross-domain validation adds six stable analytical dimensions.

### XAS13 — Security Regime Identity

Security claims bind to an exact operating regime rather than a product label.

At minimum record relevant execution location, sandbox/containment mode, permission/policy mode, network posture, persistence mode, delegation mode, and managed constraints.

### XAS14 — Policy Binding Event / Time

A policy must state when it becomes effective.

Record:
- scope;
- binding event;
- effective-from identity/time;
- expiry/revocation where relevant;
- whether the change is retroactive to already-admitted work.

### XAS15 — Authority Propagation

When one component invokes another, authority propagation must be explicit.

Classify as:
- delegated;
- attenuated;
- independent;
- clamped;
- escalatable.

Do not infer child/executor authority from topology.

### XAS16 — Persistence Class Vector

Do not model persistence as one boolean or one retention duration.

Track relevant object classes independently, such as:
- runtime workspace;
- transcript;
- artifact;
- snapshot/cache;
- credential/secret;
- derived index/embedding;
- memory;
- audit record;
- external-provider copy;
- backup/archive.

Each class may have a different owner, retention, deletion, encryption, and recovery law.

### XAS17 — Effect Commit Point / Reversibility Class

Identify the exact operation where a proposal becomes a consequential effect.

Ask:
- what is the last freely reversible state?
- what crosses the commit boundary?
- is the effect idempotent?
- what exact identity fences replay?
- what compensation, cancellation, void, undo, or other reversal exists?

Examples validated cross-domain include provider SEND, external artifact publication, admitted financial write, Game Turn Commit, Gmail send, and Calendar create/update/delete.

### XAS18 — Effect Reconciliation Oracle

A process result or acknowledgement is not automatically authoritative outcome evidence.

Record:
- authoritative result owner;
- exact identity queried;
- states distinguishable by the oracle (pending/committed/absent/failed/unknown);
- whether UNKNOWN can converge safely without repeating the effect.

Validated examples include provider exact-turn read-back, artifact destination digest read-back, venue/account reconciliation, exact Game World/Batch recovery, and provider-native Gmail/Calendar identities/read-back.

## 17. Cross-domain standing

Current standing:
- AS01-AS12: retained as Agent Security analytical objects;
- XAS13-XAS18: cross-domain validated analytical dimensions;
- shared project-plan schema: unchanged.

Shared analytical laws promoted to LEGO Theory:
- REGIME_BOUND_CLAIMS;
- POLICY_BINDING_EVENT;
- EXPLICIT_AUTHORITY_PROPAGATION;
- PERSISTENCE_CLASS_SEPARATION;
- EFFECT_COMMIT_POINT;
- EFFECT_RECONCILIATION_ORACLE.

These laws are activated when relevant. They are not mandatory fields in every project.
