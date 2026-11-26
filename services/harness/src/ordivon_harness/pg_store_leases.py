"""Original per-Run lease admission, release and transactional consumption.

Original PostgreSQL connection and existing transaction authority are retained.
"""

from __future__ import annotations
from .store_errors import (
    HarnessLeaseConflict,
    HarnessLeaseHeld,
    HarnessRevisionConflict,
    HarnessTerminalConflict,
)
from .store import (
    HarnessRunLease,
)

from .pg_store_codec import run_projection

class PostgresLeases:
    """Original per-Run lease admission, release and transactional consumption."""

    def acquire_run_lease(
        self,
        harness_run_id: str,
        *,
        owner_id: str,
        ttl_ms: int,
        now_ms: int,
        expected_run_revision: int | None = None,
    ) -> HarnessRunLease:
        if not owner_id or owner_id != owner_id.strip() or ttl_ms < 1 or now_ms < 0:
            raise ValueError("Harness lease identity, TTL or clock is invalid")
        with self.connection.transaction():
            row = self.connection.execute(
                "SELECT * FROM runs WHERE harness_run_id=%s FOR UPDATE", (harness_run_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Harness Run does not exist: {harness_run_id}")
            run = run_projection(harness_run_id, row)
            if expected_run_revision is not None and run.revision != expected_run_revision:
                raise HarnessRevisionConflict("Run revision changed before lease admission")
            if run.status.terminal:
                raise HarnessTerminalConflict("terminal Run cannot be leased")
            current = self.connection.execute(
                "SELECT * FROM run_leases WHERE harness_run_id=%s FOR UPDATE", (harness_run_id,)
            ).fetchone()
            revision = 1
            if current is not None:
                if current["expires_at_ms"] > now_ms:
                    if current["owner_id"] == owner_id and current["run_revision"] == run.revision:
                        return HarnessRunLease(
                            harness_run_id,
                            owner_id,
                            int(current["lease_revision"]),
                            run.revision,
                            int(current["expires_at_ms"]),
                        )
                    raise HarnessLeaseHeld("Harness Run leased by other execution")
                revision = int(current["lease_revision"]) + 1
            expires = now_ms + ttl_ms
            self.connection.execute(
                "INSERT INTO run_leases(harness_run_id,owner_id,lease_revision,run_revision,expires_at_ms) "
                "VALUES(%s,%s,%s,%s,%s) ON CONFLICT(harness_run_id) DO UPDATE SET "
                "owner_id=EXCLUDED.owner_id,lease_revision=EXCLUDED.lease_revision,"
                "run_revision=EXCLUDED.run_revision,expires_at_ms=EXCLUDED.expires_at_ms",
                (harness_run_id, owner_id, revision, run.revision, expires),
            )
            return HarnessRunLease(harness_run_id, owner_id, revision, run.revision, expires)

    def release_run_lease(self, lease: HarnessRunLease) -> bool:
        with self.connection.transaction():
            changed = self.connection.execute(
                "DELETE FROM run_leases WHERE harness_run_id=%s AND owner_id=%s "
                "AND lease_revision=%s AND run_revision=%s AND expires_at_ms=%s",
                (
                    lease.harness_run_id,
                    lease.owner_id,
                    lease.lease_revision,
                    lease.run_revision,
                    lease.expires_at_ms,
                ),
            ).rowcount
        return changed == 1

    def _require_lease(self, lease: HarnessRunLease, at: int) -> None:
        row = self.connection.execute(
            "SELECT * FROM run_leases WHERE harness_run_id=%s FOR UPDATE", (lease.harness_run_id,)
        ).fetchone()
        if (
            row is None
            or (row["owner_id"], row["lease_revision"], row["run_revision"], row["expires_at_ms"])
            != (lease.owner_id, lease.lease_revision, lease.run_revision, lease.expires_at_ms)
            or row["expires_at_ms"] <= at
        ):
            raise HarnessLeaseConflict("Harness Run lease expired or superseded")

    def _consume_lease(self, lease: HarnessRunLease) -> None:
        changed = self.connection.execute(
            "DELETE FROM run_leases WHERE harness_run_id=%s AND owner_id=%s "
            "AND lease_revision=%s AND run_revision=%s AND expires_at_ms=%s",
            (
                lease.harness_run_id,
                lease.owner_id,
                lease.lease_revision,
                lease.run_revision,
                lease.expires_at_ms,
            ),
        ).rowcount
        if changed != 1:
            raise HarnessLeaseConflict("Harness Run lease changed during batch")
