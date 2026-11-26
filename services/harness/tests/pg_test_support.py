"""Isolated real-PostgreSQL Harness test schema, never a production DB selector."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path


from ordivon_harness.agent_run import HarnessAgentRun
from tests.pg_fixture import pg_test_schema


@contextmanager
def isolated_harness_schema():
    with pg_test_schema() as database:
        with database.connect(initialize=True):
            pass
        yield database.dsn, database.schema


class PostgresAgentRunCase:
    """Test-only adaptation of historical root-shaped cases to the PG public API."""

    def set_up_pg(self) -> None:
        manager = isolated_harness_schema()
        self.pg_dsn, self.pg_schema = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)

    def create_pg(self, _historical_root: Path, contract, adapter_factory, **options):
        return HarnessAgentRun.create(
            self.pg_dsn, self.pg_schema, contract, adapter_factory, **options
        )

    def open_pg(self, _historical_root: Path, harness_run_id, adapter_factory, **options):
        return HarnessAgentRun.open(
            self.pg_dsn, self.pg_schema, harness_run_id, adapter_factory, **options
        )


class FakeNativeWorkspaceClaimClient:
    """Unit-test-only native tool double. NOT an authority or production fallback.

    Existing Gateway composition tests need a separate Workspace physical-pin
    transport now that unprotected Run birth correctly fails closed.
    """

    def __init__(self):
        self._claim = None

    def call_tool(self, name, args):
        from anc_canonical import canonical_digest

        if name == "workspace.get":
            return False, {
                "workspaceId": args["workspaceId"],
                "sourceStateDigest": canonical_digest({"testNative": args["workspaceId"]}),
            }
        if name == "workspace.claim.get":
            if self._claim is None:
                return True, {"error": {"code": "WORKSPACE_NOT_FOUND",
                                        "commitState": "not_committed"}}
            return False, dict(self._claim)
        if name == "workspace.claim.reserve":
            if self._claim is None:
                self._claim = {
                    "schemaVersion": 1,
                    "claimId": "wclaim-test-double",
                    "workspaceId": args["workspaceId"],
                    "runRef": args["runRef"],
                    "clientRequestId": args["clientRequestId"],
                    "storeRoot": "/test/native-workspace-store",
                    "sourceStateDigestAtReserve": args["expectedSourceStateDigest"],
                    "state": "held",
                }
            return False, dict(self._claim)
        if name == "workspace.claim.release":
            if self._claim is None:
                raise AssertionError("native claim absent")
            self._claim["state"] = "released"
            return False, dict(self._claim)
        raise AssertionError(f"unexpected native workspace claim call: {name}")
