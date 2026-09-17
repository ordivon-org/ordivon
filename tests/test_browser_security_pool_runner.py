import contextlib
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.browser_security_pool_runner as runner


class BrowserSecurityPoolRunnerTests(unittest.TestCase):
    def make_index(self, root: Path, carriers=("chatgpt-carrier-11", "chatgpt-carrier-12")) -> Path:
        fixtures = root / "fixtures/browser-security"
        fixtures.mkdir(parents=True)
        rows = []
        for carrier in carriers:
            bundle = fixtures / f"{carrier}-baseline.json"
            bundle.write_text(json.dumps({"carrier": carrier}) + "\n", encoding="utf-8")
            rows.append(
                {
                    "carrierId": carrier,
                    "bundle": str(bundle.relative_to(root)),
                    "bundleSha256": "sha256:" + hashlib.sha256(bundle.read_bytes()).hexdigest(),
                }
            )
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.browser-security-pool-lkg-index",
            "poolId": "test-pool",
            "standing": "LKG_PER_CARRIER",
            "comparisonLaw": {"sameCarrierCandidateVsSameCarrierLkg": "ALLOWED"},
            "carriers": rows,
        }
        path = fixtures / "pool-index.json"
        path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return path

    def test_pool_index_digest_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = self.make_index(root)
            value = json.loads(index.read_text())
            value["carriers"][0]["bundleSha256"] = "sha256:" + "0" * 64
            index.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                runner._load_pool_index(index, root)

    def test_pool_index_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "security"
            root.mkdir()
            index = self.make_index(root)
            outside = Path(tmp) / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            value = json.loads(index.read_text())
            value["carriers"][0]["bundle"] = str(outside)
            value["carriers"][0]["bundleSha256"] = runner._sha256(outside)
            index.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes configured root"):
                runner._load_pool_index(index, root)

    def test_run_pool_delegates_collection_and_security_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            security = tmp_root / "security"
            security.mkdir()
            index = self.make_index(security)
            artifacts = tmp_root / "artifacts"

            def collect(*, carrier_id, witness_id, output, python, config_path):
                output.write_text(
                    json.dumps(
                        {
                            "carrierId": carrier_id,
                            "witnessId": witness_id,
                            "configPath": str(config_path),
                        }
                    ),
                    encoding="utf-8",
                )

            def build(*, manifest, output, security_root, python):
                output.write_text(json.dumps({"source": manifest.name}), encoding="utf-8")

            classification = {
                "schemaVersion": 1,
                "standing": "NO_OBSERVED_DRIFT",
                "rootCauseEstablished": False,
            }

            @contextlib.contextmanager
            def lifecycle(config_path, carrier_id):
                yield {
                    "carrierId": carrier_id,
                    "serviceUnit": f"{carrier_id}.service",
                    "initiallyActive": False,
                    "lifecycleStarted": True,
                    "restoredOriginalActiveState": True,
                }

            config_path = tmp_root / "automation.json"
            config_path.write_text("{}\n")
            with mock.patch.object(
                runner, "_carrier_observation_lifecycle", side_effect=lifecycle
            ) as lifecycle_mock, mock.patch.object(
                runner, "_collect_carrier", side_effect=collect
            ) as collect_mock, mock.patch.object(
                runner, "_build_bundle", side_effect=build
            ) as build_mock, mock.patch.object(
                runner, "_compare_pool", return_value=classification
            ) as compare_mock, mock.patch.object(
                runner, "_source_revision", side_effect=["harness-head", "security-head"]
            ):
                receipt = runner.run_pool(
                    run_id="test-run",
                    security_root=security,
                    pool_index=index,
                    python="/usr/bin/python",
                    artifact_dir=artifacts,
                    config_path=config_path,
                )

            self.assertEqual(receipt["classification"], classification)
            self.assertEqual(receipt["harnessRevision"], "harness-head")
            self.assertEqual(receipt["securityRevision"], "security-head")
            self.assertFalse(receipt["providerChallengeVisited"])
            self.assertFalse(receipt["providerSendAttempted"])
            self.assertEqual(collect_mock.call_count, 2)
            self.assertEqual(lifecycle_mock.call_count, 2)
            self.assertEqual(build_mock.call_count, 2)
            self.assertEqual(
                [row["carrierId"] for row in receipt["carrierLifecycleEvidence"]],
                ["chatgpt-carrier-11", "chatgpt-carrier-12"],
            )
            self.assertTrue(
                all(
                    row["restoredOriginalActiveState"]
                    for row in receipt["carrierLifecycleEvidence"]
                )
            )
            compare_mock.assert_called_once()
            run_root = artifacts / "test-run"
            self.assertTrue((run_root / "pool-comparison-manifest.json").is_file())
            self.assertTrue((run_root / "pool-run-receipt.json").is_file())
            comparison = json.loads((run_root / "pool-comparison-manifest.json").read_text())
            for row in comparison["carriers"]:
                self.assertIn(row["carrierId"], row["baselineBundle"])
                self.assertIn(row["carrierId"], row["candidateBundle"])

    def test_observation_lifecycle_keeps_already_active_carrier_active(self) -> None:
        endpoint = mock.Mock(
            endpoint_id="chatgpt-carrier-11",
            service_unit="ordivon-browserless@11.service",
        )
        config = mock.Mock(browserless_pool=mock.Mock(endpoints=[endpoint]))
        service = mock.Mock()
        service.ensure_endpoint_active.return_value = {
            "healthy": True,
            "lifecycleStarted": False,
        }
        active = mock.Mock(returncode=0)
        with mock.patch.object(runner, "_load_automation_config", return_value=config), mock.patch(
            "scripts.agent_automation_browserless.BrowserlessAutomationService",
            return_value=service,
        ), mock.patch.object(runner.subprocess, "run", return_value=active) as run:
            with runner._carrier_observation_lifecycle(
                Path("/etc/fixture.json"), "chatgpt-carrier-11"
            ) as state:
                self.assertTrue(state["initiallyActive"])
                self.assertFalse(state["lifecycleStarted"])
        self.assertTrue(state["restoredOriginalActiveState"])
        self.assertFalse(
            any(
                call.args[0][1:3] == ["stop", "ordivon-browserless@11.service"]
                for call in run.call_args_list
            )
        )

    def test_observation_lifecycle_wakes_and_restores_sleeping_carrier(self) -> None:
        endpoint = mock.Mock(
            endpoint_id="chatgpt-carrier-12",
            service_unit="ordivon-browserless@12.service",
        )
        endpoint.sessions.return_value = []
        config = mock.Mock(browserless_pool=mock.Mock(endpoints=[endpoint]))
        service = mock.Mock()
        service.ensure_endpoint_active.return_value = {
            "healthy": True,
            "lifecycleStarted": True,
        }

        @contextlib.contextmanager
        def lease(*args, **kwargs):
            yield

        calls = [
            mock.Mock(returncode=3),  # initially inactive
            mock.Mock(returncode=0),  # stop succeeds
            mock.Mock(returncode=3),  # remains inactive after stop
        ]
        with mock.patch.object(runner, "_load_automation_config", return_value=config), mock.patch(
            "scripts.agent_automation_browserless.BrowserlessAutomationService",
            return_value=service,
        ), mock.patch(
            "scripts.agent_automation_browserless._carrier_lease", side_effect=lease
        ), mock.patch.object(runner.subprocess, "run", side_effect=calls) as run:
            with runner._carrier_observation_lifecycle(
                Path("/etc/fixture.json"), "chatgpt-carrier-12"
            ) as state:
                self.assertFalse(state["initiallyActive"])
                self.assertTrue(state["lifecycleStarted"])
        self.assertTrue(state["restoredOriginalActiveState"])
        self.assertIn(
            ["/usr/bin/systemctl", "stop", "ordivon-browserless@12.service"],
            [call.args[0] for call in run.call_args_list],
        )

    def test_observation_lifecycle_never_stops_carrier_that_became_busy(self) -> None:
        endpoint = mock.Mock(
            endpoint_id="chatgpt-carrier-13",
            service_unit="ordivon-browserless@13.service",
        )
        endpoint.sessions.return_value = [{"id": "new-session"}]
        config = mock.Mock(browserless_pool=mock.Mock(endpoints=[endpoint]))
        service = mock.Mock()
        service.ensure_endpoint_active.return_value = {
            "healthy": True,
            "lifecycleStarted": True,
        }

        @contextlib.contextmanager
        def lease(*args, **kwargs):
            yield

        with mock.patch.object(runner, "_load_automation_config", return_value=config), mock.patch(
            "scripts.agent_automation_browserless.BrowserlessAutomationService",
            return_value=service,
        ), mock.patch(
            "scripts.agent_automation_browserless._carrier_lease", side_effect=lease
        ), mock.patch.object(
            runner.subprocess, "run", return_value=mock.Mock(returncode=3)
        ) as run:
            with self.assertRaisesRegex(RuntimeError, "acquired a session"):
                with runner._carrier_observation_lifecycle(
                    Path("/etc/fixture.json"), "chatgpt-carrier-13"
                ):
                    pass
        self.assertFalse(
            any(
                call.args[0][1:3] == ["stop", "ordivon-browserless@13.service"]
                for call in run.call_args_list
            )
        )

    def test_source_revision_accepts_immutable_release_marker_without_git_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit = "a" * 40
            (root / ".ordivon-agent-automation-release.json").write_text(
                json.dumps({"schemaVersion": 1, "commit": commit, "archiveDigest": "sha256:x"}),
                encoding="utf-8",
            )
            with mock.patch.object(
                runner.subprocess,
                "run",
                return_value=mock.Mock(returncode=128, stdout="", stderr="not a git repo"),
            ):
                self.assertEqual(runner._source_revision(root), commit)

    def test_source_revision_rejects_invalid_release_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ordivon-agent-automation-release.json").write_text(
                json.dumps({"schemaVersion": 1, "commit": "short"}), encoding="utf-8"
            )
            with mock.patch.object(
                runner.subprocess,
                "run",
                return_value=mock.Mock(returncode=128, stdout="", stderr="not a git repo"),
            ):
                with self.assertRaisesRegex(RuntimeError, "marker is invalid"):
                    runner._source_revision(root)

    def test_invalid_run_id_is_rejected_before_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = self.make_index(root)
            with self.assertRaisesRegex(ValueError, "runId"):
                runner.run_pool(
                    run_id="bad/run",
                    security_root=root,
                    pool_index=index,
                    python="/usr/bin/python",
                    artifact_dir=None,
                )


if __name__ == "__main__":
    unittest.main()
