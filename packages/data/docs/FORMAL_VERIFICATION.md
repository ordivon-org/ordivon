# Data Formal Verification — property-first, consumer-bound

This is a **scoped method and evidence map**, not a new verification calculus,
registry, security policy, or claim of universal correctness. The canonical
Recursive LEGO R2.1 contracts and shared formal toolchain already exist at
`.agents/skills/recursive-lego-calculus/SKILL.md` and `tools/formal/`.

## Current proof chain

| Stage | Source | Proven or observed | Explicit non-claim |
| --- | --- | --- | --- |
| Specification | `formal/DataProduct.lean` | Optional digest observations, selected admission, exact output-port (name, optional version) abstract selection/frame law, and `(id, version)` product identity uniqueness | Python selector equivalence, source bytes and domain factual truth |
| Model and proof | Lean 4.35 kernel | Missing digest => UNKNOWN; VERIFIED requires two matching observations; FALSIFIED requires distinct observations; a unique product registry stays unique on admission | Python installed-code correctness |
| Implementation candidate | `src/ordivon_data/verification.py` | Pure `digest_verdict` with PEP 316 contracts; CrossHair 0.0.112 / Z3 searches symbolic executions | CrossHair bounded search is not a theorem |
| File/consumer refinement | `src/ordivon_data/catalog.py` and `tests/test_catalog.py` | Real file SHA-256 read-back, deliberate digest mismatch, unavailable/out-of-scope UNKNOWN; product ID-version reject | Atomicity against concurrent file changes; universal URI/JSON-LD semantics |
| Native consumer | `studies/data-lifecycle/tests` + domain-specific consumers | Selected frozen Data Lifecycle, Capital/Finance, Episode and Artifact contracts | Live finance API freshness, scientific causal validity, external distribution rights |

Formal command: `mise run data:formal:verify`.
Native integration: `mise run data:verify`.

### Selected-port refinement (R1)

`selectedAdmissible` proves that a requested nonempty list of abstract
observations cannot pass if any requested verdict is UNKNOWN or FALSIFIED.
Its *input list is assumed already selected by exact product/version/port
identity*; the theorem does not prove that Python's lookup is correct.
The implementation is `scripts/inspect_federation.py --require-port`,
with a real CLI counterexample in `tests/test_odps_projection.py`:
the selected manifest is VERIFIED, an unrelated Parquet port is FALSIFIED,
selected exit is 0, both findings remain visible, while whole-catalog and
ungated inspection exit 2. A selected mismatch still exits 2 and a missing
selected port still exits 3. The Research consumer verifies manifest bytes
and an independent analysis receipt; it never infers business acceptance
from a Data CLI exit. This separates abstract proof, implementation
behavior, producer evidence, and downstream semantic acceptance.

### Version-qualified Research refinement (R2)

`exactPortVerdict` in `formal/DataProduct.lean` now models exact output
selection on `(name, Option version)`: a unique matching entry yields its
verdict, missing/duplicate matches yield no admissible verdict, and adding an
entry with an unrelated key preserves the selected result. It is an abstract
finite-list proof, **not** an automatic refinement proof of Python.
`src/ordivon_data/local_evidence.py` gives a consumer the optional
`port_version` field; unversioned callers retain name-only selection when
unique. The Research `deliver_research.py` consumer independently requires
manifest port `1.0.0`, and selects the matching projected `dcat:version`.
Native negative tests demonstrate that replacing v1 by v2 rejects the input,
while adding same-name v2 alongside a valid v1 does not block v1.
No claim of physical immutability, rights, generalization or Finance adoption.
The formal task explicitly uses Ordivon's existing pinned Lean tool group and
CrossHair's standard PEP 316 implementation; no private theorem kernel or DSL.

The Lean proof output depends only on Lean's ordinary `propext` axiom; there
are no `sorry` assumptions. It proves the stated **abstract** model under
a total, exact digest-equality relation. Real SHA-256 digest values are modeled
abstractly: digest equality proves only hash equality, not metaphysical byte
identity, origin authenticity, producer authorization, or permission to publish.

### Shared local byte observation refinement

Producer binding and catalog inspection share one descriptor-relative,
no-symlink local file observation. Catalog discovery maps a failed observation
or malformed file URI to reason-bearing UNKNOWN without manufacturing an
observed digest. Producer binding remains strict admission and preserves
typed I/O failure behavior for existing Research consumers. Exact selected
port admission is independent of unrelated malformed access URIs; global
admission still requires every relevant distribution to be verified.
Structural and conflicting checksum binding errors remain validation errors.

