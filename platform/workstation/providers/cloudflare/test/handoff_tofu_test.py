from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import stat
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

    def test_source_identity_is_bound_to_operation_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "handoff-tofu"
            commit = "a" * 40
            release = root / "releases" / commit
            release.mkdir(parents=True)
            for name, content in {
                "main.tf": "terraform {}\n",
                "versions.tf": "terraform {}\n",
                ".terraform.lock.hcl": "lock\n",
                "tofurc": "provider_installation {}\n",
            }.items():
                path = release / name
                path.write_text(content)
                os.chmod(path, 0o644)
            (root / "current").symlink_to(pathlib.Path("releases") / commit)
            with (
                mock.patch.object(controller, "TOFU_RELEASE_ROOT", root),
                mock.patch.object(controller, "TOFU_ROOT", root / "current"),
            ):
                observed_commit, digest = controller._source_identity()
            self.assertEqual(observed_commit, commit)
            self.assertRegex(digest, r"^sha256:[0-9a-f]{64}$")

    def test_fixed_authority_paths_are_not_cli_parameters(self) -> None:
        self.assertEqual(
            controller.TOFU_ROOT,
            pathlib.Path(
                "/usr/local/lib/ordivon-operations/cloudflare-provider/handoff-tofu/current"
            ),
        )
        self.assertEqual(
            controller.CLOUDFLARE_CONFIG,
            pathlib.Path("/root/.config/ordivon/secrets/cloudflare.json"),
        )


if __name__ == "__main__":
    unittest.main()


class CredentialAliasTests(unittest.TestCase):
    def test_private_same_directory_alias_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "secrets"
            root.mkdir(mode=0o700)
            target = root / "cloudflare-account-api-token.json"
            target.write_text(json.dumps({"api_token": "x", "account_id": "a"}))
            os.chmod(target, 0o600)
            alias = root / "cloudflare.json"
            alias.symlink_to(target.name)
            self.assertEqual(controller._private_json(alias)["account_id"], "a")

    def test_cross_directory_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "secrets"
            other = pathlib.Path(directory) / "other"
            root.mkdir(mode=0o700)
            other.mkdir(mode=0o700)
            target = other / "cloudflare-account-api-token.json"
            target.write_text(json.dumps({"api_token": "x", "account_id": "a"}))
            os.chmod(target, 0o600)
            alias = root / "cloudflare.json"
            alias.symlink_to(pathlib.Path("..") / "other" / target.name)
            with self.assertRaises(controller.HandoffTofuError):
                controller._private_json(alias)


