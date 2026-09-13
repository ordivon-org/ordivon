# Host v2 R6 Cleanup

## Standing

R6 removes the last generic internal surfaces that had no production consumer and closes the remaining Board→Task routing and deployment gaps. It does not expand Host's authority.

The retained product definition is:

> Host v2 is a durable semantic continuity and collaboration substrate. It owns revisioned WorkingCheckpoint persistence, Host-local lifecycle state, durable Board collaboration records, exact re-entry navigation, and retained News publication revisions. It does not own execution, priority, assignment, deployment truth, Runtime/Git currentness, or external-world truth.

## Schema v4

Alembic revision `0004` advances `host_v2_schema.schema_version` from 3 to 4 and removes:

- `activity_log`
- `extension_states`
- `extension_history`

The production audit found zero rows in all three tables and no consumer outside the Host v2 repository. Historical migration `0003` remains immutable; `0004` performs the explicit deletion.

## Deterministic route anchors

Every newly adopted Task now atomically ensures one canonical Board root:

`task-route-anchor-v1:<sha256(taskId)>`

The canonical author, topic, message shape, digest binding, and no-parent constraint remain protected against first-writer squatting. Existing canonical anchors replay as `existing`; a conflicting row fails closed.

`attention.delta` still fences on the durable Board sequence, but canonical route-anchor rows are classified as infrastructure rather than collaboration messages. They advance the Board fence without appearing as unrouted work or inflating `newMessageCount`; `infrastructureMessageCount` reports them explicitly.

The frozen production rehearsal contained 233 open Tasks, of which 102 already had canonical route anchors. The R6 backfill produced exactly 131 new anchors and converged open-Task coverage to 233/233 while preserving all historical Board rows.

## MCP contracts

All 13 MCP tools now expose typed output schemas rather than a top-level unconstrained object. WorkingCheckpoint payloads and other deliberately owner-defined semantic payloads remain open objects at their explicit extension boundary.

`news.publish.edition` is now a Pydantic contract derived from the stable shape shared by all 14 production editions at R6 audit time. The contract fixes edition identity/timing/provenance fields and the stable News item envelope while leaving each evidence object open for source-specific evidence metadata.

## Deployment model

The shared `/opt/ordivon/host-v2/venv` deployment pattern is retired. Each immutable release directory owns its own `.venv`, created from the committed `uv.lock` with:

`uv sync --frozen --no-dev`

The systemd unit runs:

- `/opt/ordivon/host-v2/current/.venv/bin/python` for schema readiness
- `/opt/ordivon/host-v2/current/.venv/bin/ordivon-host-v2-mcp` for the service

`packaging/install_release.sh` builds/provisions one exact Git SHA and atomically switches `current` only after the release-local environment is complete.

## Verification

Before production mutation, R6 passed:

- fresh PostgreSQL Alembic `0001→0002→0003→0004`
- complete test suite: 25/25
- Ruff
- `git diff --check`
- automatic route-anchor creation smoke
- full frozen v1 semantic bundle import and equivalence verification
- full open-Task route-anchor backfill rehearsal

The full historical migration rehearsal preserved:

- 2,025 Tasks
- 14,412 Task revisions/checkpoints/events
- 15,640 pre-R6 Board messages
- 14 News publications

and then converged open route-anchor coverage from 102/233 to 233/233 by creating exactly 131 new infrastructure anchors.
