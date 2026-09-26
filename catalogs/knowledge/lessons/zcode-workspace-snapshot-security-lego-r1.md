# ZCode Workspace Snapshot — Agent Security LEGO Case R1

Date: 2026-09-18
Status: PROSPECTIVE CASE STUDY R1
Method: Agent Security LEGO R1
Primary public source: https://blog.ferstar.org/en/posts/zcode-silent-workspace-snapshot-upload/
Source boundary: This Ordivon record models the public reverse-engineering report and previously reviewed public product/privacy material. Ordivon has not independently reproduced ZCode's behavior on a local ZCode installation in this case. Claims are therefore separated into reported observation, static reverse-engineering evidence, inference, and unresolved questions.

## 1. One-sentence kernel

The security-relevant structure is not merely "an AI IDE uploads code." It is a workspace-authority pipeline in which a narrow user action may trigger broad repository capture, derivation into a snapshot, encrypted egress through a side channel, and remote persistence while visible controls may govern only downstream use rather than upstream capture/egress.

## 2. System boundary

In-scope conceptual components:

- user and visible ZCode UI;
- authenticated ZCode desktop process;
- workspace/repository;
- snapshot/capture subsystem;
- local checkpoint/snapshot state;
- encryption/key-wrapping logic;
- ZCode backend credential service;
- object-storage upload path;
- callback/registration path;
- indexing/wiki/downstream server features;
- user-facing privacy/settings controls.

Out of scope for this case:

- proof of malicious intent;
- legal judgment;
- proof that every ZCode version/platform behaves identically;
- proof that every attempted snapshot reached remote storage;
- server-side implementation not observable from public evidence.

## 3. Evidence classes

### R — Reported runtime observation

The public report describes:
- local snapshot/checkpoint state;
- large encrypted archive generation;
- repeated capture attempts;
- network connections associated with the snapshot flow.

Standing: useful direct report, not independently reproduced by Ordivon.

### S — Static reverse-engineering evidence

The report describes code paths in the packaged application for:
- snapshot creation;
- upload-credential request;
- server-provided RSA public key;
- AES encryption;
- object-storage upload;
- callback/registration behavior.

Standing: strong implementation evidence if the analyzed build matches the report; still version-specific.

### I — Inference

Examples:
- server-side possession of corresponding decryption authority;
- user mental-model mismatch;
- likely downstream indexing/wiki use.

Standing: must remain explicitly inferential unless separately evidenced.

### U — Unresolved

Examples:
- retention duration;
- exact deletion semantics;
- exact server-side access policy;
- whether every captured artifact is successfully uploaded;
- exact behavior in current/latest build.

## 4. Agent Security LEGO mapping

### AS01 — Principal / Identity Authority

Reported structure:
authenticated client identity appears to gate access to snapshot/upload backend capabilities.

Security question:
does login authority implicitly grant snapshot/egress authority, or is there a separate explicit grant?

Risk pattern:
IDENTITY AUTHORITY -> DATA AUTHORITY conflation.

### AS02 — Trigger

Reported triggers include prompt-related and task-completion-related capture paths.

Security question:
is "send prompt" a pure inference action or a compound capability invocation that also triggers workspace capture?

Risk pattern:
TRIGGER / USER-INTENT mismatch.

### AS03 — Capture / Read Scope

Reported snapshot manifests include broad repository state and, in the reported sample, substantial .git content.

Relevant classes:
- current source;
- repository metadata;
- history objects;
- reflog;
- LFS data.

Security question:
what is the exact inclusion/exclusion law for ignored files, deleted-history objects, secrets, and repository internals?

Risk pattern:
SCOPE INFLATION.

### AS04 — Derivation

Reported transforms:
workspace/repository -> manifest/archive -> encrypted snapshot.

Security significance:
the snapshot is a new durable representation with different lifecycle and access semantics from the original repository.

### AS05 — Local Persistence

Reported local checkpoint/snapshot state provides retry and continuity.

Security question:
what is retained locally after success/failure and what event clears it?