The native directory-replacement and in-place modification counterexamples
exercise the descriptor boundary. This is not a full refinement proof of
filesystem immutability, later reads, mount changes, or durable retention.

### Git SourceCut refinement boundary

An exact Git commit identifies the metadata tree; the native reader resolves
the revision once, rejects non-regular ODPS Git entries and bounded input
violations, and reads blobs by object ID with replacement objects disabled.
Committed discovery is local-only: missing promisor trees/blobs or native
diagnostics leave the cut unestablished, never a partial successful
projection. Explicit Git acquisition is a separate operator effect.
Tests exercise index/worktree mutation, prior-version replay, foreign
Git environment redirection, exact checkout-root binding, local-only
partial-clone rejection/replay and real CLI projection. This qualifies metadata source selection, not physical local
distribution immutability, Git hash collision resistance, or a full
Git-to-Lean refinement proof.

The blob read-back additionally checks the Git object identity of the exact
returned bytes using native `git hash-object --no-filters --stdin` (without
`-w`). Equal length and a successful `cat-file` are insufficient: the native
SHA-1 and SHA-256 disposable-repository counterexamples replace a loose blob
with different same-length ODPS metadata under its old object name. Both
must be rejected, and restoring the original bytes restores the observation.
This is a bounded blob-identity check, not a full commit/tree integrity audit,
a proof of cryptographic collision resistance, or a guarantee of availability.
The native hash operation is local-only; no new objects are written.

The R9 exact-cut refinement additionally obtains the resolved commit/root
tree and every distinct tree traversed by native Git. The local-only
`cat-file --batch-check` response must match the requested ordered OIDs,
kinds and bounded sizes before `--batch` contents are requested. Native Git
supplies framing/traversal; the standard library hashes the exact canonical
Git header and returned bytes in the repository's object format. The commit
must name the resolved root tree. The batch is limited to 20,000 objects and
8 MiB of declared contents plus framing; this is a preflight bound, not an
OS memory guarantee during a concurrent object mutation.

Disposable SHA-1/SHA-256 repositories demonstrate that static nested-tree
corruption can redirect a valid ODPS Blob under an old commit. Native
regression and batch framing negatives reject it while valid cuts, including
local-only partial clones with available objects, retain the existing
consumer contract. This assumes quiescent Git storage across commands; it
is not an atomic Git snapshot, whole-repository fsck, proof of collision
resistance, authentication of the source publisher, or physical-data truth.
R10 extends the same native batch plan to distinct selected ODPS Blob OIDs.
All commit/tree/blob headers must pass before the content batch, including
the existing nonempty per-Blob 2 MiB limit. The 8 MiB declared frame limit
now covers the combined source cut (not only commit/tree objects); larger
cuts fail closed and require a separately qualified partitioning policy.
The native `hash-object --no-filters --stdin` check remains for each distinct
selected Blob. Return values preserve every original sorted source path,
including duplicate contents; no producer identities are deduplicated.
The plan and bytes are invocation-local; no persisted evidence cache.
Generated framing tests exercise arbitrary binary payloads in both native
Git object formats and single-byte changes, complementing disposable
native repositories and missing-promisor-object tests.

R11 replaces the single combined 8 MiB content request with a complete
header preflight followed by maximal contiguous batches of at most 8 MiB
declared frame bytes. The cut admits at most 64 MiB of declared frames
and 20,000 distinct objects; the per-Blob nonempty 2 MiB limit is unchanged.
A single frame must fit its batch. The first batch alone must verify the
commit/root relation; every batch independently verifies exact framing,
kind and object identity. The original sorted path multiplicity is restored
only after every batch and every native Blob hash succeeds. No partial
observation is returned after a later failure. Header and retained-byte
limits are declared budgets, not RSS bounds or concurrency isolation.

For positive ordered frame sizes, a maximal prefix leaves a suffix no
longer than any other legal first batch. Induction gives the minimum
number of contiguous batches without reordering. Hypothesis compares the
implementation against an independent finite dynamic-programming oracle;
native SHA-1 and SHA-256 tests use 10 MiB of distinct metadata, and corrupt
a late loose Blob in a disposable repository. The tests do not constitute
a machine-checked proof of the Python implementation or support for
arbitrarily large repositories. No new production dependency.

The existing complete-local-snapshot Lean model remains abstract. No new
Git object, object store, production dependency or implicit hydration.


## Bounded publication and retirement state model

