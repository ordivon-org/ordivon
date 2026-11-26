# Host test qualification

从 [Host Owner Guide](HOST_OWNER_GUIDE.md) 迁移的原契约。该文件承载相关职责的操作约束与历史资格证据；不另立运行时权威。

<a name="contract-1"></a>

### Complete suite qualification

The queue entrypoint is distinct from portable/focused tests. It consumes
the native pytest collection and setup/call/teardown reports, rejects skips,
xfail/xpass, deselection, missing phases and empty suites, and preserves
native nonzero outcomes. The queue clears inherited PYTEST_ADDOPTS so a
developer's selection or collect-only option cannot masquerade as complete
qualification. It uses strict pytest marker/config validation.

An explicit caller-supplied test DSN without all dedicated boundary,
migration and receipt fixtures is not sufficient for complete qualification;
any missing native obligations must fail rather than be counted as passing.
Portable/focused pytest retains native skip behavior. This gate qualifies
the observed collected suite, not the existence of every possible semantic
test, the installed production consumer, or a hostile test plugin.

Caller-provisioned complete queue runs must supply all ten distinct database
fixtures before migration. The queue compares PostgreSQL server major,
native cluster system identifier and database OID through read-only catalog
queries, not DSN spelling. Missing, aliased, wrong-major or unobservable
identities fail before Alembic or test execution. Caller-provisioned
fixtures still require an explicitly disposable test fleet; catalog
identity does not prove that a database is safe to mutate. The native
identity query must be available to the test role. Fresh owned-container
runs provision their own fixture fleet as before.

The complete queue additionally compares the source test-file obligations
under the Host tests root (pytest's default test_*.py and *_test.py naming)
against native item discovery. Each named test file must contribute at
least one native test. Native itemcollected multiplicity must equal final
selection, with unique node IDs. Every parent test must report exactly
one successful setup, call and teardown in that order. Native subtests
are separate evidence, not duplicate parent call reports; non-passing
subtests still disqualify the complete run. Reordering tests is allowed,
silent removals, duplicate executions/reports and rerun reports are not.
This consumes the public pytest 9.2 subtest report API, not a parallel
runner; it cannot establish unexpressed semantic obligations or defend
against arbitrary malicious plugins. Report behavior is qualified on
the actual locked pytest version.

<a name="contract-2"></a>

### Native attempt evidence (opt-in)

Set ORDIVON_HOST_QUEUE_EVIDENCE_DIR to a fresh, non-existent directory
outside the checkout, under an existing private parent, before invoking
the complete Host queue. The queue consumes the destination at its own
boundary and clears inherited pytest selection/plugin environment
variables. It invokes the existing native pytest runner with JUnit XML
and a small optional attempt-evidence plugin. It does not retry tests or
replace the complete-suite verdict. Both the native JUnit and receipt
are private, non-overwriting artifacts; failure traces may contain
sensitive fixture information and must not be automatically published.

The receipt records an invocation UUID, observed clean Git commit/Host
tree and lock digest before and after, actual Python and pytest versions,
native report outcome counts, nonpassing node IDs, the exit status after
the complete-suite gate, and native JUnit digest and bytes. A missing
report or changed source cannot turn a zero exit into qualification.
A later passing attempt does not replace the earlier nonpass artifact.
GitHub environment values are only provider declarations, with source
matching required; actual provider check/run/attempt and Runtime artifact
identity must be independently read back by the consumer. Before/after
source observations do not prove immutability during execution, complete
environment equivalence, or protection from hostile plugins. A killed
or interrupted process may leave no complete receipt; absence is UNKNOWN.