Risk pattern:
persistent retry state can outlive the user action.

### AS06 — Egress Path

Reported flow separates ordinary model interaction from a snapshot/object-storage path.

Conceptual route:

client -> ZCode backend credential service -> object storage -> callback/registration.

Security significance:
network governance must model sidecar/backend channels separately from model API traffic.

Risk pattern:
HIDDEN EGRESS PLANE.

### AS07 — Remote Persistence

The architecture supports remote object persistence if upload succeeds.

Unresolved:
- retention duration;
- storage class;
- replication/backups;
- deletion propagation;
- whether indexing-off changes storage.

Risk pattern:
PERSISTENCE AMBIGUITY.

### AS08 — Cryptographic / Key Authority

Reported design:
- client generates/uses symmetric encryption for archive;
- symmetric key is wrapped using server-provided RSA public key.

Supported conclusion:
the architecture is compatible with server-side decryption authority.

Non-claim:
this does not by itself establish malicious intent or a unique product purpose.

Risk pattern:
KEY AUTHORITY must be named explicitly; "encrypted" is not equivalent to "server cannot read."

### AS09 — Capability Actuator

The report argues that visible settings for experience optimization and repository snapshot indexing do not map cleanly to capture/egress suppression.

Security question:
which stage does each setting actually control?

Required actuator map:

capture?
derive?
local persist?
credential request?
upload?
remote persist?
index/use?

Risk pattern:
ACTUATOR MISPLACEMENT.

### AS10 — Side-Effect Ledger / Observation

The reported behavior required filesystem/network/reverse-engineering inspection.

Security question:
could a normal user inspect:
- snapshot created;
- files/classes included;
- bytes uploaded;
- destination;
- retry state;
- remote persistence standing?

Risk pattern:
UNOBSERVABLE SIDE EFFECT.

### AS11 — Retention / Deletion Semantics

Unresolved:
does deletion of a conversation/workspace/account delete:
- local snapshot;
- object-store snapshot;
- downstream index/wiki;
- backups/derived state?

Risk pattern:
LOCAL DELETE != REMOTE DELETE.

### AS12 — Disclosure / Mental-Model Contract

The core test is not motive. It is alignment among:
- user-visible action;
- product settings;
- privacy/product language;
- actual implementation scope.

Risk pattern:
DISCLOSURE DRIFT if narrow interaction language coexists with broad ambient workspace replication.

## 5. READ / WRITE / DERIVE / NETWORK / PERSIST sets

### READ SET

Reported/possible:
- workspace source;
- repository metadata;
- .git objects;
- reflog;
- LFS objects.

Unknown:
- exact ignore/deny rules;
- secret-file handling;
- parent-directory traversal;
- symlink behavior.

### WRITE SET

Reported/possible local writes:
- checkpoint state;
- archive/snapshot artifact;
- retry metadata.

### DERIVE SET

- manifest;
- compressed archive;
- encrypted snapshot;
- hashes/identifiers;
- downstream index/wiki material where enabled.

### NETWORK SET

- ZCode backend credential/registration service;
- object-storage endpoint;
- ordinary model/provider paths are a separate plane.

### PERSIST SET

Local:
- checkpoint/retry/snapshot state.

Remote:
- object storage when upload succeeds;
- possible downstream index/wiki state.

Exact retention remains unresolved.

## 6. Typed dataflow graph

```text
User action
   |
   | CONTROL
   v
Capture trigger
   |
   | CONTROL
   v
Workspace reader
   |
   | DATA
   v
Repository scope (.git may be included)
   |
   | DERIVATION
   v
Manifest / archive
   |
   | PERSISTENCE
   +------> local checkpoint/retry state
   |
   | DERIVATION + KEY AUTHORITY
   v
Encrypted snapshot
   |
   | EGRESS
   v
Object storage
   |
   | PERSISTENCE
   v
Remote snapshot
   |
   | CONTROL/DATA
   v
registration / index / wiki / downstream use
```