`formal/DataPublication.lean` now specifies a finite control-state protocol:
candidate → validated → committed → published → retired → reclaimed,
plus reader acquisition/release and producer-controlled retention release.
Lean 4.35 proves by induction over every reachable abstract state that:

- Published implies validation evidence **and** a commit receipt.
- Reclaimed implies **zero** outstanding reader leases and retention release.
- Bypassing validation/commit with naive direct publish violates the model.

The state transition is an abstract atomic relation, **not** installed PG/SQL,
filesystem, Runtime, or Crash/Concurrency refinement. There is no proof of
durable multi-version snapshot isolation, wait-free readers, physical GC,
eventual completion or absence of filesystem races. The implementation owner
must discharge transaction ordering, reader leases, independent recovery,
source rights and retention release before any concrete auto-GC. This model
is a reusable *thought LEGO*, not a deployed publisher. No storage engine or
central registry has been implemented for it.

## Multi-version reader and delayed-reclamation safety (two generations)

The existing single-snapshot `formal/DataPublication.lean` cannot express
a consumer pinned to V1 while V2 is published. A separate bounded
`formal/DataMultiVersion.lean` now models an already committed old version,
a candidate new version, atomic active-version pointer switch, V1/V2 reader
counts and old-version retention release. The Lean kernel checks:

- Every reachable active V2 was validated AND committed before its switch.
- Every reachable reclaimed V1 has no old-version readers, has cleared
  retention, and is no longer the active head.
- Switching the head never changes the count of already pinned V1 readers.
- An uncommitted direct switch and early reclamation with an old reader are
  explicit unsafe-state counterexamples; neither is silently counted as a
  legal transition.
- Concrete **reachable** transition traces exhibit a V1 reader surviving
  a V2 pointer swap, then V1 becoming reclaimable only after that reader
  releases its reference and retention clearance is asserted. This avoids a
  vacuous proof in which publication or reclamation is never reachable.

This mirrors **control-state** ideas from PostgreSQL MVCC, Iceberg's
committed metadata-pointer swap and Linux RCU's delayed-reclamation
principle. It does **not** implement any of those algorithms, guarantee
distributed atomic file publication, prove liveness, grant retention
clearance, or authenticate a reader's file bytes. The verified model has
two generations, unbounded natural-number reader counters and idealized
atomic transitions. This is not a proven arbitrary-version production
registry, a PG implementation proof, or a physical lease/GC mechanism.

Source-to-model witness (different layer): Finance Accounting's real
PostgreSQL Paper tests under
`domains/capital/tests/test_paper_head_readback.py` verify a transaction
that writes receipts/ledger state before commit remains invisible, old
repeatable-read snapshots persist after another writer commits, same-key
concurrent writes conflict, an actual killed backend rolls back its
uncommitted effects, and the old committed receipt survives. Real PostgreSQL
18.6 disposable cluster and restart qualification are distinct from the
Lean theorem: PG MVCC snapshot is **not** an Artifact/file lease and cannot
justify deleting Parquet still referenced outside its DB. Retain physical
tests and require domain/Persistence/consumer GC evidence before auto-delete.

## Formal boundary / proof obligations

- **Identity and version:** for the same `(product_id, version)`, admission
  of a second entry must fail; distinct versions are separate identities.
  Source owner remains the authority for publishing a version.
- **Evidence status:** `VERIFIED` requires a bound expected digest and a
  scoped observed digest of the actually read bytes; `FALSIFIED` requires two
  differing bound/observed digests; absent, invalid, remote or unobservable
  evidence is `UNKNOWN`. The model starts only *after* URI/scope/format gates.
- **Composition:** a Data producer's guarantee must imply the consumer's
  assumption under the current contract; reuse the existing R2.1
  `IOContract` and sequential refinement lemmas. Passing a file hash
  does not discharge domain semantics or a reader's compatibility guarantee.
- **Explicit integrity gate:** `scripts/inspect_federation.py` now separates
  `InspectionCompleted` (ordinary read-only inspection) from
  `AllDistributionsVerified` (`--require-verified`). A catalog with only
  UNKNOWN or no distributions cannot satisfy the latter. This is artifact
  integrity only; the source owner must separately establish product rights,
  domain quality, freshness and final consumer compatibility.
- **Consumer-scoped admission:** the CLI may require exactly one or more
  stable `(product_id, product_version, distribution_urn)` identities to
  be VERIFIED, preserving the global NOT_ESTABLISHED result when other
  ports lack evidence. Missing/ambiguous version bindings fail; neither
  this scope rule nor the Lean abstract model proves full product
  publishability. Keep an actual multi-port consumer test.
