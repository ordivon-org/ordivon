# Host DB test qualification — Spec / short SOP / Acceptance (2026-10-15)

**Spec.** Ordinary Host tests may skip real PostgreSQL tests when no DSN is supplied. With a DSN, selected DB tests must run a single existing Host schema preflight regardless of human-readable skip reason; malformed/unavailable/unmigrated DB is a distinct failure. Required `host:queue` must actually run DB integration against PostgreSQL **18**, on a disposable DB. Do not touch an unknown self-hosted runner's database. No production Host database is modified by this plan.

**Short forecast SOP (using existing Skills, never generate new Skills).**

1. **Bind source and oracle** — read Host tests, owner manifest, native CI and historical C2/83e6 experiments. Skills: existing `user-agents/tdd`, `user-agents/diagnosing-bugs`. Tools: Ordivon Host `work.get`, Runtime `workspace.get/exec`, Git.
2. **Repair DB selection** — use pytest's native session fixture with explicit module `usefixtures` so DB selection does not parse skip reason. Tests: no DSN skips, bad DSN fails when DB tests selected, pure tests unaffected, skip-reason change does not bypass fixture. Tools: Runtime `workspace.mutate/exec`, pytest.
3. **Qualify CI** — configure owner `queue_verify_task=host:queue`; task should reject no-DSN non-hosted or self-hosted settings; on proven GitHub-hosted runners use disposable PostgreSQL 18; explicit DSN portable with readback of PG major 18, migrations via Alembic and real pytest DB tests. Tools: Git, Bash, pytest, Docker only within proven disposable environment.
4. **Acceptance** — direct native `mise`/Python3.14.7 pytest, lint, negative and positive controls, verify command source and exact SHA. Skill: existing `verification-before-completion`. Avoid claiming successful DB-18 full suite without actual PG18 execution.

**Expected deviations**: host test setup may require owner dependencies; PostgreSQL image may not be cached. Do not silently substitute unqualified local database or mark skipped tests PASS. No independent audit or new management component is required for this local code candidate.

## Actual execution (append after action)

- Pin: isolated Workspace `ws-testqual-host-ci-gpt6-20261015` based on Git `3262ebf0c37952b775a3081b8cdbbc59685d34d3`; main/protected untouched.
- DB selection: pytest `session` fixture `host_test_db_ready`, explicit three DB-module `usefixtures` markers, bounded connect_timeout=5; no dependence on `skipif.reason` strings.
- Negative controls: missing DSN skips DB modules; invalid DSN selected => `HOST_TEST_DB_PREFLIGHT_FAILED` exit 4; pure-only selection bypasses DB preflight; reworded skip reason cannot bypass the fixture. Last relevant local tests `job-01a14040-91e7-7ad1-8279-a494e92edd7b`: 17 tests passed (Fixture/Queue/Policy), owner route 25 passed, Ruff clean.
- Queue source: existing root Owner manifest selects `host:queue`; a single owner-local Bash task enforces explicit DSN or GitHub-hosted+Docker disposable PostgreSQL 18. It checks server major and runs Alembic before the *real* Host pytest suite. No `sudo systemctl`, fixed shared DB drop, new test framework or global management.
- **Real PG18 evidence**: `job-01a1403a-fdec-7ff2-aaba-4d248947ebe0` started ephemeral PG18.6 on loopback with owner-separated DSN; `180006` major readback; 89 Host tests passed before three additional reason-drift test cases. Hosted auto-provision simulation `job-01a1403e-0fcf-7983-9f48-5eb0e5fcab41`: 89 passed and no `ordivon-host-ci-*` container remained afterwards.
- Integrated local-main candidate `86c6bded6913a8de88a792bd878d6aa803a6e425` was subsequently qualified: Job `job-01a14042-f8b8-7fc3-817c-487d7eea9cbb` completed 92/92 Host tests on disposable PostgreSQL 18 after adding three controls; container cleanup verified.
- Re-representation on **current GitHub protected main** `3818e74543a79225d429e27e2acffcf88a40792a` was separately executed in `ws-testqual-protected-current-gpt6-20261016`. Job `job-01a1406d-ed80-7c10-9f34-39e0ec4eacae` passed **91/91 Host tests** with disposable PostgreSQL 18, full Alembic schema and cleanup; the count differs because the protected main contains a different preexisting test set. The remote-main baseline is not the prior local-main history. Required GitHub hosted CI and protected branch publication remain separate future evidence.