Controls/settings must be overlaid on the exact node they govern; their label is not accepted as proof of scope.

## 7. Control-theory reading

Reference state a user may reasonably intend:
"do not create/upload a repository snapshot."

Potential observed control:
"do not index repository snapshot."

If upstream capture/egress still occurs, the actuator is downstream of the controlled variable.

This is a structural control mismatch even if every component is functioning exactly as implemented.

## 8. STPA-style losses and hazards

### Losses

L1 proprietary or historical code crosses an unintended trust boundary.
L2 deleted/obsolete sensitive history becomes remotely persistent again.
L3 operator believes a flow is disabled while capture/egress continues.
L4 operator cannot reconstruct what data crossed the boundary.
L5 deletion action leaves remote or derived copies behind.

### Hazards

H1 broad capture is triggered by a narrow user action.
H2 upload credentials are issued when the user believes remote replication is disabled.
H3 .git/history is included without a task-relevance or explicit-scope constraint.
H4 local retry silently reattempts a previously failed egress.
H5 downstream controls are presented as upstream controls.
H6 remote deletion/retention state is not observable.

## 9. Falsification tests

The case becomes much stronger if tested prospectively with a synthetic repository.

Suggested repository fixture:
- current file;
- committed secret then deleted in later commit;
- uncommitted file;
- ignored file;
- reflog-only operation;
- LFS object;
- branch not pushed;
- symlink edge case.

Factorial controls:
- logged in / logged out;
- prompt / no prompt;
- indexing on / off;
- experience optimization on / off.

Measure separately:
- capture;
- manifest membership;
- archive creation;
- credential request;
- bytes sent;
- object-store success;
- callback/registration;
- downstream index/use.

The exact status of a single large failed upload must not be conflated with successful remote persistence.

## 10. Repair / mitigation routing

If scope is excessive:
-> fix AS03 capture rules; minimize workspace presented to agent.

If derived data escapes unexpectedly:
-> fix AS04 derivation policy and declaration.

If network plane is hidden:
-> fix AS06 egress mediation/observability.

If remote retention is ambiguous:
-> fix AS07/AS11 lifecycle and deletion contract.

If server key authority is misunderstood:
-> fix AS08 disclosure and key ownership.

If a toggle controls the wrong stage:
-> fix AS09 actuator placement or label/scope.

If behavior is only visible through forensics:
-> fix AS10 side-effect ledger.

If UI/policy and implementation differ:
-> fix AS12 disclosure alignment and/or implementation.

## 11. Ordivon transfer

This case suggests concrete Ordivon controls without copying ZCode's architecture:

1. Every high-authority provider/tool should have explicit READ/WRITE/DERIVE/NETWORK/PERSIST sets.
2. Runtime/provider effects should emit side-effect evidence for material egress/persistence.
3. Egress should be mediated or at least attributable by capability + destination + data class.
4. Remote persistence should be a first-class state, not inferred from successful process exit.
5. Controls should bind to exact stages.
6. Encryption evidence should include key authority.
7. Agent Plugin remains an assembly boundary; security semantics stay with Runtime/provider/policy owners unless an upstream standard owns them.

## 12. Promotion candidates

This single case supports testing, not promotion.

Candidates:
- TRIGGER as a first-class security relation;
- DERIVE SET beside READ/WRITE;
- EGRESS plane separation;
- REMOTE_PERSIST as a distinct state;
- ACTUATOR_PLACEMENT;
- SIDE_EFFECT_LEDGER;
- DISCLOSURE_ALIGNMENT.

Promote only after repeated cross-domain evidence.

## 13. Non-claims

This record does not establish:
- malicious intent;
- legality/illegality;
- universal behavior across all versions/platforms;
- successful upload of every attempted snapshot;
- exact server retention;
- exact server-side access;
- that encryption is weak;
- that repository snapshotting is inherently illegitimate.

The claim is narrower: the reported architecture is a strong prospective case for modeling ambient workspace authority, hidden side effects, egress, persistence, and control placement as separate LEGO nodes.
