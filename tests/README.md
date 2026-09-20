# Tests

The repository test owner is `pytest`. It runs both native pytest tests and the existing `unittest.TestCase` suites, so one repository gate covers current function-style tests as well as legacy class-based tests. The repository does not define a separate Ordivon test framework.

Current test responsibilities fall into four practical groups:

- **behavior/contract tests** — observable repository/domain semantics, replay rules and fail-closed behavior;
- **adapter/integration tests** — boundaries to Runtime, MCP, providers and other replaceable external systems;
- **architecture regression tests** — stable constraints such as “external-owner projections must not become semantic authority” or “Runtime execution evidence must not become semantic completion”;
- **migration/schema ratchets** — temporary or long-lived guards that prevent deleted legacy stores/classes/tables from silently returning while historical data boundaries are still relevant.

Prefer stable behavior/architecture names for current tests. Revision tokens belong only to genuinely versioned subjects such as a frozen experiment or an active migration ratchet. Retirement construction tests should disappear once their invariant is absorbed by stable architecture policy. The retired Agent Service is guarded only by the External Ownership Boundary non-reintroduction policy; its old behavior and SQLite-schema suites are intentionally gone.

Coverage is an observation, not a correctness score. Use branch coverage to locate untested risk paths, then add tests for consequential behavior rather than chasing a repository-wide percentage threshold.
