# Data Formal Verification — property-first, consumer-bound

This is a **scoped method and evidence map**, not a new verification calculus,
registry, security policy, or claim of universal correctness. The canonical
Recursive LEGO R2.1 contracts and shared formal toolchain already exist at
`.agents/skills/recursive-lego-calculus/SKILL.md` and `tools/formal/`.

## Current proof chain

| Stage | Source | Proven or observed | Explicit non-claim |
| --- | --- | --- | --- |
| Specification | `formal/DataProduct.lean` | Optional digest observations and `(id, version)` registry identities | SHA-256 collision resistance and factual truth |
| Model and proof | Lean 4.35 kernel | Missing digest => UNKNOWN; VERIFIED requires two matching observations; FALSIFIED requires distinct observations; a unique product registry stays unique on admission | Python installed-code correctness |
| Implementation candidate | `src/ordivon_data/verification.py` | Pure `digest_verdict` with PEP 316 contracts; CrossHair 0.0.112 / Z3 searches symbolic executions | CrossHair bounded search is not a theorem |
| File/consumer refinement | `src/ordivon_data/catalog.py` and `tests/test_catalog.py` | Real file SHA-256 read-back, deliberate digest mismatch, unavailable/out-of-scope UNKNOWN; product ID-version reject | Atomicity against concurrent file changes; universal URI/JSON-LD semantics |
| Native consumer | `studies/data-lifecycle/tests` + domain-specific consumers | Selected frozen Data Lifecycle, Capital/Finance, Episode and Artifact contracts | Live finance API freshness, scientific causal validity, external distribution rights |

Formal command: `mise run data:formal:verify`.
Native integration: `mise run data:verify`.
The formal task explicitly uses Ordivon's existing pinned Lean tool group and
CrossHair's standard PEP 316 implementation; no private theorem kernel or DSL.

The Lean proof output depends only on Lean's ordinary `propext` axiom; there
are no `sorry` assumptions. It proves the stated **abstract** model under
a total, exact digest-equality relation. Real SHA-256 digest values are modeled
abstractly: digest equality proves only hash equality, not metaphysical byte
identity, origin authenticity, producer authorization, or permission to publish.

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

## Guidance by role

**Human:** identify the final consumer, the business/scientific definition
and the minimum specification. Demand a counterexample to proposed weak
models, check which assumptions match reality and decide whether a test
really became redundant. Approve a version migration by real consumer
compatibility evidence, not by a passing synthetic model.

**Agent:** resolve existing formal Skills and Owner-native tools first. Write
an explicit input domain, postconditions, invariants and error states.
Run Lean for the abstract model, CrossHair for the pure Python portion, and
actual owner read-back at I/O edges. Record exact code SourceCut, verifier
version, assumptions, negative oracle and relevant native consumer outcome.
Never relabel `UNKNOWN` as `FALSIFIED` and never report bounded symbolic
exploration as full installed-code refinement.

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

## Cross-owner adoption without a new platform

- Runtime/Host/Harness: use their existing state-transition models, Rust
  contracts and PostgreSQL read-back; choose TLA+/Quint only for consequential
  concurrency/liveness questions.
- Artifact/Media: reuse real byte/format validators, native QC and bounded
  differential checks; formalize deterministic metadata and admission rules.
- Finance: formalize point-in-time data semantics, portfolio constraints,
  margin and state transitions; real provider snapshots and downstream
  research acceptance remain separate.
- Research: specify estimands, sampling/inference assumptions and reproducible
  source identities; statistical assumptions cannot generally be proved from
  software code.
- ELE/Skills: model discovery/qualification state and provenance; external
  facts and installation/permission effects still require direct observation.

This file does not grant authority over those owners' code, tests or releases.
