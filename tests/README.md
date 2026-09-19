# Tests

The test suite uses the Python standard-library `unittest` runner. The repository does not define a separate Ordivon test framework.

Current test responsibilities fall into four practical groups:

- **behavior/contract tests** — observable domain and service semantics, replay rules and fail-closed behavior;
- **adapter/integration tests** — boundaries to Runtime, MCP, providers and other replaceable external systems;
- **architecture regression tests** — stable constraints such as “semantic adapters must not own HTTP transport” or “Runtime execution evidence must not become semantic completion”;
- **migration/schema ratchets** — temporary or long-lived guards that prevent deleted legacy stores/classes/tables from silently returning while historical data boundaries are still relevant.

Prefer stable behavior/architecture names for new tests. A historical `R<n>`, `elimination`, or `retired` name is not a new taxonomy; it records an existing migration ratchet and should disappear or be renamed when the invariant is absorbed by a stable contract, schema migration, or mature architecture tool.

Coverage is an observation, not a correctness score. Use branch coverage to locate untested risk paths, then add tests for consequential behavior rather than chasing a repository-wide percentage threshold.