class PlanSemanticGateTests(unittest.TestCase):
    @staticmethod
    def _plan() -> dict[str, object]:
        prior_ingress = [
            {"hostname": "skills-mcp.ordivon.com", "service": "http://127.0.0.1:8896"},
            {"hostname": None, "service": "http_status:404"},
        ]
        planned_ingress = [
            *prior_ingress[:-1],
            {"hostname": "gateway-mcp.ordivon.com", "service": "http://127.0.0.1:8899"},
            prior_ingress[-1],
        ]
        native_prior_ingress = [
            {"hostname": "canary-mcp.ordivon.com", "service": "http://127.0.0.1:18997"},
            {"hostname": None, "service": "http_status:404"},
        ]
        native_planned_ingress = [
            native_prior_ingress[0],
            {"hostname": "gateway-mcp.ordivon.com", "service": "http://127.0.0.1:19000"},
            native_prior_ingress[-1],
        ]
        return {
            "prior_state": {
                "values": {
                    "root_module": {
                        "resources": [
                            {
                                "address": "cloudflare_zero_trust_tunnel_cloudflared_config.production",
                                "values": {"config": {"ingress": prior_ingress}},
                            }
                        ]
                    }
                }
            },
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "cloudflare_zero_trust_tunnel_cloudflared_config.production",
                            "values": {"config": {"ingress": planned_ingress}},
                        },
                        {
                            "address": "cloudflare_zero_trust_access_application.gateway_mcp",
                            "values": {
                                "type": "self_hosted",
                                "domain": "gateway-mcp.ordivon.com",
                                "allowed_idps": ["idp-1"],
                                "policies": [{"decision": "allow"}],
                                "oauth_configuration": {
                                    "enabled": True,
                                    "dynamic_client_registration": {
                                        "enabled": True,
                                        "allowed_uris": [
                                            "https://chatgpt.com/connector/oauth/*"
                                        ],
                                        "allow_any_on_localhost": True,
                                        "allow_any_on_loopback": True,
                                    },
                                    "grant": {
                                        "access_token_lifetime": "15m",
                                        "session_duration": "336h",
                                    },
                                },
                            },
                        },
                        {
                            "address": "cloudflare_dns_record.gateway_mcp",
                            "values": {
                                "name": "gateway-mcp.ordivon.com",
                                "content": "native-tunnel.cfargotunnel.com",
                                "type": "CNAME",
                                "proxied": True,
                            },
                        },
                        {
                            "address": "cloudflare_zero_trust_access_service_token.gateway_windows_runtime",
                            "values": {
                                "name": "Ordivon Gateway Windows Runtime",
                                "duration": "8760h",
                                "enabled": True,
                            },
                        },
                        {
                            "address": "data.cloudflare_zero_trust_tunnel_cloudflared_config.native",
                            "values": {"config": {"ingress": native_prior_ingress}},
                        },
                        {
                            "address": "cloudflare_zero_trust_tunnel_cloudflared_config.native",
                            "values": {
                                "tunnel_id": "native-tunnel",
                                "config": {"ingress": native_planned_ingress},
                            },
                        },
                    ]
                }
            },
            "resource_changes": [
                {
                    "address": "cloudflare_zero_trust_access_application.gateway_mcp",
                    "change": {"actions": ["create"]},
                },
                {
                    "address": "cloudflare_dns_record.gateway_mcp",
                    "change": {"actions": ["create"]},
                },
                {
                    "address": "cloudflare_zero_trust_tunnel_cloudflared_config.production",
                    "change": {"actions": ["update"]},
                },
                {
                    "address": "cloudflare_zero_trust_access_service_token.gateway_windows_runtime",
                    "change": {"actions": ["create"]},
                },
                {
                    "address": "cloudflare_zero_trust_tunnel_cloudflared_config.native",
                    "change": {"actions": ["update"]},
                },
            ],
        }

    def test_semantic_gate_accepts_exact_make_before_break_plan(self) -> None:
        semantics = controller._handoff_semantics(self._plan())
        self.assertTrue(semantics["semantic_gate"])
        self.assertEqual(semantics["details"]["unexpected_mutations"], [])

    def test_semantic_gate_rejects_disabled_local_oauth_callbacks(self) -> None:
        for field in ("allow_any_on_localhost", "allow_any_on_loopback"):
            with self.subTest(field=field):
                plan = self._plan()
                gateway = plan["planned_values"]["root_module"]["resources"][1]
                gateway["values"]["oauth_configuration"]["dynamic_client_registration"][
                    field
                ] = False
                semantics = controller._handoff_semantics(plan)
                self.assertFalse(semantics["semantic_gate"])
                check = (
                    "localhost_callbacks_enabled"
                    if field == "allow_any_on_localhost"
                    else "loopback_callbacks_enabled"
                )
                self.assertFalse(semantics["checks"][check])

    def test_semantic_gate_rejects_lost_chatgpt_callback_allowlist(self) -> None:
        plan = self._plan()
        gateway = plan["planned_values"]["root_module"]["resources"][1]
        gateway["values"]["oauth_configuration"]["dynamic_client_registration"][
            "allowed_uris"
        ] = []
        semantics = controller._handoff_semantics(plan)
        self.assertFalse(semantics["semantic_gate"])
        self.assertFalse(semantics["checks"]["chatgpt_callback_allowlist_retained"])

    def test_semantic_gate_rejects_lost_existing_ingress(self) -> None:
        plan = self._plan()
        tunnel = plan["planned_values"]["root_module"]["resources"][0]
        tunnel["values"]["config"]["ingress"] = [
            {"hostname": "gateway-mcp.ordivon.com", "service": "http://127.0.0.1:8899"},
            {"hostname": None, "service": "http_status:404"},
        ]
        semantics = controller._handoff_semantics(plan)
        self.assertFalse(semantics["semantic_gate"])
        self.assertFalse(semantics["checks"]["prior_named_ingress_preserved"])

    def test_semantic_gate_rejects_lost_native_runtime_canary(self) -> None:
        plan = self._plan()
        native = plan["planned_values"]["root_module"]["resources"][5]
        native["values"]["config"]["ingress"] = [
            {"hostname": "gateway-mcp.ordivon.com", "service": "http://127.0.0.1:19000"},
            {"hostname": None, "service": "http_status:404"},
        ]
        semantics = controller._handoff_semantics(plan)
        self.assertFalse(semantics["semantic_gate"])
        self.assertFalse(semantics["checks"]["native_runtime_canary_retained"])

    def test_semantic_gate_rejects_gateway_dns_not_on_native_tunnel(self) -> None:
        plan = self._plan()
        dns = plan["planned_values"]["root_module"]["resources"][2]
        dns["values"]["content"] = "production-tunnel.cfargotunnel.com"
        semantics = controller._handoff_semantics(plan)
        self.assertFalse(semantics["semantic_gate"])
        self.assertFalse(semantics["checks"]["gateway_dns_exact"])

    def test_semantic_gate_rejects_unexpected_mutation(self) -> None:
        plan = self._plan()
        plan["resource_changes"].append(
            {
                "address": "cloudflare_dns_record.unrelated",
                "change": {"actions": ["update"]},
            }
        )
        semantics = controller._handoff_semantics(plan)
        self.assertFalse(semantics["semantic_gate"])
        self.assertEqual(
            semantics["details"]["unexpected_mutations"],
            ["cloudflare_dns_record.unrelated"],
        )


