import contextlib
import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import scripts.browserless_image_promotion as promotion


IMAGE_A = "ghcr.io/browserless/chromium@sha256:" + "a" * 64
IMAGE_B = "ghcr.io/browserless/chromium@sha256:" + "b" * 64
COMMIT = "1" * 40
NETWORK = "sha256:" + "c" * 64


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def quadlet(image: str, *, tz: str = "Asia/Shanghai") -> bytes:
    return f"[Container]\nImage={image}\nEnvironment=TZ={tz}\n".encode()


def canary(control: str, candidate: str, standing: str) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-browserless-canary-r1",
        "standing": standing,
        "pass": True,
        "controlImage": control,
        "candidateImage": candidate,
        "providerChallengeVisited": False,
        "providerSendAttempted": False,
        "productionMutationAttempted": False,
        "rootCauseEstablished": False,
    }


def pool_receipt(*, infra=None, families=None, local_infra=None, local_families=None) -> dict:
    return {
        "harnessRevision": COMMIT,
        "securityRevision": "0" * 40,
        "poolIndexSha256": "sha256:" + "e" * 64,
        "providerChallengeVisited": False,
        "providerSendAttempted": False,
        "classification": {
            "standing": "GLOBAL_DRIFT" if infra else "NO_OBSERVED_DRIFT",
            "detectorDriftCarriers": [],
            "sharedChangedFamilies": families or [],
            "carrierLocalChangedFamilies": local_families or {},
            "sharedInfrastructureChanges": infra or [],
            "carrierLocalInfrastructureChanges": local_infra or {},
            "challengeStandingChangedCarriers": [],
            "rootCauseEstablished": False,
        },
    }


class BrowserlessImagePromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.container"
        self.installed = self.root / "installed.container"
        self.config = self.root / "config.json"
        self.receipt = self.root / "canary.json"
        self.request = self.root / "request.json"
        self.promotion_root = self.root / "promotions"
        self.old = (
            promotion.SOURCE_QUADLET,
            promotion.INSTALLED_QUADLET,
            promotion.AUTOMATION_CONFIG,
            promotion.PROMOTION_ROOT,
        )
        promotion.SOURCE_QUADLET = self.source
        promotion.INSTALLED_QUADLET = self.installed
        promotion.AUTOMATION_CONFIG = self.config
        promotion.PROMOTION_ROOT = self.promotion_root

    def tearDown(self) -> None:
        (
            promotion.SOURCE_QUADLET,
            promotion.INSTALLED_QUADLET,
            promotion.AUTOMATION_CONFIG,
            promotion.PROMOTION_ROOT,
        ) = self.old
        sys.modules.pop("agent_automation_release", None)
        self.tmp.cleanup()

    def write_case(
        self,
        *,
        control=IMAGE_A,
        candidate=IMAGE_A,
        standing="PASS_CONTROL_REPRODUCIBLE",
        source_tz="Asia/Shanghai",
        installed_tz="Asia/Shanghai",
    ) -> None:
        self.source.write_bytes(quadlet(candidate, tz=source_tz))
        self.installed.write_bytes(quadlet(control, tz=installed_tz))
        self.config.write_text(
            json.dumps(
                {
                    "browserNetworkAuthority": {
                        "generationDigest": NETWORK,
                        "serviceUnit": "network-v2-browserless.target",
                    }
                }
            )
        )
        self.receipt.write_text(json.dumps(canary(control, candidate, standing)))
        self.request.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "ordivon.browserless-image-promotion-request-r1",
                    "candidateImage": candidate,
                    "canaryReceipt": str(self.receipt),
                    "canaryReceiptSha256": digest(self.receipt),
                    "expectedInstalledQuadletSha256": digest(self.installed),
                    "expectedSourceQuadletSha256": digest(self.source),
                    "expectedNetworkGenerationDigest": NETWORK,
                    "expectedHarnessCommit": COMMIT,
                }
            )
        )

    @contextlib.contextmanager
    def plan_dependencies(self, running_image=IMAGE_A):
        with (
            mock.patch.object(promotion, "_source_revision", return_value=COMMIT),
            mock.patch.object(promotion, "_require_canonical_commit") as canonical,
            mock.patch.object(
                promotion,
                "_production_carrier_images",
                return_value={11: running_image, 12: running_image, 13: running_image},
            ),
            mock.patch.object(
                promotion,
                "_render_source_quadlet",
                side_effect=lambda: (
                    self.source.read_bytes(),
                    {
                        "generationDigest": NETWORK,
                        "serviceUnit": "network-v2-browserless.target",
                        "namespace": "nv2-browserless-prod",
                    },
                ),
            ),
            mock.patch.object(promotion, "_require_local_image") as local,
        ):
            yield canonical, local

    def test_plan_same_image_is_read_only_noop(self) -> None:
        self.write_case()
        with self.plan_dependencies() as (canonical, local):
            value = promotion.build_plan(self.request)
        self.assertEqual(value["standing"], "NOOP_ALREADY_CURRENT")
        self.assertEqual(value["harnessCommit"], COMMIT)
        self.assertEqual(
            value["runningCarrierImages"], {"11": IMAGE_A, "12": IMAGE_A, "13": IMAGE_A}
        )
        self.assertFalse(value["productionMutationAttempted"])
        canonical.assert_called_once_with(COMMIT)
        local.assert_called_once_with(IMAGE_A)

    def test_plan_different_candidate_requires_expected_canary_standing(self) -> None:
        self.write_case(candidate=IMAGE_B, standing="PASS_EXPECTED_INFRASTRUCTURE_CHANGE")
        with self.plan_dependencies():
            value = promotion.build_plan(self.request)
        self.assertEqual(value["standing"], "READY_TO_APPLY")
        self.assertEqual(value["controlImage"], IMAGE_A)
        self.assertEqual(value["candidateImage"], IMAGE_B)

    def test_plan_rejects_stale_installed_quadlet_digest(self) -> None:
        self.write_case()
        value = json.loads(self.request.read_text())
        value["expectedInstalledQuadletSha256"] = "sha256:" + "0" * 64
        self.request.write_text(json.dumps(value))
        with self.plan_dependencies():
            with self.assertRaisesRegex(promotion.PromotionError, "installed Quadlet digest changed"):
                promotion.build_plan(self.request)

    def test_plan_rejects_canary_digest_drift(self) -> None:
        self.write_case()
        value = json.loads(self.request.read_text())
        value["canaryReceiptSha256"] = "sha256:" + "0" * 64
        self.request.write_text(json.dumps(value))
        with self.plan_dependencies():
            with self.assertRaisesRegex(promotion.PromotionError, "canary receipt digest mismatch"):
                promotion.build_plan(self.request)

    def test_plan_rejects_non_image_quadlet_drift(self) -> None:
        self.write_case(source_tz="UTC")
        with self.plan_dependencies():
            with self.assertRaisesRegex(promotion.PromotionError, "differ outside Image"):
                promotion.build_plan(self.request)

    def test_plan_rejects_running_carrier_control_drift(self) -> None:
        self.write_case()
        with self.plan_dependencies(running_image=IMAGE_B):
            with self.assertRaisesRegex(promotion.PromotionError, "running Browserless carriers"):
                promotion.build_plan(self.request)

    def test_post_change_policy_allows_only_shared_browser_control_identity_drift(self) -> None:
        ok = pool_receipt(infra=["browserBinary", "controlLayer"])
        self.assertEqual(promotion.validate_post_change_pool(ok)["standing"], "GLOBAL_DRIFT")
        for bad in (
            pool_receipt(families=["CF04"]),
            pool_receipt(infra=["networkAuthority"]),
            pool_receipt(local_infra={"chatgpt-carrier-12": ["browserBinary"]}),
            pool_receipt(local_families={"chatgpt-carrier-12": ["CF07"]}),
        ):
            with self.assertRaisesRegex(
                promotion.PromotionError, "exceeded allowed candidate drift"
            ):
                promotion.validate_post_change_pool(bad)

    def fake_release(
        self, *, was_closed=False, running=None, mcp_active=True, worker_active=True
    ):
        state = {"mcp": mcp_active, "worker": worker_active}
        calls = []
        restore = mock.Mock()
        admission = self.root / "admission.closed.json"
        if was_closed:
            admission.write_text("{}")

        @contextlib.contextmanager
        def fence(commit):
            calls.append(("fence", commit))
            yield was_closed

        def active(unit):
            if unit == "ordivon-agent-automation-mcp.service":
                return state["mcp"]
            if unit == "ordivon-agent-temporal-worker.service":
                return state["worker"]
            return False

        def run(args, **kwargs):
            calls.append(tuple(args))
            if args[:2] == ["/usr/bin/systemctl", "stop"]:
                state["mcp"] = False
            elif args[:2] == ["/usr/bin/systemctl", "start"]:
                state["mcp"] = True
            return mock.Mock(returncode=0, stdout="", stderr="")

        module = types.SimpleNamespace(
            MCP_UNIT="ordivon-agent-automation-mcp.service",
            WORKER_UNIT="ordivon-agent-temporal-worker.service",
            ADMISSION_CLOSED=admission,
            release_admission_fence=fence,
            active=active,
            run=run,
            running_workflows=mock.Mock(return_value=list(running or [])),
            _restore_admission_gate=restore,
        )
        return module, state, calls, restore

    def ready_plan(self):
        return {
            "schemaVersion": 1,
            "kind": "ordivon.browserless-image-promotion-plan-r1",
            "standing": "READY_TO_APPLY",
            "candidateImage": IMAGE_B,
            "controlImage": IMAGE_A,
            "harnessCommit": COMMIT,
            "runningCarrierImages": {"11": IMAGE_A, "12": IMAGE_A, "13": IMAGE_A},
            "sourceQuadletSha256": "sha256:" + "1" * 64,
            "renderedSourceQuadletSha256": "sha256:"
            + hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "installedQuadletSha256": "sha256:" + "2" * 64,
            "networkGenerationDigest": NETWORK,
            "networkAuthorityService": "network-v2-browserless.target",
            "canaryReceiptSha256": "sha256:" + "3" * 64,
            "canaryStanding": "PASS_EXPECTED_INFRASTRUCTURE_CHANGE",
            "productionMutationAttempted": False,
            "providerChallengeVisited": False,
            "providerSendAttempted": False,
            "rootCauseEstablished": False,
        }

    def test_apply_hold_draining_keeps_admission_closed_and_does_not_mutate_quadlet(self) -> None:
        self.installed.write_bytes(quadlet(IMAGE_A))
        self.source.write_bytes(quadlet(IMAGE_B))
        before = self.installed.read_bytes()
        fake, state, calls, restore = self.fake_release(running=[{"workflowId": "wf"}])
        sys.modules["agent_automation_release"] = fake
        with (
            mock.patch.object(promotion, "build_plan", return_value=self.ready_plan()),
            mock.patch.object(
                promotion,
                "_render_source_quadlet",
                return_value=(
                    self.source.read_bytes(),
                    {
                        "generationDigest": NETWORK,
                        "serviceUnit": "network-v2-browserless.target",
                    },
                ),
            ),
            mock.patch.object(promotion, "_persist_receipt") as persist,
        ):
            value = promotion.apply(self.request)
        self.assertEqual(value["standing"], "HOLD_DRAINING")
        self.assertEqual(self.installed.read_bytes(), before)
        self.assertFalse(state["mcp"])
        self.assertTrue(
            any(
                call[:2] == ("/usr/bin/systemctl", "stop")
                for call in calls
                if isinstance(call, tuple)
            )
        )
        restore.assert_not_called()
        persist.assert_called_once()

    def test_apply_failure_after_mutation_restores_quadlet_mcp_and_new_gate(self) -> None:
        self.installed.write_bytes(quadlet(IMAGE_A))
        self.source.write_bytes(quadlet(IMAGE_B))
        before = self.installed.read_bytes()
        fake, state, calls, restore = self.fake_release()
        sys.modules["agent_automation_release"] = fake
        with (
            mock.patch.object(promotion, "build_plan", return_value=self.ready_plan()),
            mock.patch.object(promotion, "_require_browser_quiescent"),
            mock.patch.object(
                promotion,
                "_production_carrier_images",
                return_value={11: IMAGE_A, 12: IMAGE_A, 13: IMAGE_A},
            ),
            mock.patch.object(
                promotion,
                "_render_source_quadlet",
                return_value=(
                    self.source.read_bytes(),
                    {
                        "generationDigest": NETWORK,
                        "serviceUnit": "network-v2-browserless.target",
                    },
                ),
            ),
            mock.patch.object(promotion, "_wait_carrier"),
            mock.patch.object(
                promotion,
                "_post_change_pool_check",
                side_effect=promotion.PromotionError("bad post witness"),
            ),
            mock.patch.object(promotion, "_persist_receipt"),
            mock.patch.object(promotion.subprocess, "run", return_value=mock.Mock(returncode=0)),
        ):
            with self.assertRaisesRegex(promotion.PromotionError, "bad post witness"):
                promotion.apply(self.request)
        self.assertEqual(self.installed.read_bytes(), before)
        self.assertTrue(state["mcp"])
        restore.assert_called_once_with(False)
        restart_calls = [call for call in calls if isinstance(call, tuple) and "start" in call]
        self.assertTrue(restart_calls)

    def test_apply_success_keeps_admission_closed_for_security_lkg_reseal(self) -> None:
        self.installed.write_bytes(quadlet(IMAGE_A))
        self.source.write_bytes(quadlet(IMAGE_B))
        fake, state, calls, restore = self.fake_release()
        sys.modules["agent_automation_release"] = fake
        post = pool_receipt(infra=["browserBinary", "controlLayer"])
        post_path = self.root / "post-pool-receipt.json"
        post_path.write_text(json.dumps(post))
        with (
            mock.patch.object(promotion, "build_plan", return_value=self.ready_plan()),
            mock.patch.object(promotion, "_require_browser_quiescent"),
            mock.patch.object(
                promotion,
                "_production_carrier_images",
                return_value={11: IMAGE_A, 12: IMAGE_A, 13: IMAGE_A},
            ),
            mock.patch.object(
                promotion,
                "_render_source_quadlet",
                return_value=(
                    self.source.read_bytes(),
                    {
                        "generationDigest": NETWORK,
                        "serviceUnit": "network-v2-browserless.target",
                    },
                ),
            ),
            mock.patch.object(promotion, "_wait_carrier"),
            mock.patch.object(
                promotion, "_post_change_pool_check", return_value=(post, post_path)
            ),
            mock.patch.object(promotion, "_persist_receipt") as persist,
            mock.patch.object(promotion.subprocess, "run", return_value=mock.Mock(returncode=0)),
        ):
            value = promotion.apply(self.request)
        self.assertEqual(value["standing"], "APPLIED_LKG_RESEAL_REQUIRED")
        self.assertTrue(value["lkgResealRequired"])
        self.assertTrue(value["mcpAdmissionClosed"])
        self.assertFalse(state["mcp"])
        restore.assert_not_called()
        persist.assert_called_once()
        self.assertEqual(self.installed.read_bytes(), self.source.read_bytes())

    def seed_applied_receipt(self) -> dict:
        value = self.ready_plan()
        value.update(
            {
                "kind": "ordivon.browserless-image-promotion-receipt-r1",
                "standing": "APPLIED_LKG_RESEAL_REQUIRED",
                "productionMutationAttempted": True,
                "lkgResealRequired": True,
                "preResealSecurityRevision": "0" * 40,
                "preResealPoolIndexSha256": "sha256:" + "e" * 64,
                "mcpAdmissionClosed": True,
                "cliAdmissionClosed": True,
            }
        )
        promotion._persist_receipt(IMAGE_B, value)
        return value

    def test_finalize_requires_new_security_revision_and_no_observed_drift(self) -> None:
        self.write_case(candidate=IMAGE_B, standing="PASS_EXPECTED_INFRASTRUCTURE_CHANGE")
        self.installed.write_bytes(self.source.read_bytes())
        self.seed_applied_receipt()
        fake, state, calls, restore = self.fake_release(was_closed=True, mcp_active=False)
        sys.modules["agent_automation_release"] = fake
        final_pool = pool_receipt()
        final_pool["securityRevision"] = "2" * 40
        final_pool["poolIndexSha256"] = "sha256:" + "f" * 64
        final_path = self.root / "final-pool-receipt.json"
        final_path.write_text(json.dumps(final_pool))
        with (
            mock.patch.object(promotion, "_source_revision", return_value=COMMIT),
            mock.patch.object(promotion, "_require_canonical_commit"),
            mock.patch.object(
                promotion,
                "_render_source_quadlet",
                return_value=(
                    self.source.read_bytes(),
                    {
                        "generationDigest": NETWORK,
                        "serviceUnit": "network-v2-browserless.target",
                    },
                ),
            ),
            mock.patch.object(
                promotion,
                "_production_carrier_images",
                return_value={11: IMAGE_B, 12: IMAGE_B, 13: IMAGE_B},
            ),
            mock.patch.object(promotion, "_security_clean_revision", return_value="2" * 40),
            mock.patch.object(promotion, "_require_browser_quiescent"),
            mock.patch.object(
                promotion, "_run_pool_observation", return_value=(final_pool, final_path)
            ),
        ):
            value = promotion.finalize(self.request)
        self.assertEqual(value["standing"], "ACTIVE")
        self.assertFalse(value["lkgResealRequired"])
        self.assertEqual(value["finalSecurityRevision"], "2" * 40)
        self.assertEqual(value["finalPoolIndexSha256"], "sha256:" + "f" * 64)
        self.assertTrue(state["mcp"])
        self.assertFalse(fake.ADMISSION_CLOSED.exists())
        restore.assert_not_called()
        self.assertTrue(any(call[:2] == ("/usr/bin/systemctl", "start") for call in calls if isinstance(call, tuple)))

    def test_finalize_drift_preserves_closed_gate_and_stopped_mcp(self) -> None:
        self.write_case(candidate=IMAGE_B, standing="PASS_EXPECTED_INFRASTRUCTURE_CHANGE")
        self.installed.write_bytes(self.source.read_bytes())
        self.seed_applied_receipt()
        fake, state, _calls, _restore = self.fake_release(was_closed=True, mcp_active=False)
        sys.modules["agent_automation_release"] = fake
        bad = pool_receipt(families=["CF04"])
        bad["securityRevision"] = "2" * 40
        bad["poolIndexSha256"] = "sha256:" + "f" * 64
        final_path = self.root / "bad-final-pool-receipt.json"
        final_path.write_text(json.dumps(bad))
        with (
            mock.patch.object(promotion, "_source_revision", return_value=COMMIT),
            mock.patch.object(promotion, "_require_canonical_commit"),
            mock.patch.object(
                promotion,
                "_render_source_quadlet",
                return_value=(
                    self.source.read_bytes(),
                    {
                        "generationDigest": NETWORK,
                        "serviceUnit": "network-v2-browserless.target",
                    },
                ),
            ),
            mock.patch.object(
                promotion,
                "_production_carrier_images",
                return_value={11: IMAGE_B, 12: IMAGE_B, 13: IMAGE_B},
            ),
            mock.patch.object(promotion, "_security_clean_revision", return_value="2" * 40),
            mock.patch.object(promotion, "_require_browser_quiescent"),
            mock.patch.object(
                promotion, "_run_pool_observation", return_value=(bad, final_path)
            ),
        ):
            with self.assertRaisesRegex(promotion.PromotionError, "NO_OBSERVED_DRIFT"):
                promotion.finalize(self.request)
        self.assertFalse(state["mcp"])
        self.assertTrue(fake.ADMISSION_CLOSED.exists())

    def test_finalize_rejects_unadvanced_security_revision_before_reopening(self) -> None:
        value = pool_receipt()
        value["securityRevision"] = "0" * 40
        value["poolIndexSha256"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(promotion.PromotionError, "did not advance"):
            promotion.validate_finalize_pool(
                value,
                harness_commit=COMMIT,
                security_revision="0" * 40,
                previous_security_revision="0" * 40,
                previous_pool_index_sha256="sha256:" + "e" * 64,
            )

    def test_atomic_write_replaces_exact_file(self) -> None:
        path = self.root / "atomic"
        path.write_bytes(b"before")
        promotion._atomic_write(path, b"after")
        self.assertEqual(path.read_bytes(), b"after")
        self.assertFalse(path.with_name(path.name + ".promotion-tmp").exists())


if __name__ == "__main__":
    unittest.main()
