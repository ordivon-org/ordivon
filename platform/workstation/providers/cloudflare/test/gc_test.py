from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
import unittest
import urllib.parse
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


if __name__ == "__main__":
    unittest.main()