class WindowsServiceAuthTests(unittest.TestCase):
    def test_census_accepts_clean_service_token_creation(self) -> None:
        plan = PlanSemanticGateTests._plan()
        with (
            mock.patch.object(
                controller,
                "_windows_runtime_access_application",
                return_value={
                    "id": "app-1",
                    "domain": controller.WINDOWS_RUNTIME_DOMAIN,
                    "type": "self_hosted",
                    "aud": "aud-1",
                },
            ),
            mock.patch.object(controller, "_service_tokens", return_value=[]),
            mock.patch.object(controller, "_windows_runtime_policies", return_value=[]),
        ):
            census = controller._windows_service_auth_census(plan)
        self.assertTrue(census["eligible"])
        self.assertEqual(census["service_token_actions"], ["create"])
        self.assertEqual(census["service_auth_policy_state"], "absent")

    def test_census_rejects_existing_unowned_token_name(self) -> None:
        plan = PlanSemanticGateTests._plan()
        with (
            mock.patch.object(
                controller,
                "_windows_runtime_access_application",
                return_value={
                    "id": "app-1",
                    "domain": controller.WINDOWS_RUNTIME_DOMAIN,
                    "type": "self_hosted",
                    "aud": "aud-1",
                },
            ),
            mock.patch.object(
                controller,
                "_service_tokens",
                return_value=[
                    {"id": "foreign-token", "name": controller.WINDOWS_SERVICE_TOKEN_NAME}
                ],
            ),
            mock.patch.object(controller, "_windows_runtime_policies", return_value=[]),
        ):
            census = controller._windows_service_auth_census(plan)
        self.assertFalse(census["eligible"])
        self.assertFalse(census["checks"]["service_token_remote_ownership_clean"])

    def test_private_value_materialization_is_atomic_and_owner_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "gateway" / "client-secret"
            controller._write_private_value(path, "secret-value")
            self.assertEqual(path.read_text(encoding="utf-8"), "secret-value\n")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)

    def test_exact_service_auth_policy_verification(self) -> None:
        policy = {
            "name": controller.WINDOWS_SERVICE_POLICY_NAME,
            "decision": "non_identity",
            "include": [{"service_token": {"token_id": "token-1"}}],
        }
        self.assertTrue(controller._verify_service_policy(policy, "token-1"))
        self.assertFalse(controller._verify_service_policy(policy, "token-2"))
