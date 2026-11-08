# Data — Agent operating instructions

## SourceCut before execution

Select one final consumer. Capture the exact source revision, data-product
ID/version, declared source digests, data rights and accepted quality/semantics.
Discovery metadata is only a candidate until its producing owner confirms it.

## Capability-first routing

- Source API capture -> producer's existing adapters (Capital markets /
  Research scholarly sources / external provider client).
- Raw web evidence -> Artifact's existing WARC profile.
- Flat Parquet validation -> Artifact's existing Dataset Contract + DuckDB
  and PyArrow differential reader. Do not replace with ad-hoc CSV parsing.
- Analytics/transformations -> DuckDB, native domain SQL/Python/Polars
  when available in that task's lockfile; do not assume global Python imports.
- Product discovery -> the frozen DCAT projection for historical acceptance,
  or `scripts/project_owned_products.py` to derive a fresh read-only DCAT
  projection from currently tracked owner ODPS records. Do not confuse the
  two-source Git projection with the three-product frozen 2026-09 snapshot.
  Do not mint port UUIDs, URLs, digest or reuse rights; ODPS v1.1 outputPort
  IDs and versions are optional and their versions need not match the product.

- Product contract -> producing owner's ODCS/ODPS document and native tests.
- Job/Attempt/process/Artifact effect -> Runtime; not this package.
- Long-lived general workflow -> proven Temporal/runtime owner; persistent
  data-asset graph -> Dagster only after real recurring asset/partition pressure.
- Retention/archival -> Preservation and records owner, not timestamp deletion.

## Execution and proof

1. Read `README.md` and run the inspection CLI; never treat the returned
   zero exit in discovery mode as a product-integrity admission. Use
   `--verify-local --require-verified` when requiring real byte evidence;
   exit 3 means UNKNOWN/not established, while exit 2 means a conflicting
   digest or invalid catalog. For a consumer bound to one stable output-port
   identity, use `--verify-local --require-port PRODUCT_ID PRODUCT_VERSION
   DISTRIBUTION_URN`. A selected-port PASS must not be promoted to a
   global product PASS. The unmaterialized Episode Parquet stays UNKNOWN. Do not interpret these as a right to publish.
   directory path or catalog version as proof of deployed data.
2. Verify the exact physical bytes under explicit scope. Unknown remains
   typed UNKNOWN rather than FALSE or PASS. A file digest match does not
   prove statistics, correctness, licenses, or scientific causal claims.
3. Use the original domain-native contract to verify semantics and release
   version. Run negative/differential checks only for material failure modes.
4. If introducing an independently contractable LEGO, specify complete
   R2.1 `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` through the
   canonical Skill; cite real source, verifier, consumers, and currentness.
5. Emit data access/publish/read-back evidence with the exact source and
   output versions. Check final consumer outcomes separately from Runtime
   process success and transport success.
6. Migrate old ODPS only with explicit versioned producer/consumer
   contract compatibility; ODPS 4.2 differs from consumed 1.1.
7. For cleanup, use actual consumer/recovery/retention paths; no age-based
   deletion, guessed rename or wiping shared worktrees. Prefer owner-native
   Git/workspace management and temporary cache pruning.

Local producer byte binding: use explicit `--bind-local` only after reading
the producer's declared ODPS properties, qualified owner root and *exact*
output-port name. The tool checks the actual regular file SHA-256 and emits DCAT 3
`spdx:checksum` without overwriting `dct:identifier`. Never fabricate
port/file matching, claim a portable URL, or promote a missing
Episode Parquet materialization to VERIFIED. Native consumers must recheck
byte identity at their read boundary.

For publication/retirement changes, reuse the Lean `formal/DataPublication.lean`
safety model. It proves *abstract* publish-after-validate/commit and
reclaim-after-zero-readers/retention-release, but an installed SQL/Artifact
implementation requires independent transaction/refinement/read-back evidence.
Do not auto-delete data based on model success alone.

Formal contract: [FORMAL_VERIFICATION.md](FORMAL_VERIFICATION.md).
Run `mise run data:formal:verify` for Lean / CrossHair evidence; the result
is NOT a proof that path reads, source licenses, network I/O, or domain
semantics refine the model. Preserve necessary negative and real-consumer
witnesses when implementation-to-model refinement is partial.

Native verification: `mise run data:verify`, followed by the affected domain
consumer's own verify task. Agent Skills are advice, not execution authority.
