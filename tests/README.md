# Tests

The test suite uses the Python standard-library `unittest` runner. The repository does not define a separate Ordivon test framework.

Current test responsibilities fall into four practical groups:

- **behavior/contract tests** — observable domain and service semantics, replay rules and fail-closed behavior;
- **adapter/integration tests** — boundaries to Runtime, MCP, providers and other replaceable external systems;
- **architecture regression tests** — stable constraints such as “semantic adapters must not own HTTP transport” or “Runtime execution evidence must not become semantic completion”;
- **migration/schema ratchets** — temporary or long-lived guards that prevent deleted legacy stores/classes/tables from silently returning while historical data boundaries are still relevant.

Prefer stable behavior/architecture names for current tests. Revision tokens belong only to genuinely versioned subjects such as a frozen experiment or an active migration ratchet. `elimination` / `retired` construction names should disappear once their invariant is absorbed by a stable contract, schema migration, or architecture ratchet. Agent Service behavior tests therefore use stable names; legacy SQLite rejection is owned centrally by `schema_migrations.LEGACY_TABLES`, and retired type non-reintroduction is owned by the Core-Zero ratchet.

Coverage is an observation, not a correctness score. Use branch coverage to locate untested risk paths, then add tests for consequential behavior rather than chasing a repository-wide percentage threshold.
