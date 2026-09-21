from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts" / "ordivon_cloudflare_tofu_handoff.py"
SPEC = importlib.util.spec_from_file_location("ordivon_cloudflare_tofu_handoff", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load handoff OpenTofu controller")
controller = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = controller
SPEC.loader.exec_module(controller)


class HandoffTofuControllerTests(unittest.TestCase):
    def test_plan_summary_rejects_delete_and_replace(self) -> None:
        plan = {
            "resource_changes": [
                {"address": "safe.create", "change": {"actions": ["create"]}},
                {"address": "safe.update", "change": {"actions": ["update"]}},
                {"address": "bad.delete", "change": {"actions": ["delete"]}},
                {"address": "bad.replace", "change": {"actions": ["delete", "create"]}},
            ],
            "output_changes": {"gateway_mcp_audience": {}},
        }
        summary = controller._summarize_plan(plan)
        self.assertFalse(summary["safe_no_delete_replace"])
        self.assertEqual(summary["counts"]["delete"], 1)
        self.assertEqual(summary["counts"]["replace"], 1)
        self.assertEqual(
            [item["address"] for item in summary["dangerous"]],
            ["bad.delete", "bad.replace"],
        )

    def test_plan_summary_accepts_create_update_read_and_noop(self) -> None:
        plan = {
            "resource_changes": [
                {"address": "a", "change": {"actions": ["create"]}},
                {"address": "b", "change": {"actions": ["update"]}},
                {"address": "c", "change": {"actions": ["read"]}},
                {"address": "d", "change": {"actions": ["no-op"]}},
            ]
        }
        summary = controller._summarize_plan(plan)
        self.assertTrue(summary["safe_no_delete_replace"])
        self.assertEqual(summary["dangerous"], [])

    def test_private_credential_owner_rejects_group_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cloudflare.json"
            path.write_text(json.dumps({"api_token": "x", "account_id": "a"}))
            os.chmod(path, 0o640)
            with self.assertRaises(controller.HandoffTofuError):
                controller._private_json(path)

    def test_load_receipt_requires_exact_plan_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            plan_dir = root / "plans"
            receipt_dir = root / "receipts"
            plan_dir.mkdir()
            receipt_dir.mkdir()
            plan = plan_dir / ("a" * 64 + ".tfplan")
            plan.write_bytes(b"not-the-matching-plan")
            receipt = receipt_dir / ("plan-" + "a" * 64 + ".json")
            receipt.write_text(json.dumps({"plan_sha256": "a" * 64}))
            with (
                mock.patch.object(controller, "PLAN_DIR", plan_dir),
                mock.patch.object(controller, "RECEIPT_DIR", receipt_dir),
                self.assertRaises(controller.HandoffTofuError, msg="digest mismatch"),
            ):
                controller.load_plan_receipt("a" * 64)

    def test_apply_refuses_unapproved_plan_before_cloudflare_environment(self) -> None:
        receipt = {
            "plan_sha256": "b" * 64,
            "eligible_for_apply": False,
        }
        with (
            mock.patch.object(controller, "load_plan_receipt", return_value=receipt),
            mock.patch.object(controller, "cloudflare_environment") as environment,
            self.assertRaises(controller.HandoffTofuError, msg="not eligible"),
        ):
            controller.apply_reviewed_plan("b" * 64)
        environment.assert_not_called()

    def test_fixed_authority_paths_are_not_cli_parameters(self) -> None:
        self.assertEqual(
            controller.TOFU_ROOT,
            pathlib.Path("/root/projects/ordivon/platform/workstation/tofu/agent-birth-handoff"),
        )
        self.assertEqual(
            controller.CLOUDFLARE_CONFIG,
            pathlib.Path("/root/.config/ordivon/secrets/cloudflare.json"),
        )


if __name__ == "__main__":
    unittest.main()
