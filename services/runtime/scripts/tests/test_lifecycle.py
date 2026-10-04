from __future__ import annotations

import argparse
import json
import os
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def initialize_registry(database: Path, workspace_id: str | None = None, activity_ms: int = 0) -> None:
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript(
            """
            CREATE TABLE schema_migrations(version INTEGER);
            INSERT INTO schema_migrations VALUES (4);
            CREATE TABLE jobs(
              job_id TEXT,
              workspace_id TEXT,
              resolution TEXT,
              created_at_ms INTEGER
            );
            CREATE TABLE attempts(
              attempt_id TEXT,
              job_id TEXT,
              state TEXT,
              created_at_ms INTEGER,
              started_at_ms INTEGER,
              finished_at_ms INTEGER
            );
            CREATE TABLE concurrency_reservations(attempt_id TEXT,state TEXT);
            """
        )
        if workspace_id is not None:
            connection.execute(
                "INSERT INTO jobs VALUES ('job-1', ?, 'succeeded', ?)",
                (workspace_id, activity_ms),
            )
            connection.execute(
                "INSERT INTO attempts VALUES ('attempt-1','job-1','succeeded',?,?,?)",
                (activity_ms, activity_ms, activity_ms),
            )
        connection.commit()


def init_repository(path: Path) -> str:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    (path / "README.md").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "baseline"], check=True)
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = runpy.run_path(str(REPO / "scripts/ordivon-runtime-lifecycle"))

    def test_lifecycle_inspect_cli_accepts_bounded_workspace_selection(self) -> None:
        previous = sys.argv
        sys.argv = [
            "ordivon-runtime-lifecycle",
            "inspect",
            "--database",
            "/tmp/registry.sqlite3",
            "--runtime-store-root",
            "/tmp/runtime",
            "--workspace-id",
            "ws-alpha",
            "--workspace-id",
            "ws-beta",
        ]
        try:
            args = self.module["parse_args"]()
        finally:
            sys.argv = previous
        self.assertEqual(args.command, "inspect")
        self.assertEqual(args.workspace_ids, ["ws-alpha", "ws-beta"])

    def test_lifecycle_inspect_cli_accepts_owner_workspace_references(self) -> None:
        previous = sys.argv
        sys.argv = [
            "ordivon-runtime-lifecycle",
            "inspect",
            "--database",
            "/tmp/registry.sqlite3",
            "--runtime-store-root",
            "/tmp/runtime",
            "--workspace-ref",
            "runtime:workspace:ws-alpha",
            "--workspace-ref",
            "runtime:workspace:ws-beta",
        ]
        try:
            args = self.module["parse_args"]()
        finally:
            sys.argv = previous
        self.assertEqual(args.workspace_refs, [
            "runtime:workspace:ws-alpha",
            "runtime:workspace:ws-beta",
        ])
        self.assertEqual(
            self.module["selected_workspace_ids"](args),
            ["ws-alpha", "ws-beta"],
        )

    def test_lifecycle_sweep_cli_accepts_bounded_workspace_selection(self) -> None:
        previous = sys.argv
        sys.argv = [
            "ordivon-runtime-lifecycle",
            "sweep",
            "--database",
            "/tmp/registry.sqlite3",
            "--runtime-store-root",
            "/tmp/runtime",
            "--workspace-id",
            "ws-alpha",
            "--workspace-ref",
            "runtime:workspace:ws-beta",
            "--workspace-ref",
            "runtime:workspace:ws-alpha",
            "--env-file",
            "/tmp/runtime.env",
            "--receipt-root",
            "/tmp/receipts",
            "--lock-file",
            "/tmp/lifecycle.lock",
            "--confirm-policy",
            "APPLY_WORKSPACE_RETENTION_POLICY",
        ]
        try:
            args = self.module["parse_args"]()
        finally:
            sys.argv = previous
        self.assertEqual(args.command, "sweep")
        self.assertEqual(args.workspace_ids, ["ws-alpha"])
        self.assertEqual(
            args.workspace_refs,
            [
                "runtime:workspace:ws-beta",
                "runtime:workspace:ws-alpha",
            ],
        )
        self.assertEqual(
            self.module["selected_workspace_ids"](args),
            ["ws-alpha", "ws-beta"],
        )

    def test_workspace_reference_parser_is_exact_and_fail_closed(self) -> None:
        parse = self.module["workspace_id_from_reference"]
        self.assertEqual(
            parse("runtime:workspace:ws-alpha_1.2"),
            "ws-alpha_1.2",
        )
        for invalid in (
            "workspace:ws-alpha",
            "runtime:workspace:",
            "runtime:workspace:.hidden",
            "runtime:workspace:ws:alpha",
            "runtime:workspace:ws alpha",
            "runtime:workspace:" + "w" * 97,
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(Exception):
                    parse(invalid)

    def test_owner_reference_and_workspace_id_selection_deduplicates(self) -> None:
        args = type(
            "Args",
            (),
            {
                "workspace_ids": ["ws-alpha", "ws-alpha"],
                "workspace_refs": [
                    "runtime:workspace:ws-beta",
                    "runtime:workspace:ws-alpha",
                ],
            },
        )()
        self.assertEqual(
            self.module["selected_workspace_ids"](args),
            ["ws-alpha", "ws-beta"],
        )

    def test_lifecycle_reclaim_inspect_forwards_bounded_workspace_selection(self) -> None:
        captured: list[list[str]] = []
        def fake_run_json(command: list[str], *, accepted_codes: tuple[int, ...] = (0,)) -> dict[str, object]:
            del accepted_codes
            captured.append(command)
            return {"schemaVersion": 1, "summary": {}, "candidates": []}

        function_globals = self.module["reclaim_inspect"].__globals__
        original = function_globals["run_json"]
        function_globals["run_json"] = fake_run_json
        args = type(
            "Args",
            (),
            {
                "database": Path("/tmp/registry.sqlite3"),
                "runtime_store_root": Path("/tmp/runtime"),
                "workspace_root": None,
                "busy_timeout_ms": 5_000,
                "measure_bytes": False,
                "workspace_ids": ["ws-alpha"],
                "workspace_refs": [
                    "runtime:workspace:ws-beta",
                    "runtime:workspace:ws-alpha",
                ],
            },
        )()
        try:
            self.module["reclaim_inspect"](args)
        finally:
            function_globals["run_json"] = original
        command = captured[0]
        self.assertEqual(
            [command[index + 1] for index, value in enumerate(command[:-1]) if value == "--workspace-id"],
            ["ws-alpha", "ws-beta"],
        )

    def test_open_record_accepts_identity_derived_from_record_location(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record_path = root / "workspace-records" / "compact.json"
            record_path.parent.mkdir()
            record_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "sourceRepo": str(root / "source"),
                        "sourceRevision": "a" * 40,
                        "createdUnixMs": 1,
                    }
                ),
                encoding="utf-8",
            )
            value = self.module["load_open_record"](
                record_path,
                "compact",
                root / "workspaces" / "compact",
            )
            self.assertNotIn("workspaceId", value)
            self.assertNotIn("workspacePath", value)

    def test_trusted_tmp_presentation_matches_runtime_hash_vector(self) -> None:
        self.assertEqual(
            self.module["trusted_tmp_presentation_path"](Path("/tmp"), "workspace-env"),
            Path("/tmp/ordivon-t/3536fc95f765287c720c"),
        )

    def test_trusted_tmp_presentation_separates_runtime_store_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_store = root / "store-a"
            second_store = root / "store-b"
            first_store.mkdir()
            second_store.mkdir()
            first = self.module["trusted_tmp_presentation_path"](first_store, "same-workspace-id")
            second = self.module["trusted_tmp_presentation_path"](second_store, "same-workspace-id")
            self.assertNotEqual(first, second)
            self.assertEqual(len(str(first)), 35)
            self.assertEqual(len(str(second)), 35)

    def test_trusted_tmp_presentation_converges_equivalent_store_spelling(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root / "store"
            store.mkdir()
            alias = root / "store-link"
            alias.symlink_to(store, target_is_directory=True)
            direct = self.module["trusted_tmp_presentation_path"](store, "same-workspace-id")
            through_alias = self.module["trusted_tmp_presentation_path"](alias, "same-workspace-id")
            self.assertEqual(direct, through_alias)

    def test_policy_numbers_follow_real_representation_not_legacy_round_limits(self) -> None:
        self.assertEqual(cls_timeout := self.module["positive_timeout"]("60001"), 60_001)
        self.assertEqual(cls_timeout, 60_001)
        self.assertEqual(self.module["positive_timeout"]("2147483647"), 2_147_483_647)
        with self.assertRaises(Exception):
            self.module["positive_timeout"]("2147483648")
        self.assertEqual(self.module["nonnegative_float"]("87601"), 87_601.0)
        with self.assertRaises(Exception):
            self.module["nonnegative_float"]("inf")
        with self.assertRaises(Exception):
            self.module["nonnegative_float"]("-1")

    def test_carrier_projection_preserves_physical_and_semantic_boundaries(self) -> None:
        cases = (
            (
                {
                    "classification": "closable",
                    "policyEligible": True,
                    "retentionHours": 24.0,
                },
                "CLEAN_IDLE",
                "DECLARE_CLOSE_CLEAN_OR_RETAIN",
                "ELIGIBLE",
            ),
            (
                {"classification": "blocked_dirty", "policyEligible": False},
                "DIRTY_IDLE",
                "DECLARE_DIRTY_HANDOFF_OR_CHECKPOINT",
                "NOT_APPLICABLE",
            ),
            (
                {
                    "classification": "blocked_dirty",
                    "policyEligible": True,
                    "retentionHours": 48.0,
                    "forceCloseDirtyAfterRetention": True,
                },
                "DIRTY_IDLE",
                "POLICY_FORCE_CLOSE_DIRTY",
                "ELIGIBLE",
            ),
            (
                {"classification": "blocked_unintegrated", "policyEligible": False},
                "CLEAN_IDLE_UNINTEGRATED",
                "INTEGRATE_OR_EXPLICITLY_DISPOSITION_SOURCE",
                "NOT_APPLICABLE",
            ),
            (
                {
                    "classification": "blocked_unintegrated",
                    "policyEligible": True,
                    "retentionHours": 72.0,
                    "forceCloseUnintegratedAfterRetention": True,
                },
                "CLEAN_IDLE_UNINTEGRATED",
                "POLICY_FORCE_CLOSE_UNINTEGRATED",
                "ELIGIBLE",
            ),
            (
                {"classification": "blocked_active", "policyEligible": False},
                "ACTIVE_DIRTY_STATE_UNINSPECTED",
                "OBSERVE_OR_RECONCILE_ACTIVE_JOB",
                "NOT_APPLICABLE",
            ),
            (
                {
                    "classification": "stale_record",
                    "policyEligible": False,
                    "retentionHours": 24.0,
                },
                "MISSING_WITH_OPEN_RECORD",
                "RECONCILE_STALE_RECORD",
                "WAITING",
            ),
            (
                {"classification": "unknown", "policyEligible": False},
                "UNPROVEN",
                "INSPECT_BEFORE_DISPOSITION",
                "NOT_APPLICABLE",
            ),
        )
        for item, physical_state, next_step, retention_state in cases:
            with self.subTest(classification=item["classification"]):
                projection = self.module["carrier_projection"](item)
                self.assertEqual(projection["physicalState"], physical_state)
                self.assertEqual(projection["nextProtocolStep"], next_step)
                self.assertEqual(
                    projection["retentionPolicyState"], retention_state
                )
                self.assertFalse(projection["semanticCompletionEvaluated"])
                self.assertIn("Host/owner", projection["interpretation"])

    def test_hard_lifetime_can_expire_despite_recent_activity(self) -> None:
        policy = {
            "schemaVersion": 1,
            "defaultClass": "ephemeral",
            "classes": {
                "ephemeral": {
                    "retentionHours": 72,
                    "maxLifetimeHours": 168,
                    "forceCloseDirtyAfterRetention": True,
                    "forceCloseUnintegratedAfterRetention": True,
                    "forceCloseAfterMaxLifetime": True,
                }
            },
            "rules": [],
            "sourceRepoAliases": {},
        }
        observed = self.module["retention_class"](policy, "ws-hard-ttl")
        self.assertEqual(observed, ("ephemeral", 72.0, 168.0, True, True, True))

    def _prepared_r54_candidate(
        self,
        classification: str,
        *,
        created_age_hours: float = 100.0,
        last_activity_age_hours: float = 73.0,
    ) -> dict[str, object]:
        now_ms = int(__import__("time").time() * 1000)
        return {
            "workspaceId": "ws-r54",
            "classification": classification,
            "createdUnixMs": int(now_ms - created_age_hours * 3_600_000),
            "lastActivityUnixMs": int(now_ms - last_activity_age_hours * 3_600_000),
            "activityMarker": "sha256:" + "a" * 64,
            "retentionHours": 72.0,
            "maxLifetimeHours": 168.0,
            "forceCloseDirtyAfterRetention": True,
            "forceCloseUnintegratedAfterRetention": True,
            "forceCloseAfterMaxLifetime": True,
            "canonicalHeadRevision": "c" * 40,
            "sourceRepo": "/tmp/canonical",
            "expectedSourceStateDigest": "sha256:" + "d" * 64,
        }

    def test_r54_under_fence_skips_renewed_l1_activity_for_all_close_classes(self) -> None:
        revalidate = self.module["revalidate_prepared_item_under_fence"]
        globals_ = revalidate.__globals__
        original_registry = globals_["registry_workspace"]
        original_head = globals_["canonical_head_revision"]
        try:
            for classification in (
                "closable",
                "blocked_dirty",
                "blocked_unintegrated",
            ):
                with self.subTest(classification=classification):
                    prepared = self._prepared_r54_candidate(classification)
                    globals_["registry_workspace"] = lambda *_args, **_kwargs: {
                        "workspaceId": "ws-r54",
                        "activeJobIds": [],
                        "lastActivityMs": int(__import__("time").time() * 1000),
                        "activityMarker": "sha256:" + "b" * 64,
                    }
                    globals_["canonical_head_revision"] = lambda _item: "c" * 40
                    retained, _state = revalidate(
                        type("Args", (), {"database": Path("/unused"), "busy_timeout_ms": 1})(),
                        prepared,
                    )
                    self.assertIsNotNone(retained)
                    self.assertEqual(
                        retained["reason"], "workspace_activity_changed_after_plan"
                    )
        finally:
            globals_["registry_workspace"] = original_registry
            globals_["canonical_head_revision"] = original_head

    def test_r54_under_fence_hard_max_survives_renewed_activity(self) -> None:
        revalidate = self.module["revalidate_prepared_item_under_fence"]
        globals_ = revalidate.__globals__
        original_registry = globals_["registry_workspace"]
        original_head = globals_["canonical_head_revision"]
        try:
            prepared = self._prepared_r54_candidate(
                "blocked_unintegrated", created_age_hours=169.0
            )
            globals_["registry_workspace"] = lambda *_args, **_kwargs: {
                "workspaceId": "ws-r54",
                "activeJobIds": [],
                "lastActivityMs": int(__import__("time").time() * 1000),
                "activityMarker": "sha256:" + "e" * 64,
            }
            globals_["canonical_head_revision"] = lambda _item: "c" * 40
            retained, state = revalidate(
                type("Args", (), {"database": Path("/unused"), "busy_timeout_ms": 1})(),
                prepared,
            )
            self.assertIsNone(retained)
            self.assertTrue(state["hardLifetimeExpired"])
        finally:
            globals_["registry_workspace"] = original_registry
            globals_["canonical_head_revision"] = original_head

    def test_r54_under_fence_vetoes_active_job_and_canonical_head_drift(self) -> None:
        revalidate = self.module["revalidate_prepared_item_under_fence"]
        globals_ = revalidate.__globals__
        original_registry = globals_["registry_workspace"]
        original_head = globals_["canonical_head_revision"]
        prepared = self._prepared_r54_candidate("closable")
        try:
            globals_["registry_workspace"] = lambda *_args, **_kwargs: {
                "workspaceId": "ws-r54",
                "activeJobIds": ["job-live"],
                "lastActivityMs": prepared["lastActivityUnixMs"],
                "activityMarker": prepared["activityMarker"],
            }
            globals_["canonical_head_revision"] = lambda _item: "c" * 40
            retained, _ = revalidate(
                type("Args", (), {"database": Path("/unused"), "busy_timeout_ms": 1})(),
                prepared,
            )
            self.assertEqual(retained["reason"], "workspace_active_after_plan")

            globals_["registry_workspace"] = lambda *_args, **_kwargs: {
                "workspaceId": "ws-r54",
                "activeJobIds": [],
                "lastActivityMs": prepared["lastActivityUnixMs"],
                "activityMarker": prepared["activityMarker"],
            }
            globals_["canonical_head_revision"] = lambda _item: "f" * 40
            retained, _ = revalidate(
                type("Args", (), {"database": Path("/unused"), "busy_timeout_ms": 1})(),
                prepared,
            )
            self.assertEqual(
                retained["reason"], "canonicalHeadRevision_changed_after_plan"
            )
        finally:
            globals_["registry_workspace"] = original_registry
            globals_["canonical_head_revision"] = original_head

    def test_admission_and_runtime_authority_are_exact_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO) as temporary:
            root = Path(temporary)
            registry = root / "registry"
            runtime = root / "runtime"
            registry.mkdir()
            runtime.mkdir()
            database = registry / "registry.sqlite3"
            database.touch()
            env_file = root / "runtime.env"
            env_file.write_text(
                f"ORDIVON_REGISTRY_ROOT={registry}\n"
                f"ORDIVON_STORE_ROOT={runtime}\n"
                "ORDIVON_BIND=127.0.0.1:1\n"
                "ORDIVON_BEARER_TOKEN=test\n",
                encoding="utf-8",
            )
            self.assertEqual(
                self.module["validate_runtime_authority"](
                    database, runtime, env_file
                ),
                registry / "admission.lock",
            )
            with self.assertRaisesRegex(RuntimeError, "store authority"):
                self.module["validate_runtime_authority"](
                    database, root / "other-store", env_file
                )
            wrong_database = registry / "other.sqlite3"
            wrong_database.touch()
            with self.assertRaisesRegex(RuntimeError, "Registry authority"):
                self.module["validate_runtime_authority"](
                    wrong_database, runtime, env_file
                )

    def test_r54_close_passes_exact_source_digest_for_clean_and_force(self) -> None:
        close_once = self.module["close_workspace_once"]
        globals_ = close_once.__globals__
        original_client = globals_["runtime_client"]
        calls: list[dict[str, object]] = []

        class FakeClient:
            def call_tool(self, name, arguments):
                self_outer.assertEqual(name, "workspace.close")
                calls.append(dict(arguments))
                return {"closureDisposition": "removed", "removed": True}

        self_outer = self
        try:
            globals_["runtime_client"] = lambda *_args, **_kwargs: FakeClient()
            for force in (False, True):
                calls.clear()
                close_once(
                    Path("/unused"),
                    "ws-close",
                    force=force,
                    expected_source_state_digest="sha256:" + "d" * 64,
                )
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0]["force"], force)
                self.assertEqual(
                    calls[0]["expectedSourceStateDigest"], "sha256:" + "d" * 64
                )
        finally:
            globals_["runtime_client"] = original_client

    def test_r54_effect_binds_authority_and_close_client_to_one_env_snapshot(self) -> None:
        attempt = self.module["_attempt_prepared_close"]
        globals_ = attempt.__globals__
        originals = {
            name: globals_[name]
            for name in (
                "exclusive_admission_fence",
                "load_environment_file",
                "validate_runtime_authority_snapshot",
                "runtime_client_from_environment",
                "revalidate_prepared_item_under_fence",
                "close_workspace_once",
            )
        }
        events: list[str] = []
        environment = {
            "ORDIVON_REGISTRY_ROOT": "/authority-a/registry",
            "ORDIVON_STORE_ROOT": "/authority-a/store",
            "ORDIVON_BIND": "127.0.0.1:1",
            "ORDIVON_BEARER_TOKEN": "test",
        }
        client = object()

        from contextlib import contextmanager

        @contextmanager
        def fake_fence(_database):
            events.append("enter")
            try:
                yield
            finally:
                events.append("exit")

        def load_env(_path):
            events.append("load-env")
            return environment

        def validate(database, store, observed):
            self.assertIs(observed, environment)
            self.assertEqual(database, Path("/authority-a/registry/registry.sqlite3"))
            self.assertEqual(store, Path("/authority-a/store"))
            events.append("validate-authority")
            return Path("/authority-a/registry/admission.lock")

        def make_client(observed, *, client_name):
            self.assertIs(observed, environment)
            self.assertEqual(client_name, "ordivon-runtime-lifecycle-close")
            events.append("build-client")
            return client

        def close(*_args, **kwargs):
            self.assertIs(kwargs["client"], client)
            self.assertEqual(
                kwargs["expected_source_state_digest"], "sha256:" + "d" * 64
            )
            events.append("close")
            return {"closureDisposition": "removed", "removed": True}

        try:
            globals_["exclusive_admission_fence"] = fake_fence
            globals_["load_environment_file"] = load_env
            globals_["validate_runtime_authority_snapshot"] = validate
            globals_["runtime_client_from_environment"] = make_client
            globals_["revalidate_prepared_item_under_fence"] = (
                lambda _args, _item: (None, {"bounded": True})
            )
            globals_["close_workspace_once"] = close
            prepared = self._prepared_r54_candidate("blocked_dirty")
            status, _value = attempt(
                type(
                    "Args",
                    (),
                    {
                        "database": Path("/authority-a/registry/registry.sqlite3"),
                        "runtime_store_root": Path("/authority-a/store"),
                        "env_file": Path("/unused.env"),
                    },
                )(),
                prepared,
            )
            self.assertEqual(status, "closed")
            self.assertEqual(
                events,
                [
                    "enter",
                    "load-env",
                    "validate-authority",
                    "build-client",
                    "close",
                    "exit",
                ],
            )
        finally:
            for name, value in originals.items():
                globals_[name] = value

    def test_r54_unknown_close_releases_fence_before_replay(self) -> None:
        attempt = self.module["_attempt_prepared_close"]
        globals_ = attempt.__globals__
        originals = {
            name: globals_[name]
            for name in (
                "exclusive_admission_fence",
                "load_environment_file",
                "validate_runtime_authority_snapshot",
                "runtime_client_from_environment",
                "revalidate_prepared_item_under_fence",
                "close_workspace_once",
            )
        }
        events: list[str] = []
        environment = {
            "ORDIVON_REGISTRY_ROOT": "/authority-a/registry",
            "ORDIVON_STORE_ROOT": "/authority-a/store",
            "ORDIVON_BIND": "127.0.0.1:1",
            "ORDIVON_BEARER_TOKEN": "test",
        }

        from contextlib import contextmanager

        @contextmanager
        def fake_fence(_database):
            events.append("enter")
            try:
                yield
            finally:
                events.append("exit")

        try:
            globals_["exclusive_admission_fence"] = fake_fence
            globals_["load_environment_file"] = lambda _path: environment
            globals_["validate_runtime_authority_snapshot"] = lambda *_args: Path(
                "/authority-a/registry/admission.lock"
            )
            globals_["runtime_client_from_environment"] = (
                lambda *_args, **_kwargs: object()
            )
            globals_["revalidate_prepared_item_under_fence"] = (
                lambda _args, _item: (None, {"bounded": True})
            )
            globals_["close_workspace_once"] = lambda *_args, **_kwargs: (_ for _ in ()).throw(
                self.module["WorkspaceCloseDeliveryUncertain"](
                    "ws-r54", "sha256:" + "d" * 64, TimeoutError("lost")
                )
            )
            prepared = self._prepared_r54_candidate("blocked_dirty")
            status, _value = attempt(
                type(
                    "Args",
                    (),
                    {
                        "database": Path("/authority-a/registry/registry.sqlite3"),
                        "runtime_store_root": Path("/authority-a/store"),
                        "env_file": Path("/unused.env"),
                    },
                )(),
                prepared,
            )
            self.assertEqual(status, "uncertain")
            self.assertEqual(events, ["enter", "exit"])
        finally:
            for name, value in originals.items():
                globals_[name] = value

    def test_r54_unknown_replay_refences_and_uses_fresh_env_snapshot(self) -> None:
        apply_candidate = self.module["apply_prepared_candidate"]
        globals_ = apply_candidate.__globals__
        originals = {
            name: globals_[name]
            for name in (
                "exclusive_admission_fence",
                "load_environment_file",
                "validate_runtime_authority_snapshot",
                "runtime_client_from_environment",
                "revalidate_prepared_item_under_fence",
                "close_workspace_once",
                "closed_workspace_tombstone",
            )
        }
        events: list[str] = []
        envs = [
            {
                "ORDIVON_REGISTRY_ROOT": "/authority-a/registry",
                "ORDIVON_STORE_ROOT": "/authority-a/store",
                "ORDIVON_BIND": "127.0.0.1:1",
                "ORDIVON_BEARER_TOKEN": "first",
            },
            {
                "ORDIVON_REGISTRY_ROOT": "/authority-a/registry",
                "ORDIVON_STORE_ROOT": "/authority-a/store",
                "ORDIVON_BIND": "127.0.0.1:1",
                "ORDIVON_BEARER_TOKEN": "second",
            },
        ]
        load_count = 0
        close_count = 0

        from contextlib import contextmanager

        @contextmanager
        def fake_fence(_database):
            events.append("enter")
            try:
                yield
            finally:
                events.append("exit")

        def load_env(_path):
            nonlocal load_count
            observed = envs[load_count]
            load_count += 1
            events.append(f"load-{load_count}")
            return observed

        def validate(_database, _store, observed):
            self.assertIs(observed, envs[load_count - 1])
            events.append(f"validate-{load_count}")
            return Path("/authority-a/registry/admission.lock")

        def make_client(observed, *, client_name):
            self.assertIs(observed, envs[load_count - 1])
            events.append(f"client-{load_count}")
            return {"generation": load_count, "name": client_name}

        def close(*_args, **kwargs):
            nonlocal close_count
            close_count += 1
            self.assertEqual(
                kwargs["expected_source_state_digest"], "sha256:" + "d" * 64
            )
            self.assertEqual(kwargs["client"]["generation"], close_count)
            events.append(f"close-{close_count}")
            if close_count == 1:
                raise self.module["WorkspaceCloseDeliveryUncertain"](
                    "ws-r54",
                    "sha256:" + "d" * 64,
                    TimeoutError("lost"),
                )
            return {
                "closureDisposition": "removed",
                "removed": True,
                "sourceStateDigest": "sha256:" + "d" * 64,
            }

        def tombstone(*_args, **_kwargs):
            events.append("tombstone")
            return None

        try:
            globals_["exclusive_admission_fence"] = fake_fence
            globals_["load_environment_file"] = load_env
            globals_["validate_runtime_authority_snapshot"] = validate
            globals_["runtime_client_from_environment"] = make_client
            globals_["revalidate_prepared_item_under_fence"] = (
                lambda _args, _item: (None, {"bounded": True})
            )
            globals_["close_workspace_once"] = close
            globals_["closed_workspace_tombstone"] = tombstone
            prepared = self._prepared_r54_candidate("blocked_dirty")
            result = apply_candidate(
                type(
                    "Args",
                    (),
                    {
                        "database": Path("/authority-a/registry/registry.sqlite3"),
                        "runtime_store_root": Path("/authority-a/store"),
                        "env_file": Path("/unused.env"),
                    },
                )(),
                prepared,
            )
            self.assertTrue(result["deliveryReconciled"])
            self.assertEqual(result["responseLossReconciledBy"], "same_identity_replay")
            self.assertEqual(load_count, 2)
            self.assertEqual(close_count, 2)
            self.assertEqual(
                events,
                [
                    "enter",
                    "load-1",
                    "validate-1",
                    "client-1",
                    "close-1",
                    "exit",
                    "tombstone",
                    "enter",
                    "load-2",
                    "validate-2",
                    "client-2",
                    "close-2",
                    "exit",
                ],
            )
        finally:
            for name, value in originals.items():
                globals_[name] = value

    def test_r54_sweep_authority_mismatch_blocks_stale_subordinate_effect(self) -> None:
        sweep = self.module["sweep"]
        globals_ = sweep.__globals__
        original_reclaim = globals_["reclaim_apply_selected"]
        for mismatch in ("registry", "store"):
            with self.subTest(mismatch=mismatch), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                registry = root / "registry"
                runtime = root / "runtime"
                registry.mkdir()
                runtime.mkdir()
                database = registry / "registry.sqlite3"
                database.touch()
                other_database = registry / "other.sqlite3"
                other_database.touch()
                other_store = root / "other-store"
                other_store.mkdir()
                env_file = root / "runtime.env"
                env_file.write_text(
                    f"ORDIVON_REGISTRY_ROOT={registry}\n"
                    f"ORDIVON_STORE_ROOT={runtime}\n"
                    "ORDIVON_BIND=127.0.0.1:1\n"
                    "ORDIVON_BEARER_TOKEN=test\n",
                    encoding="utf-8",
                )
                called = False

                def forbidden_reclaim(*_args, **_kwargs):
                    nonlocal called
                    called = True
                    self.fail("authority mismatch reached stale subordinate reclaim")

                globals_["reclaim_apply_selected"] = forbidden_reclaim
                args = type(
                    "Args",
                    (),
                    {
                        "confirm_policy": "APPLY_WORKSPACE_RETENTION_POLICY",
                        "database": other_database if mismatch == "registry" else database,
                        "runtime_store_root": other_store if mismatch == "store" else runtime,
                        "env_file": env_file,
                        "lock_file": root / "lifecycle.lock",
                    },
                )()
                expected = (
                    "Registry authority" if mismatch == "registry" else "store authority"
                )
                with self.assertRaisesRegex(RuntimeError, expected):
                    sweep(args)
                self.assertFalse(called)
        globals_["reclaim_apply_selected"] = original_reclaim

    def test_packaged_lifecycle_unit_only_invokes_supported_lifecycle_commands(self) -> None:
        unit = (REPO / "packaging/systemd/ordivon-runtime-lifecycle.service").read_text(
            encoding="utf-8"
        )
        marker = "/ordivon-runtime-lifecycle "
        commands = [
            line.split(marker, 1)[1].split()[0]
            for line in unit.splitlines()
            if marker in line
        ]
        self.assertTrue(commands)
        lifecycle_line = next(
            line for line in unit.splitlines() if "/ordivon-runtime-lifecycle sweep " in line
        )
        self.assertNotIn("--measure-bytes", lifecycle_line)
        self.assertIn("SuccessExitStatus=1 2", unit)
        help_result = subprocess.run(
            [sys.executable, "scripts/ordivon-runtime-lifecycle", "--help"],
            cwd=REPO,
            check=True,
            text=True,
            capture_output=True,
        )
        for command in commands:
            self.assertIn(command, help_result.stdout)
        self.assertNotIn("inputs-sweep", commands)

    def test_inspect_applies_retention_class_and_last_activity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            records = runtime / "workspace-records"
            workspaces = runtime / "workspaces"
            records.mkdir(parents=True)
            workspaces.mkdir()
            database = root / "registry.sqlite3"
            initialize_registry(database, "named-audit-workspace", 2_000)
            workspace = workspaces / "named-audit-workspace"
            revision = init_repository(workspace)
            (records / "named-audit-workspace.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "workspaceId": "named-audit-workspace",
                        "sourceRepo": str(workspace),
                        "sourceRevision": revision,
                        "workspacePath": str(workspace),
                        "createdUnixMs": 1_000,
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-lifecycle",
                    "inspect",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                ],
                cwd=REPO,
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(result.stdout)
            item = report["candidates"][0]
            self.assertEqual(item["retentionClass"], "ephemeral")
            self.assertEqual(item["retentionHours"], 72.0)
            self.assertEqual(item["lastActivityUnixMs"], 2_000)
            self.assertEqual(item["retentionBasisUnixMs"], 2_000)
            self.assertTrue(item["policyEligible"])
            self.assertEqual(
                item["carrierProjection"]["physicalState"], "CLEAN_IDLE"
            )
            self.assertEqual(
                item["carrierProjection"]["nextProtocolStep"],
                "DECLARE_CLOSE_CLEAN_OR_RETAIN",
            )
            self.assertFalse(
                item["carrierProjection"]["semanticCompletionEvaluated"]
            )


    def test_inspect_marks_expired_dirty_ephemeral_force_close_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            records = runtime / "workspace-records"
            workspaces = runtime / "workspaces"
            records.mkdir(parents=True)
            workspaces.mkdir()
            database = root / "registry.sqlite3"
            initialize_registry(database, "dirty-expired", 1)
            workspace = workspaces / "dirty-expired"
            revision = init_repository(workspace)
            (workspace / "dirty.txt").write_text("dirty\n", encoding="utf-8")
            (records / "dirty-expired.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "workspaceId": "dirty-expired",
                        "sourceRepo": str(workspace),
                        "sourceRevision": revision,
                        "workspacePath": str(workspace),
                        "createdUnixMs": 1,
                    }
                ),
                encoding="utf-8",
            )
            policy = root / "policy.json"
            policy.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "classes": {
                            "ephemeral": {
                                "retentionHours": 0,
                                "forceCloseDirtyAfterRetention": True,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-lifecycle",
                    "inspect",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                    "--policy-file",
                    str(policy),
                ],
                cwd=REPO,
                check=True,
                text=True,
                capture_output=True,
            )
            item = json.loads(result.stdout)["candidates"][0]
            self.assertEqual(item["classification"], "blocked_dirty")
            self.assertTrue(item["forceCloseDirtyAfterRetention"])
            self.assertTrue(item["policyEligible"])
            self.assertEqual(
                item["carrierProjection"]["nextProtocolStep"],
                "POLICY_FORCE_CLOSE_DIRTY",
            )

    def test_sweep_selects_only_policy_expired_reclaimable_workspaces(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO) as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            records = runtime / "workspace-records"
            workspaces = runtime / "workspaces"
            records.mkdir(parents=True)
            workspaces.mkdir()
            database = root / "registry.sqlite3"
            initialize_registry(database, "ws-expired", 1)
            workspace = workspaces / "ws-expired"
            revision = init_repository(workspace)
            (records / "ws-expired.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "workspaceId": "ws-expired",
                        "sourceRepo": str(workspace),
                        "sourceRevision": revision,
                        "workspacePath": str(workspace),
                        "createdUnixMs": 1,
                    }
                ),
                encoding="utf-8",
            )
            policy = root / "policy.json"
            policy.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "classes": {"ephemeral": {"retentionHours": 0}},
                    }
                ),
                encoding="utf-8",
            )
            fake_reclaim = root / "fake-reclaim"
            fake_reclaim.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "command = sys.argv[1]\n"
                "if command == 'inspect':\n"
                " print(json.dumps({'schemaVersion':1,'summary':{'counts':{'stale_record':1},'estimatedBytes':{'stale_record':10}},'candidates':[{'workspaceId':'ws-expired','classification':'stale_record','createdUnixMs':1,'estimatedBytes':10}]}))\n"
                "elif command == 'apply':\n"
                " ids=[sys.argv[i+1] for i,v in enumerate(sys.argv) if v == '--workspace-id']\n"
                " print(json.dumps({'schemaVersion':1,'status':'completed','actions':[{'workspaceId':x,'action':'workspace_closed'} for x in ids],'failures':[],'receipt':'/fake/reclaim'}))\n"
                "else: raise SystemExit(1)\n",
                encoding="utf-8",
            )
            fake_reclaim.chmod(0o755)
            env_file = root / "runtime.env"
            env_file.write_text(
                f"ORDIVON_REGISTRY_ROOT={root}\n"
                f"ORDIVON_STORE_ROOT={runtime}\n"
                "ORDIVON_BIND=127.0.0.1:1\n"
                "ORDIVON_BEARER_TOKEN=test\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["ORDIVON_RUNTIME_RECLAIM"] = str(fake_reclaim)
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-lifecycle",
                    "sweep",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                    "--policy-file",
                    str(policy),
                    "--env-file",
                    str(env_file),
                    "--receipt-root",
                    str(root / "receipts"),
                    "--lock-file",
                    str(root / "lifecycle.lock"),
                    "--confirm-policy",
                    "APPLY_WORKSPACE_RETENTION_POLICY",
                ],
                cwd=REPO,
                env=environment,
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["selectedWorkspaceIds"], ["ws-expired"])
            self.assertEqual(report["actions"][0]["workspaceId"], "ws-expired")

    def test_repair_rebinds_worktree_after_source_repository_rename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old_repo = root / "old-repo"
            revision = init_repository(old_repo)
            runtime = root / "runtime"
            records = runtime / "workspace-records"
            workspaces = runtime / "workspaces"
            records.mkdir(parents=True)
            workspaces.mkdir()
            workspace_id = "renamed-worktree"
            workspace = workspaces / workspace_id
            subprocess.run(
                ["git", "-C", str(old_repo), "worktree", "add", "--detach", str(workspace), revision],
                check=True,
                capture_output=True,
            )
            record = records / f"{workspace_id}.json"
            record.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "workspaceId": workspace_id,
                        "sourceRepo": str(old_repo),
                        "sourceRevision": revision,
                        "workspacePath": str(workspace),
                        "createdUnixMs": 1,
                    }
                ),
                encoding="utf-8",
            )
            new_repo = root / "new-repo"
            old_repo.rename(new_repo)
            database = root / "registry.sqlite3"
            initialize_registry(database)
            policy = root / "policy.json"
            policy.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "sourceRepoAliases": {str(old_repo): str(new_repo)},
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-lifecycle",
                    "repair",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                    "--policy-file",
                    str(policy),
                    "--receipt-root",
                    str(root / "receipts"),
                    "--lock-file",
                    str(root / "lifecycle.lock"),
                    "--workspace-id",
                    workspace_id,
                    "--confirm-policy",
                    "REPAIR_WORKSPACE_IDENTITIES",
                ],
                cwd=REPO,
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["actions"][0]["action"], "worktree_repaired")
            updated = json.loads(record.read_text(encoding="utf-8"))
            self.assertEqual(updated["sourceRepo"], str(new_repo.resolve()))
            observed = subprocess.run(
                ["git", "-C", str(workspace), "rev-parse", "HEAD"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.strip()
            self.assertEqual(observed, revision)

    def test_repair_can_quarantine_unrepairable_workspace_with_tombstone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            records = runtime / "workspace-records"
            workspaces = runtime / "workspaces"
            records.mkdir(parents=True)
            workspaces.mkdir()
            workspace_id = "broken-quarantine-tmp-presentation"
            workspace = workspaces / workspace_id
            workspace.mkdir()
            (workspace / "important.txt").write_text("preserve me\n", encoding="utf-8")
            tmp_backing = (
                self.module["canonical_runtime_store_root"](runtime)
                / "cache"
                / "tmp"
                / workspace_id
            )
            tmp_backing.mkdir(parents=True)
            tmp_presentation = self.module["trusted_tmp_presentation_path"](runtime, workspace_id)
            tmp_presentation.parent.mkdir(mode=0o700, exist_ok=True)
            try:
                tmp_presentation.unlink()
            except FileNotFoundError:
                pass
            tmp_presentation.symlink_to(tmp_backing, target_is_directory=True)
            record = records / f"{workspace_id}.json"
            record.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "workspaceId": workspace_id,
                        "sourceRepo": str(root / "missing-source"),
                        "sourceRevision": "a" * 40,
                        "workspacePath": str(workspace),
                        "createdUnixMs": 1,
                    }
                ),
                encoding="utf-8",
            )
            database = root / "registry.sqlite3"
            initialize_registry(database)
            quarantine = root / "quarantine"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-lifecycle",
                    "repair",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                    "--receipt-root",
                    str(root / "receipts"),
                    "--lock-file",
                    str(root / "lifecycle.lock"),
                    "--workspace-id",
                    workspace_id,
                    "--confirm-policy",
                    "REPAIR_WORKSPACE_IDENTITIES",
                    "--quarantine-unrepairable",
                    "--quarantine-root",
                    str(quarantine),
                    "--confirm-quarantine",
                    "QUARANTINE_BROKEN_WORKSPACES",
                ],
                cwd=REPO,
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["actions"][0]["action"], "workspace_quarantined")
            tombstone = json.loads(record.read_text(encoding="utf-8"))
            self.assertEqual(tombstone, {"schemaVersion": 1, "state": "closed"})
            quarantined = Path(report["actions"][0]["quarantinePath"])
            self.assertEqual((quarantined / "important.txt").read_text(), "preserve me\n")
            self.assertEqual(report["actions"][0]["removedTmpPresentation"], str(tmp_presentation))
            self.assertFalse(tmp_presentation.is_symlink())

    def test_repair_explicitly_quarantines_true_orphan_without_inventing_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            revision = init_repository(source)
            runtime = root / "runtime"
            records = runtime / "workspace-records"
            workspaces = runtime / "workspaces"
            records.mkdir(parents=True)
            workspaces.mkdir()
            workspace_id = "true-orphan-worktree"
            workspace = workspaces / workspace_id
            subprocess.run(
                ["git", "-C", str(source), "worktree", "add", "--detach", str(workspace), revision],
                check=True, capture_output=True,
            )
            (workspace / "important-untracked.txt").write_text("preserve uncertain bytes\n", encoding="utf-8")
            database = root / "registry.sqlite3"
            initialize_registry(database)
            quarantine = root / "quarantine"
            result = subprocess.run(
                [
                    sys.executable, "scripts/ordivon-runtime-lifecycle", "repair",
                    "--database", str(database),
                    "--runtime-store-root", str(runtime),
                    "--receipt-root", str(root / "receipts"),
                    "--lock-file", str(root / "lifecycle.lock"),
                    "--workspace-id", workspace_id,
                    "--confirm-policy", "REPAIR_WORKSPACE_IDENTITIES",
                    "--quarantine-unrepairable",
                    "--quarantine-root", str(quarantine),
                    "--confirm-quarantine", "QUARANTINE_BROKEN_WORKSPACES",
                ],
                cwd=REPO, check=True, text=True, capture_output=True,
            )
            report = json.loads(result.stdout)
            action = report["actions"][0]
            self.assertEqual(action["action"], "orphan_workspace_quarantined")
            self.assertEqual(action["sourceIdentityStanding"], "UNKNOWN_NO_RUNTIME_RECORD")
            self.assertFalse(workspace.exists())
            target = Path(action["quarantinePath"])
            self.assertEqual((target / "important-untracked.txt").read_text(), "preserve uncertain bytes\n")
            self.assertEqual(
                subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip(),
                revision,
            )
            self.assertEqual(action["gitRegistrationRepair"]["standing"], "REPAIRED")
            worktrees = subprocess.run(["git", "-C", str(source), "worktree", "list", "--porcelain"], check=True, text=True, capture_output=True).stdout
            self.assertIn(str(target), worktrees)
            self.assertNotIn(str(workspace) + "\n", worktrees)
            tombstone = json.loads((records / f"{workspace_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(tombstone, {"schemaVersion": 1, "state": "closed"})
            inspect = subprocess.run(
                [sys.executable, "scripts/ordivon-runtime-reclaim", "inspect", "--database", str(database), "--runtime-store-root", str(runtime)],
                cwd=REPO, check=True, text=True, capture_output=True,
            )
            candidates = json.loads(inspect.stdout)["candidates"]
            self.assertFalse(any(row["workspaceId"] == workspace_id for row in candidates))

    def test_true_orphan_quarantine_is_never_bulk_or_implicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            (runtime / "workspace-records").mkdir(parents=True)
            workspaces = runtime / "workspaces"
            workspaces.mkdir()
            workspace_id = "true-orphan-explicit-only"
            workspace = workspaces / workspace_id
            workspace.mkdir()
            (workspace / "important.txt").write_text("keep\n", encoding="utf-8")
            database = root / "registry.sqlite3"
            initialize_registry(database)
            base = [
                sys.executable, "scripts/ordivon-runtime-lifecycle", "repair",
                "--database", str(database), "--runtime-store-root", str(runtime),
                "--receipt-root", str(root / "receipts"), "--lock-file", str(root / "lifecycle.lock"),
                "--confirm-policy", "REPAIR_WORKSPACE_IDENTITIES",
            ]
            bulk = subprocess.run(base + ["--quarantine-unrepairable", "--quarantine-root", str(root / "q"), "--confirm-quarantine", "QUARANTINE_BROKEN_WORKSPACES"], cwd=REPO, check=True, text=True, capture_output=True)
            self.assertEqual(json.loads(bulk.stdout)["actions"], [])
            self.assertTrue(workspace.exists())
            implicit = subprocess.run(base + ["--workspace-id", workspace_id], cwd=REPO, check=False, text=True, capture_output=True)
            self.assertEqual(implicit.returncode, 2)
            self.assertIn("explicit --quarantine-unrepairable", implicit.stdout)
            self.assertTrue(workspace.exists())
            self.assertFalse((runtime / "workspace-records" / f"{workspace_id}.json").exists())

    def test_true_orphan_quarantine_refuses_active_job(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            (runtime / "workspace-records").mkdir(parents=True)
            workspaces = runtime / "workspaces"
            workspaces.mkdir()
            workspace_id = "true-orphan-active"
            workspace = workspaces / workspace_id
            workspace.mkdir()
            database = root / "registry.sqlite3"
            initialize_registry(database, workspace_id, 1)
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("UPDATE jobs SET resolution=NULL WHERE workspace_id=?", (workspace_id,))
                connection.execute("UPDATE attempts SET state='running',finished_at_ms=NULL WHERE job_id='job-1'")
                connection.execute("INSERT INTO concurrency_reservations VALUES ('attempt-1','active')")
                connection.commit()
            result = subprocess.run(
                [
                    sys.executable, "scripts/ordivon-runtime-lifecycle", "repair",
                    "--database", str(database), "--runtime-store-root", str(runtime),
                    "--receipt-root", str(root / "receipts"), "--lock-file", str(root / "lifecycle.lock"),
                    "--workspace-id", workspace_id, "--confirm-policy", "REPAIR_WORKSPACE_IDENTITIES",
                    "--quarantine-unrepairable", "--quarantine-root", str(root / "q"),
                    "--confirm-quarantine", "QUARANTINE_BROKEN_WORKSPACES",
                ],
                cwd=REPO, check=False, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("active or held Job", result.stdout)
            self.assertTrue(workspace.exists())
            self.assertFalse((runtime / "workspace-records" / f"{workspace_id}.json").exists())

    def test_quarantine_tmp_presentation_wrong_target_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            workspace_id = "wrong-target-quarantine"
            expected = runtime / "cache" / "tmp" / workspace_id
            wrong = runtime / "cache" / "tmp" / "another-workspace"
            expected.mkdir(parents=True)
            wrong.mkdir(parents=True)
            presentation = self.module["trusted_tmp_presentation_path"](runtime, workspace_id)
            presentation.parent.mkdir(mode=0o700, exist_ok=True)
            try:
                presentation.unlink()
            except FileNotFoundError:
                pass
            presentation.symlink_to(wrong, target_is_directory=True)
            try:
                with self.assertRaisesRegex(RuntimeError, "points at"):
                    self.module["remove_trusted_tmp_presentation"](runtime, workspace_id)
                self.assertTrue(presentation.is_symlink())
                self.assertEqual(Path(os.readlink(presentation)), wrong)
            finally:
                try:
                    presentation.unlink()
                except FileNotFoundError:
                    pass

    def test_dirty_review_records_exact_evidence_without_mutating_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            records = runtime / "workspace-records"
            workspaces = runtime / "workspaces"
            records.mkdir(parents=True)
            workspaces.mkdir()
            workspace_id = "dirty-review"
            workspace = workspaces / workspace_id
            revision = init_repository(workspace)
            (workspace / "README.md").write_text("changed\n", encoding="utf-8")
            (workspace / "new.txt").write_text("untracked\n", encoding="utf-8")
            record = records / f"{workspace_id}.json"
            record.write_text(
                json.dumps({
                    "schemaVersion": 1,
                    "workspaceId": workspace_id,
                    "sourceRepo": str(workspace),
                    "sourceRevision": revision,
                    "workspacePath": str(workspace),
                    "createdUnixMs": 1,
                }),
                encoding="utf-8",
            )
            database = root / "registry.sqlite3"
            initialize_registry(database)
            fake_reclaim = root / "fake-reclaim"
            fake_reclaim.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                f"print(json.dumps({{'schemaVersion': 1, 'summary': {{'counts': {{'blocked_dirty': 1}}}}, 'candidates': [{{'workspaceId': '{workspace_id}', 'classification': 'blocked_dirty', 'createdUnixMs': 1, 'lastActivityUnixMs': 1}}]}}))\n",
                encoding="utf-8",
            )
            fake_reclaim.chmod(0o755)
            environment = os.environ.copy()
            environment["ORDIVON_RUNTIME_RECLAIM"] = str(fake_reclaim)
            before = subprocess.run(
                ["git", "-C", str(workspace), "status", "--porcelain=v1", "--untracked-files=all"],
                check=True, text=True, capture_output=True,
            ).stdout
            result = subprocess.run(
                [
                    sys.executable, "scripts/ordivon-runtime-lifecycle", "dirty-review",
                    "--database", str(database),
                    "--runtime-store-root", str(runtime),
                    "--receipt-root", str(root / "receipts"),
                    "--lock-file", str(root / "lifecycle.lock"),
                    "--workspace-id", workspace_id,
                ],
                cwd=REPO, env=environment, check=False, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "completed")
            action = report["actions"][0]
            self.assertEqual(action["workspaceId"], workspace_id)
            self.assertEqual(action["currentHeadRevision"], revision)
            self.assertEqual(action["recommendedOwnerAction"], "quarantine_review")
            self.assertFalse(action["automaticDeletionAllowed"])
            self.assertGreater(action["trackedDiffBytes"], 0)
            self.assertEqual([item["path"] for item in action["untracked"]], ["new.txt"])
            after = subprocess.run(
                ["git", "-C", str(workspace), "status", "--porcelain=v1", "--untracked-files=all"],
                check=True, text=True, capture_output=True,
            ).stdout
            self.assertEqual(after, before)
            receipt = Path(report["receipt"]) / "result.json"
            self.assertTrue(receipt.is_file())
            self.assertEqual(json.loads(receipt.read_text())["actions"][0]["statusDigest"], action["statusDigest"])


    def test_sweep_reuses_bounded_selection_for_before_and_after(self) -> None:
        sweep = self.module["sweep"]
        globals_ = sweep.__globals__
        original_enrich = globals_["enrich_report"]
        original_reclaim = globals_["reclaim_apply_selected"]
        with tempfile.TemporaryDirectory(dir=REPO) as temporary:
            root = Path(temporary)
            registry = root / "registry"
            registry.mkdir()
            database = registry / "registry.sqlite3"
            database.touch()
            runtime = root / "runtime"
            runtime.mkdir()
            env_file = root / "runtime.env"
            env_file.write_text(
                f"ORDIVON_REGISTRY_ROOT={registry}\n"
                f"ORDIVON_STORE_ROOT={runtime}\n"
                "ORDIVON_BIND=127.0.0.1:1\n"
                "ORDIVON_BEARER_TOKEN=test\n",
                encoding="utf-8",
            )
            observed_selections: list[list[str]] = []

            def fake_enrich(args):
                selected = self.module["selected_workspace_ids"](args)
                observed_selections.append(list(selected))
                return {
                    "schemaVersion": 1,
                    "summary": {"policyEligible": len(selected)},
                    "candidates": [
                        {
                            "workspaceId": workspace_id,
                            "classification": "stale_record",
                            "policyEligible": True,
                        }
                        for workspace_id in selected
                    ],
                }

            def fake_reclaim(_args, workspace_ids, _receipt):
                return {
                    "schemaVersion": 1,
                    "status": "completed",
                    "actions": [
                        {
                            "workspaceId": workspace_id,
                            "action": "workspace_closed",
                        }
                        for workspace_id in workspace_ids
                    ],
                    "failures": [],
                    "receipt": "/fake/reclaim",
                }

            globals_["enrich_report"] = fake_enrich
            globals_["reclaim_apply_selected"] = fake_reclaim
            args = argparse.Namespace(
                confirm_policy="APPLY_WORKSPACE_RETENTION_POLICY",
                database=database,
                runtime_store_root=runtime,
                workspace_root=None,
                policy_file=None,
                busy_timeout_ms=5_000,
                measure_bytes=False,
                workspace_ids=["ws-target"],
                workspace_refs=[
                    "runtime:workspace:ws-target",
                ],
                env_file=env_file,
                receipt_root=root / "receipts",
                lock_file=root / "lifecycle.lock",
                pretty=False,
            )
            try:
                report = sweep(args)
            finally:
                globals_["enrich_report"] = original_enrich
                globals_["reclaim_apply_selected"] = original_reclaim

            self.assertEqual(
                observed_selections,
                [["ws-target"], ["ws-target"]],
            )
            self.assertEqual(report["selectionMode"], "bounded")
            self.assertEqual(report["requestedWorkspaceIds"], ["ws-target"])
            self.assertEqual(report["selectedWorkspaceIds"], ["ws-target"])
            before = json.loads(
                (Path(report["receipt"]) / "before.json").read_text(encoding="utf-8")
            )
            self.assertEqual(before["selectionMode"], "bounded")
            self.assertEqual(before["requestedWorkspaceIds"], ["ws-target"])
            self.assertEqual(
                [item["workspaceId"] for item in report["actions"]],
                ["ws-target"],
            )

    def test_sweep_receipt_preserves_requested_scope_outside_action_plan(self) -> None:
        sweep = self.module["sweep"]
        globals_ = sweep.__globals__
        original_enrich = globals_["enrich_report"]
        original_reclaim = globals_["reclaim_apply_selected"]

        cases = [
            (
                "requested_ineligible",
                ["ws-a", "ws-b"],
                [
                    {
                        "workspaceId": "ws-a",
                        "classification": "stale_record",
                        "policyEligible": True,
                    },
                    {
                        "workspaceId": "ws-b",
                        "classification": "blocked_dirty",
                        "policyEligible": False,
                    },
                ],
                "bounded",
                ["ws-a", "ws-b"],
                ["ws-a"],
            ),
            (
                "requested_missing",
                ["ws-a", "ws-missing"],
                [
                    {
                        "workspaceId": "ws-a",
                        "classification": "stale_record",
                        "policyEligible": True,
                    },
                ],
                "bounded",
                ["ws-a", "ws-missing"],
                ["ws-a"],
            ),
            (
                "global_no_selector",
                [],
                [
                    {
                        "workspaceId": "ws-global",
                        "classification": "stale_record",
                        "policyEligible": True,
                    },
                ],
                "global",
                [],
                ["ws-global"],
            ),
        ]

        for (
            name,
            requested_ids,
            candidates,
            expected_mode,
            expected_requested,
            expected_selected,
        ) in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=REPO) as temporary:
                root = Path(temporary)
                registry = root / "registry"
                registry.mkdir()
                database = registry / "registry.sqlite3"
                database.touch()
                runtime = root / "runtime"
                runtime.mkdir()
                env_file = root / "runtime.env"
                env_file.write_text(
                    f"ORDIVON_REGISTRY_ROOT={registry}\n"
                    f"ORDIVON_STORE_ROOT={runtime}\n"
                    "ORDIVON_BIND=127.0.0.1:1\n"
                    "ORDIVON_BEARER_TOKEN=test\n",
                    encoding="utf-8",
                )

                observed_selections: list[list[str]] = []

                def fake_enrich(args):
                    observed_selections.append(
                        list(self.module["selected_workspace_ids"](args))
                    )
                    return {
                        "schemaVersion": 1,
                        "summary": {
                            "policyEligible": sum(
                                item.get("policyEligible") is True
                                for item in candidates
                            )
                        },
                        "candidates": [dict(item) for item in candidates],
                    }

                def fake_reclaim(_args, workspace_ids, receipt):
                    before_path = receipt / "before.json"
                    self.assertTrue(before_path.is_file())
                    persisted_before = json.loads(before_path.read_text(encoding="utf-8"))
                    self.assertEqual(persisted_before["selectionMode"], expected_mode)
                    self.assertEqual(
                        persisted_before["requestedWorkspaceIds"],
                        expected_requested,
                    )
                    return {
                        "schemaVersion": 1,
                        "status": "completed",
                        "actions": [
                            {
                                "workspaceId": workspace_id,
                                "action": "workspace_closed",
                            }
                            for workspace_id in workspace_ids
                        ],
                        "failures": [],
                        "receipt": "/fake/reclaim",
                    }

                globals_["enrich_report"] = fake_enrich
                globals_["reclaim_apply_selected"] = fake_reclaim
                args = argparse.Namespace(
                    confirm_policy="APPLY_WORKSPACE_RETENTION_POLICY",
                    database=database,
                    runtime_store_root=runtime,
                    workspace_root=None,
                    policy_file=None,
                    busy_timeout_ms=5_000,
                    measure_bytes=False,
                    workspace_ids=list(requested_ids),
                    workspace_refs=[],
                    env_file=env_file,
                    receipt_root=root / "receipts",
                    lock_file=root / "lifecycle.lock",
                    pretty=False,
                )
                try:
                    report = sweep(args)
                finally:
                    globals_["enrich_report"] = original_enrich
                    globals_["reclaim_apply_selected"] = original_reclaim

                self.assertEqual(
                    observed_selections,
                    [list(requested_ids), list(requested_ids)],
                )
                self.assertEqual(report["selectionMode"], expected_mode)
                self.assertEqual(
                    report["requestedWorkspaceIds"],
                    expected_requested,
                )
                self.assertEqual(
                    report["selectedWorkspaceIds"],
                    expected_selected,
                )
                before = json.loads(
                    (Path(report["receipt"]) / "before.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(before["selectionMode"], expected_mode)
                self.assertEqual(
                    before["requestedWorkspaceIds"],
                    expected_requested,
                )
                self.assertEqual(
                    [item["workspaceId"] for item in before["candidates"]],
                    [item["workspaceId"] for item in candidates],
                )
                after = json.loads(
                    (Path(report["receipt"]) / "after.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(after["selectionMode"], expected_mode)
                self.assertEqual(
                    after["requestedWorkspaceIds"],
                    expected_requested,
                )

    def test_sweep_rejects_incompatible_reclaim_contract_before_apply(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO) as temporary:
            root = Path(temporary)
            marker = root / "apply-called"
            fake_reclaim = root / "fake-reclaim"
            fake_reclaim.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                "if sys.argv[1] == 'inspect':\n"
                " print(json.dumps({'schemaVersion': 2, 'summary': {}, 'candidates': []}))\n"
                "elif sys.argv[1] == 'apply':\n"
                f" pathlib.Path({str(marker)!r}).write_text('called')\n"
                " print(json.dumps({'schemaVersion': 2, 'status': 'completed', 'actions': [], 'failures': [], 'receipt': '/fake'}))\n"
                "else: raise SystemExit(1)\n",
                encoding="utf-8",
            )
            fake_reclaim.chmod(0o755)
            database = root / "registry.sqlite3"
            database.touch()
            runtime = root / "runtime"
            runtime.mkdir()
            env_file = root / "runtime.env"
            env_file.write_text(
                f"ORDIVON_REGISTRY_ROOT={root}\n"
                f"ORDIVON_STORE_ROOT={runtime}\n"
                "ORDIVON_BIND=127.0.0.1:1\n"
                "ORDIVON_BEARER_TOKEN=test\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["ORDIVON_RUNTIME_RECLAIM"] = str(fake_reclaim)
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-lifecycle",
                    "sweep",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                    "--env-file",
                    str(env_file),
                    "--receipt-root",
                    str(root / "receipts"),
                    "--lock-file",
                    str(root / "lifecycle.lock"),
                    "--confirm-policy",
                    "APPLY_WORKSPACE_RETENTION_POLICY",
                ],
                cwd=REPO,
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported schemaVersion", result.stderr)
            self.assertFalse(marker.exists(), "incompatible inspect contract reached apply")

    def test_reclaim_result_validators_reject_malformed_structures(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "candidates must be an array"):
            self.module["validate_reclaim_inspect"](
                {"schemaVersion": 1, "summary": {}, "candidates": {}}
            )
        with self.assertRaisesRegex(RuntimeError, "duplicate workspaceId"):
            self.module["validate_reclaim_inspect"](
                {
                    "schemaVersion": 1,
                    "summary": {},
                    "candidates": [
                        {"workspaceId": "same", "classification": "closable"},
                        {"workspaceId": "same", "classification": "closable"},
                    ],
                }
            )
        with self.assertRaisesRegex(RuntimeError, "actions must be an array of objects"):
            self.module["validate_reclaim_apply"](
                {
                    "schemaVersion": 1,
                    "status": "completed",
                    "actions": ["not-an-object"],
                    "failures": [],
                    "receipt": "/fake",
                }
            )


    def test_default_policy_is_disposable_with_idle_and_hard_ttl(self) -> None:
        ephemeral = self.module["DEFAULT_POLICY"]["classes"]["ephemeral"]
        self.assertEqual(ephemeral["retentionHours"], 72.0)
        self.assertEqual(ephemeral["maxLifetimeHours"], 168.0)
        self.assertTrue(ephemeral["forceCloseDirtyAfterRetention"])
        self.assertTrue(ephemeral["forceCloseUnintegratedAfterRetention"])
        self.assertTrue(ephemeral["forceCloseAfterMaxLifetime"])

    def test_packaged_default_policy_is_disposable_with_idle_and_hard_ttl(self) -> None:
        policy = json.loads(
            (REPO / "packaging/systemd/ordivon-workspace-retention.json").read_text(
                encoding="utf-8"
            )
        )
        ephemeral = policy["classes"]["ephemeral"]
        self.assertEqual(ephemeral["retentionHours"], 72)
        self.assertEqual(ephemeral["maxLifetimeHours"], 168)
        self.assertTrue(ephemeral["forceCloseDirtyAfterRetention"])
        self.assertTrue(ephemeral["forceCloseUnintegratedAfterRetention"])
        self.assertTrue(ephemeral["forceCloseAfterMaxLifetime"])


if __name__ == "__main__":
    unittest.main()
