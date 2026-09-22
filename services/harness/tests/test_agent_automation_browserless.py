from __future__ import annotations
import importlib.util

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_browserless import (  # noqa: E402
    BrowserlessAutomationConfig,
    BrowserlessAutomationConflict,
    BrowserlessAutomationHold,
    BrowserlessAutomationService,
    BrowserlessCarrierBusy,
    _prompt_file_text,
)
from agent_automation_browserless_effects import BrowserlessEffectAdapter  # noqa: E402
from sqlite_conversation_materializer import TargetMaterializationObservation  # noqa: E402
from conversation_relay_carrier import MaterializationStanding  # noqa: E402


def spec():
    return {
        "campaignId": "campaign:test-browserless",
        "sharedPrompt": "Do bounded work.",
        "roster": [{"agentId": "A01", "roleCard": "Reviewer."}],
    }


def config(root: Path):
    token = root / "token"
    token.write_text("secret")
    return {
        "schemaVersion": 1,
        "stateRoot": str(root / "state"),
        "playwrightPython": "/venv/bin/python",
        "browserlessSubmitScript": str(ROOT / "scripts/playwright_browserless_chatgpt_submit.py"),
        "browserlessReconcileScript": str(
            ROOT / "scripts/playwright_browserless_binding_reconcile.py"
        ),
        "browserlessTurnScript": str(ROOT / "scripts/playwright_browserless_turn_once.py"),
        "browserlessPreflightScript": str(
            ROOT / "scripts/playwright_browserless_provider_preflight.py"
        ),
        "temporalPython": "/temporal/bin/python",
        "temporalLaunchScript": str(ROOT / "scripts/temporal_agent_automation_launch.py"),
        "temporalAddress": "127.0.0.1:7233",
        "temporalNamespace": "default",
        "temporalTaskQueue": "ordivon-agent-automation",
        "browserlessHumanHandoffMs": 300000,
        "waitStableSeconds": 150,
        "browserlessSessionTimeoutMs": 480000,
        "browserSubstrate": {
            "kind": "browserless",
            "endpoints": [
                {
                    "id": "carrier-a",
                    "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                    "httpEndpoint": "http://127.0.0.1:3011",
                    "operatorHttpEndpoint": "http://127.0.0.1:13111",
                    "tokenFile": str(token),
                    "networkNamespace": "surfpath-test",
                }
            ],
        },
    }


