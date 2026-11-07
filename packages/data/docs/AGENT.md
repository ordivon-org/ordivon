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
- Product discovery -> current DCAT projection and this read-only CLI.
- Product contract -> producing owner's ODCS/ODPS document and native tests.
- Job/Attempt/process/Artifact effect -> Runtime; not this package.
- Long-lived general workflow -> proven Temporal/runtime owner; persistent
  data-asset graph -> Dagster only after real recurring asset/partition pressure.
- Retention/archival -> Preservation and records owner, not timestamp deletion.

## Execution and proof

1. Read `README.md` and run the inspection CLI; never treat the returned
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

Native verification: `mise run data:verify`, followed by the affected domain
consumer's own verify task. Agent Skills are advice, not execution authority.
