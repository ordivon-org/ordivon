# Host Rust R6 — Original Python MCP schema ↔ real native Rust consumer proof

## Customer-facing defect this eliminates
The legacy Python Host source publishes a TypedDict-derived **outputSchema** for all 31 MCP tools; the R5 official `rmcp` Rust candidate exposed 27 tools but **no output schema**. A tool name and even a passing isolated database mutation are insufficient proof that an Agent or Gateway may interpret the returned structured content correctly. There were also five original Python parameter default discrepancies in native Rust metadata.

## DELETE-CUSTOM → REUSE
- Use existing **official rmcp 3.9.0** `#[tool(output_schema = ...)]` and `schemars` `#[schemars(extend("default" = ...))]`, not a second tool registry or handwritten schema engine.
- Generate immutable JSON from **the real original Python MCP server** `build_server(...).list_tools()`, using `outputSchema` derived from the existing authoritative TypedDict response contracts. `tools/sync_python_output_contracts.py --write` produces `contracts/python_host_mcp_output_schemas.json` with 31 typed tool schemas. `--check` reruns the same source registry in the original Python Host environment and compares bytes exactly; any source contract drift breaks the isolated merge queue.
- Rust `mcp.rs::legacy_output_schema` reads the source-generated embedded JSON via `include_str!` and `OnceLock`. It has **no Python process, mutable registry, Pydantic dependency, shadow data or duplicated persistence**.
- Existing Rust handlers still own actual execution. The original Python source schema is a contract, **not evidence that a Rust response conforms**.

## Falsification at the consumers, not only the tool manifest
- Real Rust `tools/list` output schemas are compared to original Python MCP registry **whole JSON objects** by `tools/audit_mcp_surface.py`. For every published Rust tool, input required fields/properties/defaults/enums/additionalProperties and original Python output schema must match. Newly absent tools remain listed separately and cannot be counted as active.
- Rust unit test `mcp::tests::output_schemas_and_input_defaults_match_original_python_sdk_contract` verifies all 27 advertised output schemas and the six individual default fields that caused five tool-level mismatches.
- Disposable **PostgreSQL 18 + original Alembic 0001→0013** runs normal Rust official stdio and streamable HTTP MCP; every successful `structuredContent` in these wire tests is independently verified against the tool's **actual advertised Draft 2020-12 JSON Schema** with the existing Python `jsonschema` package. Error/UNKNOWN results (`isError=true`) are not masqueraded as a success object for validation.
- stdio exercises and validates **30/30** successful tool types, HTTP validates the eleven consumer tools it calls, including Work/Social/Attention/Doctor and original Python readback. The old full Host Python 485-suite, native Work/Actor and Social/Attention concurrency/Unicode/receipt/history gates still run unchanged on fresh disposable PG18.
- Comparison outputs `planning/mcp_source_rust_r6.json` should report **Python=31, Rust=30, missing=1, schemaDifferences=0, outputSchema Python31/Rust30** at this SourceCut. It is not a claim of production Gateway/connector installation or deployment parity.

## Pool stats: no invented zeros
The Python-only source `host.pool.stats` returned 15 **Psycopg-specific cumulative and gauge measurements** from `psycopg_pool.get_stats()`. The actual reused Rust pool is `deadpool-postgres`, whose documented native process projection has four eventually consistent gauges and per-object lifecycle timestamps/recycle counts; it does **not** supply 15 equivalent native counters. Filling missing cumulative counters with zero would be false evidence. Source-vs-installed consumer decision and explicit metric semantics require a separate owner review; this change does not register a fake `host.pool.stats` tool.

## Release gate still red
B's Space/Subject/Participation domains are already merged and all three are exposed through the official C rmcp bridge. Original Python SocialStore exact JSON and real stdio/HTTP success-schema checks pass. Only host.pool.stats remains source-only and under consumer qualification. The existing production Python Host and its historic three invalid Work histories are untouched; A owns the single Draft PR #2088, remote checks and eventual installed/Gateway cutover.
