# R23 native Work receipt read-side donor

Parent: 1b513e8142f6d056a65400f185971848c1ffb48a (#2088).
Independent Python oracle: e518460b99f2464ebe369dc9adf48506ccb768a2.
The schema admission remains exactly as in the parent. This is not a service
release, migration, or compact writer. The caller transaction and request
arbiter remain the sole authority. A Work receipt is read in two native
statements (claim + row) or three for a compact receipt (plus exact historical
snapshot). A typed create/commit context disambiguates a later create from a
commit's exact successor. Legacy reads require null pins; schema <17 requires
no native pin columns. Compact reads require the actual stored pin and the
request, envelope, payload digest, writer, and normalized response digest
to agree. No current-head substitution or secondary store.

Run the private native differential witness in an isolated test Runtime:
`bash tools/verify_work_receipt_cross_language.sh /path/to/exact/python/services/host`
(the Python checkout has already been synchronized with its own locked uv
environment). The script creates and removes its own Unix-only PG18 cluster.
Do not call the raw test helpers on real data. The fixture deliberately corrupts
only its own synthetic response and historical snapshot, restores them, and
tests a wrong but internally consistent root. The reverse witness writes one
Rust Legacy receipt and reads it through Python, then expands two compact roots
and downgrades to schema 16 for a final replay check. Separate service admission
and complete MCP/ABI/recovery qualification are required before installation.

Known existing test dependency: the schema-13 actor timestamp test asserts UTC;
native initdb may inherit Asia/Shanghai. Use explicit UTC for that fixture,
not a relaxed timestamp assertion. Preserve original nonpass evidence.
