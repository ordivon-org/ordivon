# Agent instructions

Keep this provider limited to production-reachable Fetch, Browser, Receipt, Artifact, release, rollback, retention, and cleanup paths.

## Invariants

1. The same Request ID cannot bind different input.
2. An uncertain external operation is reconciled through its original request before redispatch.
3. A stale lease generation cannot commit.
4. A Receipt cannot outlive the Artifact it names.
5. Downloaded Artifacts are independently checked by digest and byte count.
6. Releases bind the exact Worker input tree, not repository ceremony.
7. A candidate smoke proves the deployed version and only the capabilities affected by the change.

Delete dormant capabilities, historical experiments, duplicate declarations, and checks that only preserve wording or project shape.
