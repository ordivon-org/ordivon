from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
import urllib.parse
from contextlib import redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts" / "ordivon_edge_gc.py"
SPEC = importlib.util.spec_from_file_location("ordivon_edge_gc", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load GC controller")
gc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gc
SPEC.loader.exec_module(gc)


class GarbageCollectionTests(unittest.TestCase):
    def test_default_provider_repository_is_canonical_monorepo_owner(self) -> None:
        self.assertEqual(
            gc.DEFAULT_PROVIDER_REPOSITORY,
            pathlib.Path("/root/projects/ordivon/platform/workstation/providers/cloudflare"),
        )

    def test_gc_unit_uses_canonical_monorepo_working_directory(self) -> None:
        unit = (ROOT / "deploy/systemd/ordivon-edge-gc.service").read_text()
        self.assertIn(
            "WorkingDirectory=/root/projects/ordivon/platform/workstation/providers/cloudflare",
            unit,
        )
        self.assertNotIn(
            "WorkingDirectory=/root/projects/ordivon-workstation-v2/providers/cloudflare",
            unit,
        )

    def test_installed_controller_resolves_world_monorepo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            provider = repository / "providers" / "cloudflare"
            provider.mkdir(parents=True)
            (provider / "wrangler.jsonc").write_text("{}\n")
            resolved = gc.resolve_provider_root(
                pathlib.Path("/usr/local/sbin/ordivon-edge-gc"),
                repository,
            )
            self.assertEqual(resolved, provider.resolve())

    def test_r2_list_contract_uses_per_page_and_cursor(self) -> None:
        responses = [
            {
                "success": True,
                "result": {
                    "objects": [{"key": "cleanup/v2/request_001/g1.json"}],
                    "truncated": True,
                    "cursor": "next-page",
                },
            },
            {
                "success": True,
                "result": {
                    "objects": [{"key": "cleanup/v2/request_002/g1.json"}],
                    "truncated": False,
                },
            },
        ]
        urls: list[str] = []

        def fake_api_json(token: str, url: str):
            self.assertEqual(token, "token")
            urls.append(url)
            return responses.pop(0)

        with mock.patch.object(gc, "api_json", side_effect=fake_api_json):
            keys = gc.list_cleanup_keys("token", "account", 100)

        self.assertEqual(
            keys,
            [
                "cleanup/v2/request_001/g1.json",
                "cleanup/v2/request_002/g1.json",
            ],
        )
        first = urllib.parse.parse_qs(urllib.parse.urlsplit(urls[0]).query)
        second = urllib.parse.parse_qs(urllib.parse.urlsplit(urls[1]).query)
        self.assertEqual(first["per_page"], ["100"])
        self.assertNotIn("limit", first)
        self.assertEqual(first["prefix"], ["cleanup/v2/"])
        self.assertEqual(second["cursor"], ["next-page"])
        self.assertEqual(second["per_page"], ["99"])

    def test_cleanup_scope_is_generation_and_operation_bounded(self) -> None:
        task = {
            "schema_version": 1,
            "request_id": "request_001",
            "lease_generation": 2,
            "operation": "fetch",
            "reason": "execution_lease_lost",
            "artifact_keys": [
                "fetch/v2/request_001/g2/body",
                "fetch/v2/request_001/g2/body",
            ],
        }
        self.assertEqual(
            gc.validate_task("cleanup/v2/request_001/g2.json", task),
            ["fetch/v2/request_001/g2/body"],
        )
        task["artifact_keys"] = ["fetch/v2/request_001/g1/body"]
        with self.assertRaises(gc.GarbageCollectionError):
            gc.validate_task("cleanup/v2/request_001/g2.json", task)


    def test_cleanup_requires_exact_identity_operation_and_generation(self) -> None:
        task = {
            "schema_version": 1, "request_id": "request_001",
            "operation": "fetch", "lease_generation": 2,
            "reason": "execution_lease_lost",
            "artifact_keys": ["fetch/v2/request_001/g2/body"],
        }
        for key, changes in [
            ("cleanup/v2/other_001/g2.json", {}),
            ("cleanup/v2/request_001/g3.json", {}),
            ("cleanup/v2/request_001/g2.json", {"lease_generation": True}),
            ("cleanup/v2/request_001/g2.json", {"schema_version": True}),
            ("cleanup/v2/request_001/g2.json", {"operation": "browser.run"}),
            ("cleanup/v2/request_001/g2.json", {"artifact_keys": ["fetch/v2/request_001/g3/other/g2/body"]}),
            ("cleanup/v2/request_001/g2.json", {"artifact_keys": ["browser/v2/request_001/g2/screenshot.png"]}),
        ]:
            with self.subTest(key=key, changes=changes):
                with self.assertRaises(gc.GarbageCollectionError):
                    gc.validate_task(key, task | changes)

    def test_audit_accepts_single_new_bundle_but_rejects_mixed_epochs(self) -> None:
        task = {
            "schema_version": 1, "request_id": "request_001",
            "operation": "browser.run", "lease_generation": 2,
            "reason": "browser_partial_write",
        }
        key = "cleanup/v2/request_001/g2.json"
        prefix = "browser/v2/request_001/g2/"
        one = prefix + "12345678-1234-4abc-8def-123456789abc/"
        two = prefix + "87654321-1234-4abc-8def-123456789abc/"
        keys = [one + "screenshot.png", one + "content.html"]
        self.assertEqual(gc.validate_task(key, task | {"artifact_keys": keys}), keys)
        for mixed in ([keys[0], two + "content.html"], [keys[0], prefix + "content.html"]):
            with self.assertRaises(gc.GarbageCollectionError):
                gc.validate_task(key, task | {"artifact_keys": mixed})

    def test_all_legacy_tombstones_are_reported_without_remote_deletion(self) -> None:
        key = "cleanup/v2/request_001/g2.json"
        for reason in (
            "receipt_commit_unavailable", "receipt_lease_mismatch",
            "execution_lease_lost", "browser_partial_write", "future_reason",
        ):
            for dry_run in (False, True):
                task = {
                    "schema_version": 1, "request_id": "request_001",
                    "operation": "fetch", "lease_generation": 2,
                    "reason": reason, "artifact_keys": ["fetch/v2/request_001/g2/body"],
                }
                argv = ["ordivon-edge-gc"] + (["--dry-run"] if dry_run else [])
                with (
                    self.subTest(reason=reason, dry_run=dry_run),
                    mock.patch.object(sys, "argv", argv),
                    mock.patch.object(gc, "load_cloudflare", return_value=("token", "account", {})),
                    mock.patch.object(gc, "list_cleanup_keys", return_value=[key]),
                    mock.patch.object(gc, "get_task", return_value=task) as read,
                    mock.patch.object(gc, "wrangler") as remote,
                    mock.patch.object(gc, "write_receipt", return_value=pathlib.Path("/tmp/gc.json")),
                    redirect_stdout(io.StringIO()) as output,
                ):
                    self.assertEqual(gc.main(), 0)
                    read.assert_called_once_with({}, key)
                    remote.assert_not_called()
                    result = json.loads(output.getvalue())
                    self.assertEqual(result["completed"], [])
                    self.assertEqual(result["deferred"][0]["task_key"], key)
                    self.assertEqual(result["deferred"][0]["disposition"], "native_retention")
                    self.assertEqual(result["deferred"][0]["reason"], reason)
                    self.assertEqual(result["status"], "completed_with_deferred")

    def test_invalid_task_is_reported_and_other_tasks_remain_auditable(self) -> None:
        bad_key = "cleanup/v2/other_001/g2.json"
        key = "cleanup/v2/request_001/g2.json"
        task = {
            "schema_version": 1, "request_id": "request_001",
            "operation": "fetch", "lease_generation": 2,
            "reason": "execution_lease_lost", "artifact_keys": ["fetch/v2/request_001/g2/body"],
        }
        with (
            mock.patch.object(sys, "argv", ["ordivon-edge-gc"]),
            mock.patch.object(gc, "load_cloudflare", return_value=("token", "account", {})),
            mock.patch.object(gc, "list_cleanup_keys", return_value=[bad_key, key]),
            mock.patch.object(gc, "get_task", return_value=task),
            mock.patch.object(gc, "wrangler") as remote,
            mock.patch.object(gc, "write_receipt", return_value=pathlib.Path("/tmp/gc.json")),
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(gc.main(), 1)
            remote.assert_not_called()
            result = json.loads(output.getvalue())
            self.assertEqual(result["failed"][0]["task_key"], bad_key)
            self.assertEqual(result["deferred"][0]["task_key"], key)


if __name__ == "__main__":
    unittest.main()
