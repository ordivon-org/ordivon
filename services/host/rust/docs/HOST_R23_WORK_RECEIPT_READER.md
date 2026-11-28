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

## Explicit oracle requalification

The optional second argument binds a new exact Python commit (40 lowercase hex digits); the historical default remains unchanged. The script refuses a mismatched HEAD or changes in the Python interpreter pin, migration, package/lock, or source inputs. Prepare the locked Python environment separately. The Rust candidate may coexist in the same checkout without becoming part of the Python oracle. A successful library witness is not service admission or full ABI qualification.

Requalification 2026-11-28: Python source f2455e654d2d4035adbf8718c4d413910198234f, native PG18 direct library witness EXIT0, 3/3 legacy/compact/later exact replay, Rust legacy writer to Python equal, schema16 rollback replay 3/3; service schema17 and schema16 explicitly rejected. Runtime job job-01a22022-afe6-73f0-ba99-cf7a95d0dbd3, stdout SHA256 aefb3cba60bdd757cb7568c9a785c88678a643b398859beb337ab55b77b18c33. No production mutation or schema gate change.

All-targets non-ignored Rust qualification at that scoped source: 30 passed, 30 ignored (database-dependent), 0 failed (job-01a22023-4e10-7114-8de0-477343955a36). Three source-binding negative controls rejected malformed revision, wrong commit and untracked Python input before test DB startup (job-01a22023-d93e-7638-8b7e-3ac4fd0a2567). This does not replace full native service/ABI qualification.