- **Physical I/O:** path resolution, symlink races, file replacement,
  filesystem permissions, atomic publish, provider API changes and network
  I/O have no present complete Python-to-Lean refinement proof. Keep their
  native tests and real read-back evidence.
- **Scientific/finance:** sampled statistics, temporal known-as-of availability,
  source rights, data cleaning and actual economic outcomes require native
  consumer evidence. SMT cannot turn questionable market data into a fact.

## Delete–reuse–compose–create verification decision

| Property class | Preferred evidence | Existing tests disposition |
| --- | --- | --- |
| Pure finite/inductive identity and state invariants | Lean or a stronger owner-native prover | Consolidate redundant synthetic examples **only after** source-to-model refinement is independently established |
| Pure Python projection/control predicate | PEP 316 with CrossHair + SMT and real implementation comparison | Keep one interface/consumer witness; search coverage is bounded, so no universal deletion claim |
| Parquet/SQL/bytes | Artifact Dataset Contract, independent DuckDB/PyArrow readers and native schemas | Keep critical differential and real-byte tests; Lean abstract equality does not replace them |
| Stateful publishing/recovery | TLA+/Quint transition model or explicit Hoare/refinement, owner-side | Keep durable PostgreSQL/Runtime read-back until state/effect refinement is demonstrated |
| External source/network/rights | Source agreements, timestamps, credentials policy, provider and consumer evidence | Preserve focused native integration; do not replace by a simulated proof |

Do not count theorem numbers or tests as the objective. Each maintained check
needs a consumer invariant or an actual known failure mode. Historical frozen
evidence may have real downstream consumers: delete only after proving loss of
reachability and fulfilling the actual retention/recovery authority.

## Read-only product projection evidence boundary

`src/ordivon_data/odps_projection.py` is a concrete ODPS v1.1-to-DCAT 3
metadata adapter, not an additional product registry or executable publishing
transaction. The source ODPS byte digests are bound into the resulting
catalog identity; output-port ID and version absence is faithfully preserved
under the upstream Bitol standard. New native tests check determinism,
duplicate product identity, optional port fields, malformed input and
compatibility with the existing DCAT inspector. A separate locked-version
RDFLib 7.6 parser read-back validates the actual JSON-LD graph. These are
implementation/format witnesses, **not** abstract proof or installed data
availability. The owner-native data and rights policies remain external.

## Conditional I/O refinement from real producer metadata

`local_evidence.py` provides the missing I/O evidence for selected exact
product-output boundaries, using only producer-declared ODPS source path
and SHA-256 fields plus an operator-specified owner root. A current
regular-file read is hashed and mismatches reject the projection. This
binds two present JSON files in the tested checkout; the Episode Parquet
index remains unavailable/UNKNOWN. Native positive and negative tests
cover real file digest, corrupted bytes, incorrect port, missing property,
duplicate binding, and `..` traversal. W3C DCAT 3 `spdx:checksum`
preserves producer port `dct:identifier` and allows RDFLib readback.
A contradictory legacy SHA-256 declaration rejects the source; the
frozen legacy federation still supports the older digest shape.

This is **not** a formal proof that symbolic file paths never change,
that SHA-256 is collision-free, or that port/source association was proved
from ODPS alone (the explicit operator binding is an additional assumption).
Source identity, physical availability, rights and downstream acceptance
must remain distinct from the Lean abstract digest verdict.

## Scope of proof evidence

The existing models and symbolic checks are bounded source-level inputs,
not production transaction, release or reclamation services. The natural
Runtime, Preservation, Artifact, Research and Finance Owners retain
installed/effect/consumer authority. Use their own native acceptance.
Workflow guidance lives in [AGENTS.md](../AGENTS.md) and the
[README](../README.md); do not duplicate generic cross-owner instructions here.


### Shared file-port and SHA-256 representation (2026-11-28)

The existing local-evidence owner supplies the file-port media-type mapping
used by ODPS projection and strict local binding; the existing pure
verification module owns the lowercase digest grammar and SPDX algorithm
identifier. Remove parallel format and digest definitions without changing
producer errors, legacy UNKNOWN, valid byte verdicts or local scope.
Consumer tests exercise all three supported types and malformed/unsupported
types, plus legacy versus typed checksum admission. This is source-level
representation convergence, not proof of the physical file's media format.

Native verification: 42 Data, 31 lifecycle/property, and 25 Research
consumer tests passed; existing formal task (three Lean models plus
bounded CrossHair) exited successfully. Independent peer review and
remote integration remain unestablished.