class BrowserlessAutomationServiceTests(unittest.TestCase):
    def test_prompt_file_accepts_one_conventional_terminal_newline(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "prompt.txt"
            path.write_text("continue exactly\n", encoding="utf-8")
            self.assertEqual(_prompt_file_text(path), "continue exactly")
            path.write_text("continue exactly", encoding="utf-8")
            self.assertEqual(_prompt_file_text(path), "continue exactly")

    def test_config_contains_no_local_chromium_allocator(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = BrowserlessAutomationConfig.from_dict(config(Path(d)))
            self.assertFalse(hasattr(cfg, "display_first"))
            self.assertFalse(hasattr(cfg, "cdp_port_first"))
            self.assertFalse(hasattr(cfg, "equipment_contract"))
            self.assertFalse(hasattr(cfg, "profile_templates"))
            self.assertFalse(hasattr(cfg, "runtime_mcp_endpoint"))
            self.assertFalse(hasattr(cfg, "runtime_mcp_token_file"))
            self.assertFalse(hasattr(cfg, "host_mcp_endpoint"))
            self.assertFalse(hasattr(cfg, "host_mcp_token_file"))
            self.assertFalse(hasattr(cfg, "mcp_probe_path"))

    def test_birth_uses_browserless_and_existing_effect_fence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(config(root)))

            class Target:
                def materialize(self, request):
                    return TargetMaterializationObservation(
                        standing=MaterializationStanding.BOUND,
                        provider_conversation_coordinate="https://chatgpt.com/c/abc",
                        evidence_digest="sha256:" + "2" * 64,
                        detail="fake Browserless bound",
                    )

                def reconcile(self, request):
                    raise AssertionError

            ready = {
                "standing": "READY",
                "endpointId": "carrier-a",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            with (
                mock.patch.object(effects.context, "provider_preflight", return_value=ready),
                mock.patch.object(effects, "_target", return_value=Target()),
            ):
                result = effects.materialize(sp, "A01")
            self.assertEqual(result["receipt"]["standing"], "bound")
            self.assertEqual(result["receipt"]["providerResource"], "https://chatgpt.com/c/abc")
            binding = json.loads(
                next((root / "state" / "materializations").glob("*/carrier-binding.json")).read_text()
            )
            self.assertEqual(set(binding), {"effectId", "endpointId", "endpointIdentityDigest"})
            self.assertEqual(binding["effectId"], result["effectId"])
            self.assertEqual(binding["endpointId"], "carrier-a")
            self.assertFalse(list((root / "state" / "materializations").glob("*/resources.json")))
            self.assertNotIn("capsuleDigest", binding)
            self.assertNotIn("schemaVersion", binding)
            self.assertNotIn("kind", binding)
            self.assertNotIn("secret", json.dumps(binding))

    def test_birth_replay_does_not_materialize_again(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(config(root)))

            class Target:
                def materialize(self, request):
                    return TargetMaterializationObservation(
                        standing=MaterializationStanding.BOUND,
                        provider_conversation_coordinate="https://chatgpt.com/c/abc",
                        evidence_digest="sha256:" + "2" * 64,
                    )

                def reconcile(self, request):
                    raise AssertionError

            ready = {
                "standing": "READY",
                "endpointId": "carrier-a",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            with (
                mock.patch.object(effects.context, "provider_preflight", return_value=ready),
                mock.patch.object(effects, "_target", return_value=Target()),
            ):
                effects.materialize(sp, "A01")
            with mock.patch.object(effects, "_target") as target:
                replay = effects.materialize(sp, "A01")
            target.assert_not_called()
            self.assertEqual(replay["action"], "existing-terminal")

    def test_external_campaign_launch_admits_temporal_instead_of_direct_birth(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            admitted = {
                "kind": "temporal-campaign-materialization-admission",
                "campaignId": "campaign:test-browserless",
                "campaignRef": "sha256:" + "1" * 64,
                "requested": 1,
                "workflowId": "campaign:" + "1" * 64,
                "workflowType": "ordivon.campaign.materialize",
                "disposition": "started",
                "effects": [{"agentId": "A01", "effectId": "effect:1"}],
            }
            with (
                mock.patch.object(
                    service,
                    "_require_materialization_substrate_available",
                    return_value={"healthy": True, "id": "carrier-a"},
                ) as health,
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                result = service.launch_campaign(sp)
            health.assert_called_once()
            preflight.assert_not_called()
            temporal.assert_called_once_with(
                sp, "campaign-materialize", campaign_agent_ids=("A01",)
            )
            self.assertFalse(hasattr(service, "birth"))
            self.assertEqual(result["temporal"]["workflowType"], "ordivon.campaign.materialize")

    def test_campaign_relaunch_never_creates_fresh_pre_effect_retry_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "campaignId": "campaign:test-browserless",
                "counts": {"pre-effect-failed": 1},
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "pre-effect-failed",
                        "providerResource": None,
                        "blindResendForbidden": False,
                    }
                ],
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_require_materialization_substrate_available") as substrate,
                mock.patch.object(service, "_temporal_admit") as temporal,
            ):
                out = service.launch_campaign(sp)
            substrate.assert_not_called()
            temporal.assert_not_called()
            self.assertEqual(out["preEffectRetries"], [])
            self.assertEqual(out["temporal"]["disposition"], "not-required")
            self.assertEqual(out["temporal"]["requested"], 0)

    def test_external_occurrence_birth_admits_temporal_instead_of_effect_activity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            admitted = {
                "workflowId": "wf-a",
                "workflowType": "ordivon.materialize",
                "disposition": "started",
            }
            with (
                mock.patch.object(
                    service,
                    "_require_materialization_substrate_available",
                    return_value={"healthy": True, "id": "carrier-a"},
                ) as health,
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                result = service.launch_reconcile(sp, "A01")
            health.assert_called_once()
            preflight.assert_not_called()
            temporal.assert_called_once_with(sp, "materialize", agent_id="A01")
            self.assertFalse(hasattr(service, "birth"))
            self.assertEqual(result["temporal"]["workflowId"], "wf-a")
            self.assertEqual(
                result["effectId"], service._materialization(service.load_spec(sp), "A01").request_id
            )
            self.assertNotIn("birthRequestId", result)

    def test_legacy_campaign_fields_are_rejected_before_temporal_admission(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            legacy = spec()
            legacy.update(
                {
                    "campaignRevision": "r1",
                    "maxOccurrences": 1,
                    "maxConcurrentBirths": 1,
                    "boardTopic": "historical-topic",
                    "lifecycleProtocol": "board-v1",
                }
            )
            sp = root / "legacy.json"
            sp.write_text(json.dumps(legacy))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            with mock.patch.object(service, "_temporal_admit") as temporal:
                with self.assertRaisesRegex(ValueError, "unsupported CampaignSpec fields"):
                    service.launch_campaign(sp)
            temporal.assert_not_called()

    def test_campaign_registry_lazy_fallback_does_not_swallow_dependency_import_failure(self):
        text = (ROOT / "scripts/agent_automation_browserless.py").read_text()
        temporal = text[
            text.index("    def _temporal_admit(") : text.index(
                "    def launch_campaign(", text.index("    def _temporal_admit(")
            )
        ]
        self.assertIn("except ModuleNotFoundError as error:", temporal)
        self.assertIn('if error.name != "agent_automation_registry":', temporal)
        self.assertIn("raise", temporal)

    @unittest.skipUnless(
        importlib.util.find_spec("rfc8785") is not None,
        "exact Agent Automation registry runtime is unavailable",
    )
    def test_temporal_admission_uses_durable_registered_spec_and_transient_prompt_transport(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source_spec = root / "caller-local-spec.json"
            source_spec.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            observed = {}

            def fake_run(command, **kwargs):
                prompt_idx = command.index("--prompt-file") + 1
                prompt_path = Path(command[prompt_idx])
                observed["prompt_path"] = prompt_path
                spec_idx = command.index("--spec") + 1
                durable_spec = Path(command[spec_idx])
                observed["durable_spec"] = durable_spec
                self.assertTrue(prompt_path.is_file())
                self.assertEqual(prompt_path.read_text(), "continue exactly")
                self.assertEqual(prompt_path.stat().st_mode & 0o777, 0o600)
                self.assertTrue(durable_spec.is_file())
                self.assertNotEqual(durable_spec, source_spec.resolve())
                self.assertEqual(
                    durable_spec.parent, root / "state" / "campaign-registry" / "blobs" / "sha256"
                )
                self.assertEqual(json.loads(durable_spec.read_text()), spec())
                return mock.Mock(
                    returncode=0,
                    stdout=json.dumps({"workflowId": "wf-turn", "disposition": "started"}) + "\n",
                    stderr="",
                )

            with mock.patch("agent_automation_browserless.subprocess.run", side_effect=fake_run):
                out = service._temporal_admit(
                    source_spec,
                    "continue",
                    agent_id="A01",
                    prompt="continue exactly",
                    turn_request_id="turn:1",
                )
            self.assertEqual(out["workflowId"], "wf-turn")
            self.assertFalse(observed["prompt_path"].exists())
            self.assertTrue(observed["durable_spec"].is_file())
            self.assertFalse((root / "state" / "mcp-turn-prompts").exists())

    def test_launch_continue_passes_prompt_to_temporal_not_persistent_registry(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            birth = service._materialization(service.load_spec(sp), "A01")
            endpoint = service.config.browserless_pool.endpoints[0]
            binding = service._binding_path(birth)
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    }
                )
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                    }
                ]
            }
            admitted = {
                "workflowId": "wf-c",
                "workflowType": "ordivon.agent.continue",
                "disposition": "started",
            }
            ready = {
                "standing": "READY",
                "endpointId": "carrier-a",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "provider_preflight", return_value=ready) as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                result = service.launch_continue(
                    sp,
                    "A01",
                    prompt="continue exactly",
                    turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
                )
            preflight.assert_called_once_with("carrier-a")
            temporal.assert_called_once_with(
                sp,
                "continue",
                agent_id="A01",
                prompt="continue exactly",
                turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
            )
            self.assertEqual(result["temporal"]["workflowId"], "wf-c")
            self.assertFalse((root / "state" / "mcp-turn-prompts").exists())

    def test_failed_continuation_reenters_with_fresh_temporal_execution_only_when_ledger_absent(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            endpoint = service.config.browserless_pool.endpoints[0]
            birth = service._materialization(service.load_spec(sp), "A01")
            binding = service._binding_path(birth)
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    }
                )
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                    }
                ]
            }
            initial = {"workflowId": "turn-logical", "disposition": "existing"}
            retry = {
                "workflowId": "retry-workflow",
                "disposition": "admitted",
                "retryStanding": "admitted-after-failed",
                "retryId": "0199-retry",
                "logicalWorkflowId": "017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
            }
            ready = {
                "standing": "READY",
                "endpointId": "carrier-a",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "provider_preflight", return_value=ready),
                mock.patch.object(service, "_turn_effect_row", side_effect=[None, None]) as ledger,
                mock.patch.object(
                    service, "_temporal_admit", side_effect=[initial, retry]
                ) as temporal,
            ):
                result = service.launch_continue(
                    sp,
                    "A01",
                    prompt="continue exactly",
                    turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
                )
            self.assertEqual(ledger.call_count, 2)
            self.assertEqual(
                temporal.call_args_list[0],
                mock.call(
                    sp,
                    "continue",
                    agent_id="A01",
                    prompt="continue exactly",
                    turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
                ),
            )
            self.assertEqual(
                temporal.call_args_list[1],
                mock.call(
                    sp,
                    "continue-retry",
                    agent_id="A01",
                    prompt="continue exactly",
                    turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
                ),
            )
            self.assertTrue(result["retryAdmitted"])
            self.assertEqual(result["temporal"]["retryId"], "0199-retry")

    def test_claimed_continuation_never_enters_retry_or_provider_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            endpoint = service.config.browserless_pool.endpoints[0]
            birth = service._materialization(service.load_spec(sp), "A01")
            binding = service._binding_path(birth)
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    }
                )
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                    }
                ]
            }
            claimed = {
                "state": "UNKNOWN",
                "promptDigest": "sha256:" + "1" * 64,
                "targetCoordinate": "https://chatgpt.com/c/abc",
                "receipt": None,
                "updatedAtMs": 1,
            }
            existing = {"workflowId": "turn-logical", "disposition": "existing"}
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_turn_effect_row", return_value=claimed),
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=existing) as temporal,
            ):
                result = service.launch_continue(
                    sp,
                    "A01",
                    prompt="continue exactly",
                    turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
                )
            preflight.assert_not_called()
            temporal.assert_called_once_with(
                sp,
                "continue",
                agent_id="A01",
                prompt="continue exactly",
                turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
            )
            self.assertFalse(result["retryAdmitted"])
            self.assertEqual(result["turnLedgerStanding"], "UNKNOWN")

    def test_continuation_failure_preserves_bounded_turn_script_detail(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(config(root)))
            birth = effects.context._materialization(effects.context.load_spec(sp), "A01")
            endpoint = effects.config.browserless_pool.endpoints[0]
            binding = effects.context._binding_path(birth)
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    }
                )
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                    }
                ]
            }
            failed = mock.Mock(
                returncode=1,
                stdout="",
                stderr="Browserless continuation conversation history did not hydrate before timeout\n",
            )
            with (
                mock.patch(
                    "agent_automation_browserless_effects.campaign_census", return_value=census
                ),
                mock.patch(
                    "agent_automation_browserless_effects.subprocess.run", return_value=failed
                ),
            ):
                with self.assertRaisesRegex(
                    BrowserlessAutomationHold, "history did not hydrate before timeout"
                ):
                    effects.send_turn(sp, "A01", prompt="continue", turn_request_id="turn:1")

    def test_new_birth_provider_gate_is_worker_owned_not_public_ui_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            admitted = {
                "workflowId": "wf-human",
                "workflowType": "ordivon.materialize",
                "disposition": "started",
            }
            with (
                mock.patch.object(
                    service,
                    "_require_materialization_substrate_available",
                    return_value={"healthy": True, "id": "carrier-a"},
                ) as health,
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                out = service.launch_reconcile(sp, "A01")
            health.assert_called_once()
            preflight.assert_not_called()
            temporal.assert_called_once_with(sp, "materialize", agent_id="A01")
            self.assertEqual(out["temporal"]["workflowId"], "wf-human")
            self.assertFalse(service.config.ledger.exists())

    def test_bound_birth_skips_provider_ready_gate_and_remains_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                        "blindResendForbidden": True,
                    }
                ]
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit") as temporal,
            ):
                out = service.launch_reconcile(sp, "A01")
            preflight.assert_not_called()
            temporal.assert_not_called()
            self.assertEqual(out["census"]["materializations"][0]["materializationStanding"], "bound")

    def test_pre_effect_failed_birth_reenters_same_effect_with_fresh_temporal_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "pre-effect-failed",
                        "providerResource": None,
                        "blindResendForbidden": False,
                    }
                ]
            }
            admitted = {
                "workflowId": "0199-retry",
                "workflowType": "ordivon.materialize",
                "disposition": "started",
                "retryId": "0199-retry",
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(
                    service,
                    "_require_materialization_substrate_available",
                    return_value={"healthy": True, "id": "carrier-a"},
                ) as health,
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                out = service.launch_reconcile(sp, "A01")
            health.assert_called_once()
            preflight.assert_not_called()
            temporal.assert_called_once_with(sp, "pre-effect-retry", agent_id="A01")
            self.assertEqual(out["temporal"]["retryId"], "0199-retry")

    def test_challenge_gated_continue_is_held_before_temporal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            birth = service._materialization(service.load_spec(sp), "A01")
            endpoint = service.config.browserless_pool.endpoints[0]
            binding = service._binding_path(birth)
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    }
                )
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                    }
                ]
            }
            blocked = {
                "standing": "CHALLENGE_GATED",
                "endpointId": "carrier-a",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "provider_preflight", return_value=blocked),
                mock.patch.object(service, "_temporal_admit") as temporal,
            ):
                with self.assertRaisesRegex(
                    BrowserlessAutomationHold,
                    "CHALLENGE_GATED.*no new provider-effect workflow admitted",
                ):
                    service.launch_continue(
                        sp,
                        "A01",
                        prompt="continue",
                        turn_request_id="017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
                    )
            temporal.assert_not_called()

    def test_human_handoff_info_exposes_bounded_current_vnc_transport(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            birth = service._materialization(service.load_spec(sp), "A01")
            path = (
                service._materialization_dir(birth)
                / "human-handoff"
                / f"{__import__('hashlib').sha256(birth.request_id.encode()).hexdigest()[:24]}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            from browserless_human_handoff import digest_obj

            value = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-human-verification-handoff",
                "effectId": birth.request_id,
                "promptDigest": "sha256:" + "1" * 64,
                "browserlessEndpointId": "carrier-a",
                "providerEffectAttempted": False,
                "assistantOutputRead": False,
                "blocker": "challenge-gated",
                "mode": "self-hosted-vnc",
                "trackingId": "h-1",
                "transportInstance": 11,
                "operatorURL": "http://127.0.0.1:16011/vnc.html?host=127.0.0.1&port=16011&path=websockify",
                "sessionActive": True,
                "sessionActiveUntilMs": 9999999999999,
            }
            value["handoffDigest"] = digest_obj(value)
            path.write_text(json.dumps(value))
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "human-required",
                        "providerResource": None,
                        "blindResendForbidden": False,
                    }
                ]
            }
            transport = {"standing": "READY", "operatorURL": value["operatorURL"]}
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch("browserless_human_interaction.observe", return_value=transport),
            ):
                row = service.human_handoff_info(sp, "A01")
            self.assertEqual(row["handoffURL"], value["operatorURL"])
            self.assertEqual(row["mode"], "self-hosted-vnc")
            self.assertFalse(row["providerEffectAttempted"])
            self.assertTrue(row["sessionActive"])
            self.assertNotIn("debuggerURL", row)
            self.assertNotIn("inspectorURL", row)

    def test_human_handoff_info_rejects_stale_or_absent_vnc_transport(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            birth = service._materialization(service.load_spec(sp), "A01")
            path = (
                service._materialization_dir(birth)
                / "human-handoff"
                / f"{__import__('hashlib').sha256(birth.request_id.encode()).hexdigest()[:24]}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            from browserless_human_handoff import digest_obj

            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "human-required",
                        "providerResource": None,
                        "blindResendForbidden": False,
                    }
                ]
            }
            base = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-human-verification-handoff",
                "effectId": birth.request_id,
                "promptDigest": "sha256:" + "1" * 64,
                "browserlessEndpointId": "carrier-a",
                "providerEffectAttempted": False,
                "assistantOutputRead": False,
                "blocker": "challenge-gated",
                "mode": "self-hosted-vnc",
                "trackingId": "h-1",
                "transportInstance": 11,
                "operatorURL": "http://127.0.0.1:16011/vnc.html",
                "sessionActive": True,
            }
            stale = dict(base, sessionActiveUntilMs=1)
            stale["handoffDigest"] = digest_obj(stale)
            path.write_text(json.dumps(stale))
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch(
                    "browserless_human_interaction.observe", return_value={"standing": "READY"}
                ),
                self.assertRaisesRegex(BrowserlessAutomationHold, "not current"),
            ):
                service.human_handoff_info(sp, "A01")
            current = dict(base, sessionActiveUntilMs=9999999999999)
            current["handoffDigest"] = digest_obj(current)
            path.write_text(json.dumps(current))
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch(
                    "browserless_human_interaction.observe", return_value={"standing": "CLOSED"}
                ),
                self.assertRaisesRegex(BrowserlessAutomationHold, "not current"),
            ):
                service.human_handoff_info(sp, "A01")

    def test_worker_resume_after_human_preserves_materialization_effect_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(config(root)))
            request = effects.context._materialization(effects.context.load_spec(sp), "A01")
            endpoint = effects.config.browserless_pool.endpoints[0]
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "human-required",
                        "providerResource": None,
                        "blindResendForbidden": False,
                    }
                ]
            }
            receipt = mock.Mock(
                standing=MaterializationStanding.BOUND,
                provider_conversation_coordinate="https://chatgpt.com/c/abc",
                evidence_digest="sha256:" + "2" * 64,
                detail="resumed",
                receipt_digest="sha256:" + "3" * 64,
            )
            materializer = mock.Mock()
            materializer.resume_human.return_value = receipt
            with (
                mock.patch(
                    "agent_automation_browserless_effects.campaign_census", return_value=census
                ),
                mock.patch.object(
                    effects.context,
                    "_current_binding",
                    return_value={
                        "effectId": request.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    },
                ),
                mock.patch(
                    "agent_automation_browserless_effects.SQLiteConversationMaterializer",
                    return_value=materializer,
                ),
            ):
                result = effects.resume_after_human(sp, "A01")
            materializer.resume_human.assert_called_once_with(request)
            self.assertEqual(result["effectId"], request.request_id)
            self.assertEqual(result["receipt"]["standing"], "bound")

    def test_config_accepts_https_public_handoff_origin(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = config(Path(d))
            cfg["browserlessHumanPublicOrigins"] = {
                "carrier-a": "https://handoff-11.ordivon.com"
            }
            parsed = BrowserlessAutomationConfig.from_dict(cfg)
            self.assertEqual(
                parsed.browserless_human_public_origins["carrier-a"],
                "https://handoff-11.ordivon.com",
            )

    def test_config_rejects_non_https_public_handoff_origin(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = config(Path(d))
            cfg["browserlessHumanPublicOrigins"] = {
                "carrier-a": "http://handoff-11.ordivon.com"
            }
            with self.assertRaisesRegex(ValueError, "HTTPS origin"):
                BrowserlessAutomationConfig.from_dict(cfg)

    def test_public_handoff_url_uses_https_origin_without_mutating_receipt(self):
        from agent_automation_browserless import _project_public_handoff_url

        local = "http://127.0.0.1:16011/vnc.html?host=127.0.0.1&port=16011&path=websockify&autoconnect=1&resize=scale"
        projected = _project_public_handoff_url("https://handoff-11.ordivon.com", local)
        self.assertEqual(
            projected,
            "https://handoff-11.ordivon.com/vnc.html?host=handoff-11.ordivon.com&port=443&path=websockify&autoconnect=1&resize=scale&encrypt=1",
        )
        self.assertIn("127.0.0.1:16011", local)

    def test_human_resume_admits_temporal_only_for_human_required(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "human-required",
                        "providerResource": None,
                        "blindResendForbidden": False,
                    }
                ]
            }
            birth = service._materialization(service.load_spec(sp), "A01")
            path = (
                service._materialization_dir(birth)
                / "human-handoff"
                / f"{__import__('hashlib').sha256(birth.request_id.encode()).hexdigest()[:24]}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            from browserless_human_handoff import digest_obj

            handoff = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-human-verification-handoff",
                "mode": "self-hosted-vnc",
                "effectId": birth.request_id,
                "promptDigest": "sha256:" + "1" * 64,
                "browserlessEndpointId": "carrier-a",
                "providerEffectAttempted": False,
                "assistantOutputRead": False,
                "blocker": "challenge-gated",
                "sessionActive": False,
            }
            handoff["handoffDigest"] = digest_obj(handoff)
            path.write_text(json.dumps(handoff))
            admitted = {
                "workflowId": handoff["handoffDigest"],
                "workflowType": "ordivon.agent.human-resume",
                "disposition": "started",
                "resumeId": handoff["handoffDigest"],
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                row = service.launch_human_resume(sp, "A01")
            temporal.assert_called_once_with(
                sp, "human-resume", agent_id="A01", resume_id=handoff["handoffDigest"]
            )
            self.assertEqual(row["temporal"]["workflowId"], handoff["handoffDigest"])

    def test_human_resume_rejects_current_or_unknown_self_hosted_session(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "human-required",
                        "providerResource": None,
                        "blindResendForbidden": False,
                    }
                ]
            }
            birth = service._materialization(service.load_spec(sp), "A01")
            path = (
                service._materialization_dir(birth)
                / "human-handoff"
                / f"{__import__('hashlib').sha256(birth.request_id.encode()).hexdigest()[:24]}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            from browserless_human_handoff import digest_obj

            h = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-human-verification-handoff",
                "mode": "self-hosted-vnc",
                "effectId": birth.request_id,
                "promptDigest": "sha256:" + "1" * 64,
                "browserlessEndpointId": "carrier-a",
                "providerEffectAttempted": False,
                "assistantOutputRead": False,
                "blocker": "challenge-gated",
                "trackingId": "h-1",
                "transportInstance": 11,
                "operatorURL": "http://127.0.0.1:16011/vnc.html",
                "sessionActive": True,
                "sessionActiveUntilMs": 9999999999999,
            }
            h["handoffDigest"] = digest_obj(h)
            path.write_text(json.dumps(h))
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch(
                    "browserless_human_interaction.observe", return_value={"standing": "READY"}
                ),
                mock.patch.object(service, "_temporal_admit") as temporal,
            ):
                with self.assertRaisesRegex(BrowserlessAutomationHold, "CURRENT"):
                    service.launch_human_resume(sp, "A01")
                temporal.assert_not_called()
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch(
                    "browserless_human_interaction.observe",
                    side_effect=RuntimeError("observe failed"),
                ),
                mock.patch.object(service, "_temporal_admit") as temporal,
            ):
                with self.assertRaisesRegex(BrowserlessAutomationHold, "UNKNOWN"):
                    service.launch_human_resume(sp, "A01")
                temporal.assert_not_called()

    def test_current_binding_record_is_minimal_and_endpoint_identity_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            birth = service._materialization(service.load_spec(sp), "A01")
            endpoint = service.config.browserless_pool.endpoints[0]
            path = service._binding_path(birth)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    }
                )
            )
            row = service._current_binding(birth)
            self.assertEqual(set(row), {"effectId", "endpointId", "endpointIdentityDigest"})
            path.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": "sha256:" + "0" * 64,
                    }
                )
            )
            with self.assertRaisesRegex(BrowserlessAutomationConflict, "endpoint identity changed"):
                service._current_binding(birth)

    def test_census_projects_only_reality_bound_human_handoff_without_exposing_url(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            birth = service._materialization(service.load_spec(sp), "A01")
            path = (
                service._materialization_dir(birth)
                / "human-handoff"
                / f"{__import__('hashlib').sha256(birth.request_id.encode()).hexdigest()[:24]}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            from browserless_human_handoff import digest_obj

            handoff = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-human-verification-handoff",
                "mode": "self-hosted-vnc",
                "effectId": birth.request_id,
                "promptDigest": "sha256:" + "1" * 64,
                "browserlessEndpointId": "carrier-a",
                "providerEffectAttempted": False,
                "assistantOutputRead": False,
                "blocker": "challenge-gated",
                "trackingId": "h-1",
                "transportInstance": 11,
                "operatorURL": "http://127.0.0.1:16011/secret",
                "sessionActive": True,
                "sessionActiveUntilMs": 9999999999999,
            }
            handoff["handoffDigest"] = digest_obj(handoff)
            path.write_text(json.dumps(handoff))
            raw = {
                "campaignId": "campaign:test-browserless",
                "requested": 1,
                "counts": {"unknown": 1},
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "unknown",
                        "providerResource": None,
                        "blindResendForbidden": True,
                    }
                ],
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=raw),
                mock.patch(
                    "browserless_human_interaction.observe", return_value={"standing": "READY"}
                ),
            ):
                out = service.census(sp)
            self.assertEqual(out["activeHumanHandoffs"], 1)
            self.assertTrue(out["materializations"][0]["humanHandoffAvailable"])
            self.assertNotIn("operatorURL", json.dumps(out))
            handoff.pop("handoffDigest")
            handoff["sessionActiveUntilMs"] = 1
            handoff["handoffDigest"] = digest_obj(handoff)
            path.write_text(json.dumps(handoff))
            raw2 = {
                "campaignId": "campaign:test-browserless",
                "requested": 1,
                "counts": {"unknown": 1},
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "unknown",
                        "providerResource": None,
                        "blindResendForbidden": True,
                    }
                ],
            }
            with mock.patch("agent_automation_browserless.campaign_census", return_value=raw2):
                stale = service.census(sp)
            self.assertEqual(stale["activeHumanHandoffs"], 0)
            self.assertNotIn("humanHandoffAvailable", stale["materializations"][0])

    def test_carrier_lease_excludes_a_second_process_and_releases_cleanly(self):
        import subprocess as sp
        from agent_automation_browserless import BrowserlessCarrierBusy, _carrier_lease
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = SimpleNamespace(state_root=root)
            holder_code = (
                "import sys,time; from pathlib import Path; from types import SimpleNamespace; "
                f"sys.path.insert(0,{str(ROOT / 'scripts')!r}); "
                "from agent_automation_browserless import _carrier_lease; "
                f"cfg=SimpleNamespace(state_root=Path({str(root)!r})); "
                "cm=_carrier_lease(cfg,'carrier-a',blocking=True); cm.__enter__(); "
                "print('LOCKED',flush=True); time.sleep(1); cm.__exit__(None,None,None)"
            )
            proc = sp.Popen(
                [sys.executable, "-c", holder_code], stdout=sp.PIPE, stderr=sp.PIPE, text=True
            )
            try:
                self.assertEqual(proc.stdout.readline().strip(), "LOCKED")
                with self.assertRaises(BrowserlessCarrierBusy):
                    with _carrier_lease(cfg, "carrier-a", blocking=False):
                        pass
                self.assertEqual(proc.wait(timeout=3), 0, proc.stderr.read())
                with _carrier_lease(cfg, "carrier-a", blocking=False):
                    pass
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=3)
                if proc.stdout is not None:
                    proc.stdout.close()
                if proc.stderr is not None:
                    proc.stderr.close()

    def test_managed_carrier_starts_on_demand_before_health(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = config(root)
            raw["browserSubstrate"]["endpoints"][0]["serviceUnit"] = "ordivon-browserless@11.service"
            raw["browserlessStartTimeoutSeconds"] = 1
            service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(raw))
            endpoint = service.config.browserless_pool.endpoints[0]
            with (
                mock.patch(
                    "agent_automation_browserless.subprocess.run",
                    side_effect=[
                        mock.Mock(returncode=3, stdout="", stderr=""),
                        mock.Mock(returncode=0, stdout="", stderr=""),
                    ],
                ) as run,
                mock.patch(
                    "browserless_substrate.BrowserlessEndpoint.health",
                    return_value={"id": "carrier-a", "healthy": True},
                ),
            ):
                observed = service.ensure_endpoint_active(endpoint)
            self.assertTrue(observed["healthy"])
            self.assertTrue(observed["lifecycleStarted"])
            stamps = list((service.config.state_root / "carrier-lifecycle").glob("*.last-use"))
            self.assertEqual(len(stamps), 1)
            self.assertEqual(stamps[0].stat().st_mode & 0o777, 0o600)
            self.assertEqual(run.call_args_list[1].args[0], ["/usr/bin/systemctl", "start", "ordivon-browserless@11.service"])

    def test_cf07_preflight_telemetry_persists_only_allowlisted_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            source = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-provider-preflight",
                "endpointId": "carrier-a",
                "standing": "CHALLENGE_GATED",
                "pageRef": "https://chatgpt.com/?secret=query",
                "detail": "sensitive-diagnostic-detail",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
                "substrateHealth": {"healthy": True, "token": "must-not-persist"},
            }
            observed = service._record_cf07_preflight(
                source,
                lifecycle_started=True,
                session_count_class="ZERO",
            )
            self.assertEqual(observed["standing"], "CHALLENGE_GATED")
            self.assertEqual(observed["cf07Telemetry"]["standing"], "RECORDED")
            events = list(
                (service.config.state_root / "cf07-provider-preflight-events").glob("*.json")
            )
            self.assertEqual(len(events), 1)
            event = json.loads(events[0].read_text())
            self.assertEqual(
                set(event),
                {
                    "schemaVersion",
                    "kind",
                    "observedAtMs",
                    "endpointId",
                    "standing",
                    "lifecycleStarted",
                    "sessionCountClass",
                    "providerEffectAttempted",
                    "clicked",
                    "composerFilled",
                    "sendAttempted",
                    "assistantOutputRead",
                    "profileFirstObservedAtMs",
                    "semanticProviderSessionCreationKnown",
                },
            )
            self.assertEqual(event["standing"], "CHALLENGE_GATED")
            self.assertTrue(event["lifecycleStarted"])
            self.assertEqual(event["sessionCountClass"], "ZERO")
            self.assertFalse(event["semanticProviderSessionCreationKnown"])
            serialized = json.dumps(event, sort_keys=True)
            self.assertNotIn("chatgpt.com", serialized)
            self.assertNotIn("secret", serialized)
            self.assertNotIn("sensitive-diagnostic-detail", serialized)
            self.assertNotIn("must-not-persist", serialized)
            self.assertEqual(events[0].stat().st_mode & 0o777, 0o600)

    def test_cf07_profile_first_observed_marker_is_create_once(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            source = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-provider-preflight",
                "endpointId": "carrier-a",
                "standing": "CHALLENGE_GATED",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            first = service._record_cf07_preflight(
                source, lifecycle_started=False, session_count_class="ZERO"
            )
            second = service._record_cf07_preflight(
                source, lifecycle_started=False, session_count_class="ZERO"
            )
            self.assertEqual(
                first["cf07Telemetry"]["profileFirstObservedAtMs"],
                second["cf07Telemetry"]["profileFirstObservedAtMs"],
            )
            markers = list(
                (service.config.state_root / "cf07-profile-first-observed").glob("*.json")
            )
            events = list(
                (service.config.state_root / "cf07-provider-preflight-events").glob("*.json")
            )
            self.assertEqual(len(markers), 1)
            self.assertEqual(len(events), 2)
            marker_value = json.loads(markers[0].read_text())
            self.assertFalse(marker_value["semanticProviderSessionCreationKnown"])
            self.assertEqual(markers[0].stat().st_mode & 0o777, 0o600)

    def test_provider_preflight_returns_carrier_busy_without_opening_browser(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            endpoint = mock.Mock()
            endpoint.endpoint_id = "carrier-a"
            endpoint.health.return_value = {"healthy": True, "id": "carrier-a"}
            endpoint.sessions.return_value = [{"type": "browser", "running": True}]
            with (
                mock.patch.object(service, "_endpoint_by_id", return_value=endpoint),
                mock.patch("agent_automation_browserless.subprocess.run") as run,
            ):
                result = service.provider_preflight("carrier-a")
            self.assertEqual(result["standing"], "CARRIER_BUSY")
            self.assertFalse(result["providerEffectAttempted"])
            self.assertEqual(result["cf07Telemetry"]["standing"], "RECORDED")
            self.assertEqual(result["cf07Telemetry"]["sessionCountClass"], "NONZERO")
            endpoint.sessions.assert_called_once_with(timeout_seconds=3)
            run.assert_not_called()

    def test_provider_preflight_records_lease_busy_without_opening_browser(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            endpoint = mock.Mock()
            endpoint.endpoint_id = "carrier-a"
            endpoint.health.return_value = {"healthy": True, "id": "carrier-a"}
            with (
                mock.patch.object(service, "_endpoint_by_id", return_value=endpoint),
                mock.patch(
                    "agent_automation_browserless._carrier_lease",
                    side_effect=BrowserlessCarrierBusy("busy"),
                ),
                mock.patch("agent_automation_browserless.subprocess.run") as run,
            ):
                result = service.provider_preflight("carrier-a")
            self.assertEqual(result["standing"], "CARRIER_BUSY")
            self.assertEqual(result["cf07Telemetry"]["standing"], "RECORDED")
            self.assertEqual(result["cf07Telemetry"]["sessionCountClass"], "LEASE_BUSY")
            endpoint.health.assert_called_once_with(timeout_seconds=5)
            run.assert_not_called()

    def test_provider_preflight_requires_explicit_endpoint_and_read_only_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            fake = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-provider-preflight",
                "endpointId": "carrier-a",
                "standing": "CHALLENGE_GATED",
                "pageRef": "https://chatgpt.com/",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            completed = mock.Mock(returncode=0, stdout=json.dumps(fake) + "\n", stderr="")
            with (
                mock.patch(
                    "browserless_substrate.BrowserlessEndpoint.health",
                    return_value={"id": "carrier-a", "healthy": True, "status": 204},
                ),
                mock.patch("browserless_substrate.BrowserlessEndpoint.sessions", return_value=[]),
                mock.patch(
                    "agent_automation_browserless.subprocess.run", return_value=completed
                ) as run,
            ):
                result = service.provider_preflight("carrier-a")
            self.assertEqual(result["standing"], "CHALLENGE_GATED")
            self.assertFalse(result["providerEffectAttempted"])
            self.assertEqual(result["cf07Telemetry"]["standing"], "RECORDED")
            self.assertEqual(result["cf07Telemetry"]["sessionCountClass"], "ZERO")
            diagnosis = result["providerBoundaryDiagnosis"]
            self.assertEqual(
                diagnosis["state"], "SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE"
            )
            self.assertEqual(diagnosis["substrateStanding"], "HEALTHY")
            self.assertEqual(diagnosis["providerAdmission"], "NOT_ADMISSIBLE")
            self.assertEqual(diagnosis["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
            self.assertEqual(diagnosis["providerAction"], "PRE_EFFECT_HOLD")
            self.assertFalse(diagnosis["humanVerificationEligible"])
            self.assertFalse(diagnosis["automaticInfrastructureMutationAllowed"])
            command = run.call_args.args[0]
            self.assertIn("--endpoint-id", command)
            self.assertNotIn("send", " ".join(command).lower())

    def test_public_facade_has_no_derived_compilation_writer(self):
        text = (ROOT / "scripts/agent_automation_browserless.py").read_text()
        self.assertNotIn("def compile(self, spec_path", text)
        self.assertNotIn("write_compilation", text)

    def test_doctor_observes_unmanaged_browser_health(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            endpoint = service.config.browserless_pool.endpoints[0]
            with mock.patch(
                "browserless_substrate.BrowserlessEndpoint.health",
                return_value={
                    "id": endpoint.endpoint_id,
                    "healthy": True,
                    "identityDigest": endpoint.identity_digest,
                },
            ):
                result = service.doctor()
            self.assertTrue(result["healthy"])
            self.assertEqual(result["browserSubstrate"]["kind"], "browserless")
            self.assertEqual(
                result["browserSubstrate"]["endpoints"][0]["lifecycleStanding"],
                "UNMANAGED_OBSERVED",
            )
            policy = result["providerBoundaryPolicy"]
            self.assertEqual(policy["policyVersion"], "provider-boundary-r2")
            self.assertEqual(
                policy["neutralAttributionReference"],
                {
                    "reference": "browser-security-r9",
                    "standing": "REFERENCE_ONLY_NOT_LIVE_ASSERTION",
                },
            )
            self.assertFalse(policy["automaticInfrastructureMutationFromProviderBoundary"])

    def test_doctor_marks_cold_managed_endpoint_sleeping_without_curl(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = config(root)
            endpoint_raw = raw["browserSubstrate"]["endpoints"][0]
            endpoint_raw["serviceUnit"] = "ordivon-browserless@12.service"
            service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(raw))
            with (
                mock.patch(
                    "agent_automation_browserless.subprocess.run",
                    return_value=mock.Mock(returncode=3, stdout="", stderr=""),
                ),
                mock.patch("browserless_substrate.BrowserlessEndpoint.health") as health,
            ):
                result = service.doctor()
            health.assert_not_called()
            row = result["browserSubstrate"]["endpoints"][0]
            self.assertEqual(row["lifecycleStanding"], "SLEEPING_ON_DEMAND")
            self.assertTrue(row["healthy"])
            self.assertTrue(result["healthy"])

    def test_doctor_fails_closed_when_warm_endpoint_is_inactive(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = config(root)
            endpoint_raw = raw["browserSubstrate"]["endpoints"][0]
            endpoint_raw["serviceUnit"] = "ordivon-browserless@11.service"
            raw["browserlessWarmEndpointIds"] = ["carrier-a"]
            service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(raw))
            with (
                mock.patch(
                    "agent_automation_browserless.subprocess.run",
                    return_value=mock.Mock(returncode=3, stdout="", stderr=""),
                ),
                mock.patch("browserless_substrate.BrowserlessEndpoint.health") as health,
            ):
                result = service.doctor()
            health.assert_not_called()
            row = result["browserSubstrate"]["endpoints"][0]
            self.assertEqual(row["lifecycleStanding"], "WARM_ENDPOINT_INACTIVE")
            self.assertFalse(row["healthy"])
            self.assertFalse(result["healthy"])

    def test_turn_effect_ledger_uses_current_neutral_names(self):
        facade = (ROOT / "scripts/agent_automation_browserless.py").read_text()
        turn = (ROOT / "scripts/playwright_browserless_turn_once.py").read_text()
        self.assertIn("turn-ledger.sqlite", facade)
        self.assertIn("turn_effects", turn)
        self.assertNotIn("retained-turn-ledger.sqlite", facade)
        self.assertNotIn("retained_turn_effects", turn)

    def test_bound_continuation_uses_current_carrier_binding(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(config(root)))
            birth = effects.context._materialization(effects.context.load_spec(sp), "A01")
            endpoint = effects.config.browserless_pool.endpoints[0]
            binding = effects.context._binding_path(birth)
            binding.parent.mkdir(parents=True, exist_ok=True)
            binding.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": endpoint.identity_digest,
                    }
                )
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                    }
                ]
            }
            completed = mock.Mock(
                returncode=0,
                stdout=json.dumps(
                    {
                        "schemaVersion": 1,
                        "kind": "ordivon.browserless-turn-replay",
                        "turnRequestId": "turn:1",
                        "standing": "UNKNOWN",
                        "safeToResend": False,
                    }
                )
                + "\n",
                stderr="",
            )
            with (
                mock.patch(
                    "agent_automation_browserless_effects.campaign_census", return_value=census
                ),
                mock.patch(
                    "agent_automation_browserless_effects.subprocess.run", return_value=completed
                ) as run,
            ):
                result = effects.send_turn(sp, "A01", prompt="continue", turn_request_id="turn:1")
            self.assertFalse(result["safeToResend"])
            command = run.call_args.args[0]
            self.assertIn("--target-resource", command)
            self.assertIn("https://chatgpt.com/c/abc", command)
            self.assertEqual(command[command.index("--endpoint-id") + 1], endpoint.endpoint_id)

    def test_stale_carrier_identity_is_not_rebound_during_ambiguous_reconciliation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(config(root)))
            birth = effects.context._materialization(effects.context.load_spec(sp), "A01")
            endpoint = effects.config.browserless_pool.endpoints[0]
            path = effects.context._binding_path(birth)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "effectId": birth.request_id,
                        "endpointId": endpoint.endpoint_id,
                        "endpointIdentityDigest": "sha256:" + "0" * 64,
                    }
                )
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "unknown",
                        "blindResendForbidden": True,
                        "providerResource": None,
                    }
                ]
            }
            with mock.patch(
                "agent_automation_browserless_effects.campaign_census", return_value=census
            ):
                result = effects.reconcile(sp, "A01")
            self.assertEqual(result["action"], "preserved-standing-no-current-carrier-evidence")
            self.assertEqual(result["reconciliationUnavailableReason"], "carrier-no-longer-current")
            self.assertFalse(result["safeToResend"])
            with self.assertRaisesRegex(BrowserlessAutomationConflict, "endpoint identity changed"):
                effects.context._current_binding(birth)

    def test_ambiguous_birth_replay_preserves_no_resend_without_current_binding(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(config(root)))
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "unknown",
                        "blindResendForbidden": True,
                        "providerResource": None,
                    }
                ]
            }
            with (
                mock.patch(
                    "agent_automation_browserless_effects.campaign_census", return_value=census
                ),
                mock.patch.object(effects.context, "_current_binding", return_value=None),
                mock.patch.object(effects, "reconcile") as reconcile,
            ):
                result = effects.materialize(sp, "A01")
            reconcile.assert_not_called()
            self.assertEqual(result["action"], "existing-effect-unknown-no-resend")
            self.assertFalse(result["safeToResend"])

    def test_external_reconcile_admits_temporal_instead_of_direct_ledger_or_provider_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "unknown",
                        "blindResendForbidden": True,
                        "providerResource": None,
                    }
                ]
            }
            admitted = {
                "workflowId": "wf-r",
                "workflowType": "ordivon.agent.reconcile",
                "disposition": "started",
                "observationId": "0199-test",
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                result = service.launch_reconcile(sp, "A01")
            temporal.assert_called_once_with(sp, "reconcile", agent_id="A01")
            self.assertFalse(hasattr(service, "reconcile"))
            self.assertEqual(result["temporal"]["workflowId"], "wf-r")
            self.assertFalse(result["safeToResend"])

    def test_cli_reconcile_routes_to_temporal_admission_not_raw_reconcile(self):
        text = (ROOT / "scripts/agent_automation_browserless.py").read_text()
        self.assertIn('elif a.action == "reconcile":', text)
        self.assertIn('r = svc.launch_reconcile(a.spec, a.agent_id)', text)
        self.assertNotIn('r = svc.reconcile(a.spec, a.agent_id)', text)

    def test_reconcile_admission_treats_bound_occurrence_as_converged_noop(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "blindResendForbidden": True,
                        "providerResource": "https://chatgpt.com/c/x",
                    }
                ]
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_temporal_admit") as temporal,
            ):
                result = service.launch_reconcile(sp, "A01")
                temporal.assert_not_called()
                self.assertEqual(
                    result["census"]["materializations"][0]["materializationStanding"],
                    "bound",
                )

    def test_reconcile_admission_reenters_pre_effect_failed_with_same_effect_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "pre-effect-failed",
                        "blindResendForbidden": False,
                        "providerResource": None,
                    }
                ]
            }
            admitted = {
                "workflowId": "wf-retry",
                "workflowType": "ordivon.materialize",
                "disposition": "started",
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_require_materialization_substrate_available") as substrate,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                result = service.launch_reconcile(sp, "A01")
            substrate.assert_called_once()
            temporal.assert_called_once_with(sp, "pre-effect-retry", agent_id="A01")
            self.assertEqual(result["temporal"]["workflowId"], "wf-retry")
            self.assertFalse(result["safeToResend"])


    def test_new_continuation_admission_requires_rfc9562_uuid7_before_temporal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "bound",
                        "providerResource": "https://chatgpt.com/c/abc",
                    }
                ]
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_temporal_admit") as temporal,
            ):
                with self.assertRaisesRegex(BrowserlessAutomationConflict, "RFC 9562 UUIDv7"):
                    service.launch_continue(sp, "A01", prompt="continue", turn_request_id="turn:1")
                temporal.assert_not_called()

    @unittest.skipUnless(
        importlib.util.find_spec("rfc8785") is not None,
        "exact Agent Automation registry runtime is unavailable",
    )
    def test_temporal_admission_receipt_loss_is_explicitly_ambiguous(self):
        from agent_automation_browserless import BrowserlessAutomationAmbiguous

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "caller-spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            completed = mock.Mock(returncode=0, stdout="not-json\n", stderr="")
            with mock.patch("agent_automation_browserless.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(BrowserlessAutomationAmbiguous, "outcome is unknown"):
                    service._temporal_admit(sp, "campaign-materialize")

    @unittest.skipUnless(
        importlib.util.find_spec("rfc8785") is not None,
        "exact Agent Automation registry runtime is unavailable",
    )
    def test_campaign_temporal_admission_requires_per_birth_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "caller-spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            completed = mock.Mock(
                returncode=0,
                stdout=json.dumps({"kind": "temporal-materialization-admissions", "workflows": []}) + "\n",
                stderr="",
            )
            with mock.patch("agent_automation_browserless.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(
                    __import__("agent_automation_browserless").BrowserlessAutomationAmbiguous,
                    "campaign admission outcome is unknown",
                ):
                    service._temporal_admit(sp, "campaign-materialize")

    def test_public_birth_admission_uses_substrate_only_not_provider_failover(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            cfg = config(root)
            first = cfg["browserSubstrate"]["endpoints"][0]
            second = dict(first)
            second["id"] = "carrier-b"
            second["websocketEndpoint"] = "ws://127.0.0.1:3012/chromium"
            second["httpEndpoint"] = "http://127.0.0.1:3012"
            second["operatorHttpEndpoint"] = "http://127.0.0.1:13112"
            cfg["browserSubstrate"]["endpoints"] = [first, second]
            service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(cfg))
            admitted = {
                "workflowId": "wf-a",
                "workflowType": "ordivon.materialize",
                "disposition": "started",
            }
            with (
                mock.patch.object(
                    service,
                    "_require_materialization_substrate_available",
                    return_value=service.config.browserless_pool.endpoints[1],
                ) as substrate,
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                out = service.launch_reconcile(sp, "A01")
            substrate.assert_called_once()
            preflight.assert_not_called()
            temporal.assert_called_once_with(sp, "materialize", agent_id="A01")
            self.assertEqual(out["temporal"]["workflowId"], "wf-a")

    def test_leased_provider_preflight_does_not_reacquire_and_self_conflict(self):
        from agent_automation_browserless import _carrier_lease

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            endpoint = service.config.browserless_pool.endpoints[0]
            ready = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-provider-preflight",
                "endpointId": endpoint.endpoint_id,
                "standing": "READY",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            completed = mock.Mock(returncode=0, stdout=json.dumps(ready) + "\n", stderr="")
            with (
                mock.patch(
                    "browserless_substrate.BrowserlessEndpoint.health",
                    return_value={"healthy": True, "id": endpoint.endpoint_id},
                ),
                mock.patch("browserless_substrate.BrowserlessEndpoint.sessions", return_value=[]),
                mock.patch("agent_automation_browserless.subprocess.run", return_value=completed),
            ):
                with _carrier_lease(service.config, endpoint.endpoint_id, blocking=True):
                    observed = service._provider_preflight_under_carrier_lease(endpoint.endpoint_id)
            self.assertEqual(observed["standing"], "READY")
            self.assertFalse(observed["providerEffectAttempted"])

    def test_worker_selected_effect_treats_only_carrier_transport_standings_as_failover(self):
        from agent_automation_browserless import PRE_SEND_CARRIER_FAILOVER_STANDINGS

        self.assertEqual(
            PRE_SEND_CARRIER_FAILOVER_STANDINGS,
            {"SUBSTRATE_UNAVAILABLE", "CARRIER_BUSY", "PROVIDER_UNAVAILABLE", "CONNECT_FAILED"},
        )
        for standing in sorted(PRE_SEND_CARRIER_FAILOVER_STANDINGS):
            with self.subTest(standing=standing), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                sp = root / "spec.json"
                sp.write_text(json.dumps(spec()))
                effects = BrowserlessEffectAdapter(
                    BrowserlessAutomationConfig.from_dict(config(root))
                )
                endpoint = effects.config.browserless_pool.endpoints[0]
                observation = {
                    "standing": standing,
                    "endpointId": endpoint.endpoint_id,
                    "providerEffectAttempted": False,
                    "clicked": False,
                    "composerFilled": False,
                    "sendAttempted": False,
                    "assistantOutputRead": False,
                }
                with mock.patch.object(effects, "_target") as target:
                    result = effects.materialize(
                        sp, "A01", endpoint_id=endpoint.endpoint_id, provider_preflight=observation
                    )
                self.assertEqual(result["action"], "carrier-pre-effect-unavailable")
                target.assert_not_called()
                self.assertFalse(
                    any((root / "state" / "materializations").glob("*/carrier-binding.json"))
                )

    def test_provider_policy_and_ui_standings_do_not_rotate_carriers(self):
        # AUTH_REQUIRED now transfers to the durable CfT human-auth path and is covered by
        # test_durable_human_materialization.py. The remaining provider/UI standings stay
        # pre-effect on the selected Browserless carrier and must never rotate profiles.
        for standing in (
            "PROVIDER_RATE_LIMITED",
            "CHALLENGE_GATED",
            "CONTEXT_UNAVAILABLE",
            "COMPOSER_UNAVAILABLE",
        ):
            with self.subTest(standing=standing), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                sp = root / "spec.json"
                sp.write_text(json.dumps(spec()))
                effects = BrowserlessEffectAdapter(
                    BrowserlessAutomationConfig.from_dict(config(root))
                )
                endpoint = effects.config.browserless_pool.endpoints[0]
                observation = {
                    "standing": standing,
                    "endpointId": endpoint.endpoint_id,
                    "providerEffectAttempted": False,
                    "clicked": False,
                    "composerFilled": False,
                    "sendAttempted": False,
                    "assistantOutputRead": False,
                    "substrateHealth": {"healthy": True},
                }

                class Target:
                    def materialize(self, request):
                        return TargetMaterializationObservation(
                            standing=MaterializationStanding.PRE_EFFECT_FAILED,
                            evidence_digest="sha256:" + "4" * 64,
                            detail="policy/ui blocker before SEND",
                        )

                    def reconcile(self, request):
                        raise AssertionError

                with mock.patch.object(effects, "_target", return_value=Target()) as target:
                    result = effects.materialize(
                        sp, "A01", endpoint_id=endpoint.endpoint_id, provider_preflight=observation
                    )
                self.assertEqual(result["action"], "materialize")
                self.assertEqual(result["receipt"]["standing"], "pre-effect-failed")
                diagnosis = result["providerBoundaryDiagnosis"]
                self.assertEqual(diagnosis["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
                self.assertFalse(diagnosis["automaticInfrastructureMutationAllowed"])
                for action in (
                    "rotate-carrier",
                    "restart-carrier",
                    "clear-profile",
                    "mutate-launcher-flags",
                    "mutate-network-authority",
                ):
                    self.assertIn(action, diagnosis["forbiddenAutomaticInfrastructureRepairs"])
                if standing == "AUTH_REQUIRED":
                    self.assertTrue(diagnosis["humanVerificationEligible"])
                    self.assertEqual(diagnosis["providerAction"], "HUMAN_CONTROL_TRANSFER")
                    self.assertIn(
                        "authorized-human-control-transfer", diagnosis["allowedAutomaticActions"]
                    )
                elif standing == "CHALLENGE_GATED":
                    self.assertFalse(diagnosis["humanVerificationEligible"])
                    self.assertEqual(diagnosis["providerAction"], "PRE_EFFECT_HOLD")
                    self.assertIn("hold-provider-effect", diagnosis["allowedAutomaticActions"])
                else:
                    self.assertFalse(diagnosis["humanVerificationEligible"])
                target.assert_called_once()
                binding = json.loads(
                    next(
                        (root / "state" / "materializations").glob("*/carrier-binding.json")
                    ).read_text()
                )
                self.assertEqual(binding["endpointId"], endpoint.endpoint_id)

    def test_effect_writer_requires_worker_selected_endpoint_and_binds_only_after_admissible_preflight(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            cfg = config(root)
            first = cfg["browserSubstrate"]["endpoints"][0]
            second = dict(first)
            second["id"] = "carrier-b"
            second["websocketEndpoint"] = "ws://127.0.0.1:3012/chromium"
            second["httpEndpoint"] = "http://127.0.0.1:3012"
            second["operatorHttpEndpoint"] = "http://127.0.0.1:13112"
            cfg["browserSubstrate"]["endpoints"] = [first, second]
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(cfg))
            birth = effects.context._materialization(effects.context.load_spec(sp), "A01")
            ordered = effects.config.browserless_pool.candidates(birth.request_id)
            unavailable = {
                "standing": "PROVIDER_UNAVAILABLE",
                "endpointId": ordered[0].endpoint_id,
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }
            with (
                mock.patch.object(effects.context, "provider_preflight", return_value=unavailable),
                mock.patch.object(effects, "_target") as target,
            ):
                first_result = effects.materialize(
                    sp, "A01", endpoint_id=ordered[0].endpoint_id, provider_preflight=unavailable
                )
            self.assertEqual(first_result["action"], "carrier-pre-effect-unavailable")
            target.assert_not_called()
            self.assertFalse(any((root / "state" / "materializations").glob("*/carrier-binding.json")))
            ready = {
                "standing": "READY",
                "endpointId": ordered[1].endpoint_id,
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
            }

            class Target:
                def materialize(self, request):
                    return TargetMaterializationObservation(
                        standing=MaterializationStanding.BOUND,
                        provider_conversation_coordinate="https://chatgpt.com/c/failover",
                        evidence_digest="sha256:" + "3" * 64,
                    )

                def reconcile(self, request):
                    raise AssertionError

            with (
                mock.patch.object(effects.context, "provider_preflight", return_value=ready),
                mock.patch.object(effects, "_target", return_value=Target()),
            ):
                result = effects.materialize(
                    sp, "A01", endpoint_id=ordered[1].endpoint_id, provider_preflight=ready
                )
            binding = json.loads(
                next((root / "state" / "materializations").glob("*/carrier-binding.json")).read_text()
            )
            self.assertEqual(binding["endpointId"], ordered[1].endpoint_id)
            self.assertEqual(result["receipt"]["standing"], "bound")

    def test_post_send_unknown_never_uses_failover_selection(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = BrowserlessAutomationService(
                BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": "submit-observed",
                        "providerResource": None,
                        "blindResendForbidden": True,
                    }
                ]
            }
            admitted = {
                "workflowId": "reconcile-1",
                "workflowType": "ordivon.agent.reconcile",
                "disposition": "started",
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "provider_preflight") as preflight,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                result = service.launch_reconcile(sp, "A01")
            preflight.assert_not_called()
            temporal.assert_called_once_with(sp, "reconcile", agent_id="A01")
            self.assertFalse(result["safeToResend"])


if __name__ == "__main__":
    unittest.main()


class WindowsUserBrowserCarrierTests(unittest.TestCase):
    def test_config_admits_explicit_windows_user_browser_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = config(root)
            raw['windowsUserBrowser'] = {
                'gatewayUrl': 'http://127.0.0.1:8899/mcp',
                'workspaceId': 'ws-user-browser-prod-r1',
                'powershellPath': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                'driverPath': r'C:\ProgramData\Ordivon\chat-ingress\windows_user_browser_chatgpt.ps1',
                'proxyUrl': 'http://127.0.0.1:19081',
                'linuxStageRoot': '/mnt/c/ProgramData/Ordivon/chat-ingress',
                'windowsStageRoot': r'C:\ProgramData\Ordivon\chat-ingress',
                'timeoutMs': 90000,
            }
            cfg = BrowserlessAutomationConfig.from_dict(raw)
            self.assertEqual(cfg.windows_user_browser.workspace_id, 'ws-user-browser-prod-r1')
            self.assertEqual(cfg.windows_user_browser.gateway_url, 'http://127.0.0.1:8899/mcp')

    def test_user_browser_materialize_reuses_existing_effect_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = config(root)
            raw['windowsUserBrowser'] = {
                'gatewayUrl': 'http://127.0.0.1:8899/mcp',
                'workspaceId': 'ws-user-browser-prod-r1',
                'powershellPath': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                'driverPath': r'C:\ProgramData\Ordivon\chat-ingress\windows_user_browser_chatgpt.ps1',
                'proxyUrl': 'http://127.0.0.1:19081',
                'linuxStageRoot': '/mnt/c/ProgramData/Ordivon/chat-ingress',
                'windowsStageRoot': r'C:\ProgramData\Ordivon\chat-ingress',
                'timeoutMs': 90000,
            }
            sp = root / 'spec.json'
            sp.write_text(json.dumps(spec()))
            effects = BrowserlessEffectAdapter(BrowserlessAutomationConfig.from_dict(raw))

            class Target:
                def materialize(self, request):
                    return TargetMaterializationObservation(
                        standing=MaterializationStanding.BOUND,
                        provider_conversation_coordinate='https://chatgpt.com/c/user-browser-canary',
                        evidence_digest='sha256:' + '7' * 64,
                        detail='fake user browser bound',
                    )
                def reconcile(self, request):
                    raise AssertionError

            with mock.patch.object(effects, '_user_browser_target', return_value=Target()):
                result = effects.materialize_user_browser(sp, 'A01')
            self.assertEqual(result['kind'], 'ordivon.user-browser-materialization')
            self.assertEqual(result['receipt']['standing'], 'bound')
            self.assertTrue(effects.config.ledger.is_file())
            self.assertFalse(list((root / 'state' / 'materializations').glob('*/carrier-binding.json')))
