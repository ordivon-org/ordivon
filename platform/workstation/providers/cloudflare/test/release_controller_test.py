from __future__ import annotations

import argparse
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts" / "ordivon_edge_release.py"
SPEC = importlib.util.spec_from_file_location("ordivon_edge_release", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load release controller")
release_controller = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release_controller
SPEC.loader.exec_module(release_controller)


class ReleaseControllerTests(unittest.TestCase):
    def test_installed_release_controller_resolves_world_monorepo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            provider = repository / "providers" / "cloudflare"
            provider.mkdir(parents=True)
            (provider / "wrangler.jsonc").write_text("{}\n")
            resolved = release_controller.resolve_provider_root(
                pathlib.Path("/usr/local/sbin/ordivon-edge-release"),
                repository,
            )
            self.assertEqual(resolved, provider.resolve())

    def test_source_release_controller_prefers_adjacent_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = pathlib.Path(directory) / "provider"
            script = provider / "scripts" / "ordivon_edge_release.py"
            script.parent.mkdir(parents=True)
            (provider / "wrangler.jsonc").write_text("{}\n")
            resolved = release_controller.resolve_provider_root(
                script,
                pathlib.Path("/does/not/exist"),
            )
            self.assertEqual(resolved, provider.resolve())

    def test_deployment_specifications_are_bounded_and_normalized(self) -> None:
        parsed = release_controller.parse_deployment_specifications(
            ["old@99.5", "new@0.5"]
        )
        self.assertEqual(
            parsed,
            [
                {"version_id": "old", "percentage": 99.5},
                {"version_id": "new", "percentage": 0.5},
            ],
        )
        with self.assertRaises(release_controller.ReleaseError):
            release_controller.parse_deployment_specifications(["new@99"] )

    def test_nonzero_deployment_uses_cloudflare_api_without_wrangler(self) -> None:
        expected = [{"version_id": "candidate", "percentage": 100}]
        deployment = {"id": "deployment", "versions": expected}
        with (
            mock.patch.object(
                release_controller,
                "create_deployment_api",
                return_value=deployment,
            ) as create,
            mock.patch.object(release_controller.subprocess, "Popen") as popen,
        ):
            result = release_controller.deploy_versions(
                {},
                ["candidate@100"],
                "promote",
            )
        self.assertEqual(result, deployment)
        create.assert_called_once_with(expected, "promote", force=False)
        popen.assert_not_called()

    def test_deploy_timeout_is_reconciled_from_cloudflare_api(self) -> None:
        class Process:
            pid = 1234
            returncode = None

            def communicate(self, timeout=None):
                if timeout is not None:
                    raise subprocess.TimeoutExpired(
                        cmd=["wrangler"],
                        timeout=timeout,
                        output="SUCCESS deployed",
                    )
                self.returncode = -9
                return ("", None)

        expected = [
            {"version_id": "old", "percentage": 100},
            {"version_id": "new", "percentage": 0},
        ]
        deployment = {"id": "deployment", "versions": expected}
        with (
            mock.patch.object(release_controller.subprocess, "Popen", return_value=Process()),
            mock.patch.object(release_controller.os, "killpg") as killpg,
            mock.patch.object(
                release_controller,
                "wait_for_deployment",
                return_value=deployment,
            ) as reconcile,
        ):
            result = release_controller.deploy_versions(
                {},
                ["old@100", "new@0"],
                "smoke",
                command_timeout_seconds=1,
            )
        self.assertEqual(result, deployment)
        killpg.assert_called_once_with(1234, release_controller.signal.SIGKILL)
        reconcile.assert_called_once_with(expected)

    def test_expected_policy_matches_local_configuration(self) -> None:
        version, retention = release_controller.expected_policy()
        self.assertRegex(version, r"^p1\.6\.[a-f0-9]{16}$")
        self.assertGreater(retention["artifacts"], retention["idempotency"])

    def test_worker_release_digest_supports_monorepo_provider_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            provider = repository / "providers" / "cloudflare"
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.name", "Test"],
                check=True,
            )
            for relative in release_controller.WORKER_RELEASE_INPUTS:
                target = provider / relative
                if relative == "src":
                    target.mkdir(parents=True, exist_ok=True)
                    (target / "index.ts").write_text("worker\n")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(relative + "\n")
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-qm", "worker"], check=True)
            commit = subprocess.check_output(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            with mock.patch.object(release_controller, "ROOT", provider):
                digest = release_controller.worker_release_digest(commit)
            self.assertEqual(len(digest), 64)

    def test_worker_version_tag_binds_source_and_release_inputs(self) -> None:
        commit = "a" * 40
        digest = "b" * 64
        tag = release_controller.worker_version_tag(commit, digest, 1234567890)
        self.assertEqual(
            tag,
            "git-aaaaaaaaaaaa-src-bbbbbbbbbbbbbbbb-1234567890",
        )
        self.assertEqual(
            release_controller.parse_worker_version_tag(tag),
            ("aaaaaaaaaaaa", "bbbbbbbbbbbbbbbb"),
        )
        self.assertEqual(
            release_controller.parse_worker_version_tag(
                "git-aaaaaaaaaaaa-1234567890"
            ),
            ("aaaaaaaaaaaa", None),
        )

    def test_resumable_current_tag_rejects_release_input_drift(self) -> None:
        versions = [
            {
                "id": "candidate",
                "annotations": {
                    "workers/tag": (
                        "git-abcdef123456-src-1111111111111111-1234567890"
                    )
                },
            }
        ]
        with (
            mock.patch.object(
                release_controller,
                "worker_release_digest",
                return_value="2" * 64,
            ),
            self.assertRaises(release_controller.ReleaseError),
        ):
            release_controller.resumable_candidate(
                versions,
                "candidate",
                "abcdef1234567890abcdef1234567890abcdef12",
            )

    def test_resumable_candidate_must_match_current_commit(self) -> None:
        versions = [
            {
                "id": "candidate",
                "annotations": {
                    "workers/tag": "git-abcdef123456-1234567890"
                },
            }
        ]
        candidate = release_controller.resumable_candidate(
            versions,
            "candidate",
            "abcdef1234567890abcdef1234567890abcdef12",
        )
        self.assertEqual(candidate["id"], "candidate")
        with self.assertRaises(release_controller.ReleaseError):
            release_controller.resumable_candidate(
                versions,
                "candidate",
                "0000000000000000000000000000000000000000",
                source_equivalent=lambda *_: False,
            )

    def test_resumable_candidate_accepts_equivalent_worker_inputs(self) -> None:
        versions = [
            {
                "id": "candidate",
                "annotations": {
                    "workers/tag": "git-abcdef123456-1234567890"
                },
            }
        ]
        comparisons: list[tuple[str, str]] = []

        def equivalent(candidate_ref: str, current_commit: str) -> bool:
            comparisons.append((candidate_ref, current_commit))
            return True

        candidate = release_controller.resumable_candidate(
            versions,
            "candidate",
            "0000000000000000000000000000000000000000",
            source_equivalent=equivalent,
        )
        self.assertEqual(candidate["id"], "candidate")
        self.assertEqual(
            comparisons,
            [("abcdef123456", "0" * 40)],
        )

    def test_deployments_are_sorted_by_created_time(self) -> None:
        payload = [
            {"id": "new", "created_on": "2026-07-27T02:00:00Z"},
            {"id": "old", "created_on": "2026-07-27T01:00:00Z"},
        ]
        with (
            mock.patch.object(
                release_controller,
                "load_cloudflare_credentials",
                return_value=release_controller.CloudflareCredentials(
                    api_token="test-token",
                    account_id="test-account",
                ),
            ),
            mock.patch.object(
                release_controller,
                "cloudflare_api",
                return_value={"deployments": payload},
            ),
        ):
            result = release_controller.deployments({})
        self.assertEqual([item["id"] for item in result], ["old", "new"])

    def test_upload_failure_writes_failure_receipt(self) -> None:
        reports: list[tuple[str, dict[str, object]]] = []

        def capture_receipt(prefix: str, report: dict[str, object]) -> pathlib.Path:
            reports.append((prefix, dict(report)))
            return pathlib.Path("/tmp/release-failed.json")

        args = argparse.Namespace(message="test upload failure")
        edge_config = release_controller.EdgeConfig(
            endpoint="https://edge.invalid",
            key_id="runtime-v1",
            secret=b"x" * 32,
        )
        versions_payload = [
            {
                "id": "old-version",
                "number": 1,
                "metadata": {"created_on": "2026-07-27T00:00:00Z"},
                "annotations": {
                    "workers/tag": "git-111111111111-src-2222222222222222-1"
                },
            }
        ]
        deployment_payload = [
            {
                "id": "deployment-old",
                "created_on": "2026-07-27T00:00:00Z",
                "versions": [
                    {"version_id": "old-version", "percentage": 100}
                ],
            }
        ]

        with (
            mock.patch.object(release_controller, "cloudflare_environment", return_value={}),
            mock.patch.object(release_controller, "load_edge_config", return_value=edge_config),
            mock.patch.object(
                release_controller,
                "verify_release_source",
                return_value="a" * 40,
            ),
            mock.patch.object(
                release_controller,
                "worker_release_digest",
                return_value="b" * 64,
            ),
            mock.patch.object(release_controller, "run"),
            mock.patch.object(
                release_controller,
                "versions",
                return_value=versions_payload,
            ),
            mock.patch.object(
                release_controller,
                "deployments",
                return_value=deployment_payload,
            ),
            mock.patch.object(
                release_controller,
                "smoke_operations_for_change",
                return_value={"fetch", "browser.run"},
            ),
            mock.patch.object(
                release_controller,
                "wrangler",
                side_effect=release_controller.ReleaseError("upload rejected"),
            ),
            mock.patch.object(
                release_controller,
                "write_receipt",
                side_effect=capture_receipt,
            ),
        ):
            with self.assertRaises(release_controller.ReleaseError) as raised:
                release_controller.release(args)

        self.assertIn("/tmp/release-failed.json", str(raised.exception))
        self.assertEqual(len(reports), 1)
        prefix, report = reports[0]
        self.assertEqual(prefix, "release-failed")
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["failed_stage"], "upload_pending")
        self.assertEqual(report["previous_version"], "old-version")
        self.assertIsNone(report["candidate_version"])
        self.assertNotIn("restored_previous_version", report)


    def test_release_source_ignores_unrelated_dirty_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            provider = repository / "providers" / "cloudflare"
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.name", "Test"], check=True)
            for relative in release_controller.WORKER_RELEASE_INPUTS:
                target = provider / relative
                if relative == "src":
                    target.mkdir(parents=True)
                    (target / "index.ts").write_text("worker\n")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(relative + "\n")
            (repository / "README.md").write_text("one\n")
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-qm", "base"], check=True)
            commit = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
            (repository / "README.md").write_text("unrelated dirty\n")
            with mock.patch.object(release_controller, "ROOT", provider):
                self.assertEqual(release_controller.verify_release_source(), commit)
                (provider / "src" / "index.ts").write_text("dirty worker\n")
                with self.assertRaises(release_controller.ReleaseError):
                    release_controller.verify_release_source()

    def test_change_aware_smoke_selection(self) -> None:
        previous = {"id": "old", "annotations": {"workers/tag": "git-aaaaaaaaaaaa-src-bbbbbbbbbbbbbbbb-1"}}
        cases = [
            (["providers/cloudflare/src/external-fetch.ts"], {"fetch"}),
            (["providers/cloudflare/src/browser-run.ts"], {"browser.run"}),
            (["providers/cloudflare/src/index.ts"], {"fetch", "browser.run"}),
            (["providers/cloudflare/wrangler.jsonc"], {"fetch", "browser.run"}),
            (None, {"fetch", "browser.run"}),
        ]
        for changed, expected in cases:
            with mock.patch.object(release_controller, "changed_worker_inputs", return_value=changed):
                self.assertEqual(release_controller.smoke_operations_for_change(previous, "c" * 40), expected)

    def test_propagation_requires_three_consecutive_matches(self) -> None:
        responses = [
            (200, {"CF-Ray": "old-1"}, {"worker_version": {"id": "old"}}),
            (
                200,
                {"CF-Ray": "candidate-1"},
                {"worker_version": {"id": "candidate"}},
            ),
            (200, {"CF-Ray": "old-2"}, {"worker_version": {"id": "old"}}),
            (
                200,
                {"CF-Ray": "candidate-2"},
                {"worker_version": {"id": "candidate"}},
            ),
            (
                200,
                {"CF-Ray": "candidate-3"},
                {"worker_version": {"id": "candidate"}},
            ),
            (
                200,
                {"CF-Ray": "candidate-4"},
                {"worker_version": {"id": "candidate"}},
            ),
        ]
        with mock.patch.object(
            release_controller,
            "signed_request",
            side_effect=responses,
        ):
            result = release_controller.wait_for_version_propagation(
                release_controller.EdgeConfig(
                    endpoint="https://edge.invalid",
                    key_id="runtime-v1",
                    secret=b"x" * 32,
                ),
                "candidate",
                use_override=True,
                sleep=lambda _: None,
                monotonic=lambda: 0.0,
            )
        self.assertEqual(result["attempts"], 6)
        self.assertEqual(result["consecutive_required"], 3)
        self.assertEqual(result["observations"][-1]["cf_ray"], "candidate-4")

    def test_versioned_read_retries_read_only_version_drift(self) -> None:
        responses = [
            (200, {"CF-Ray": "old"}, {"worker_version": {"id": "old"}}),
            (
                200,
                {"CF-Ray": "candidate"},
                {"worker_version": {"id": "candidate"}, "ok": True},
            ),
        ]
        with mock.patch.object(
            release_controller,
            "signed_request",
            side_effect=responses,
        ):
            value, report = release_controller.read_versioned_document(
                release_controller.EdgeConfig(
                    endpoint="https://edge.invalid",
                    key_id="runtime-v1",
                    secret=b"x" * 32,
                ),
                "candidate",
                "/health",
                "health read",
                use_override=True,
                sleep=lambda _: None,
                monotonic=lambda: 0.0,
            )
        self.assertTrue(value["ok"])
        self.assertEqual(report["attempts"], 2)
        self.assertEqual(report["observations"][-1]["cf_ray"], "candidate")

    def test_smoke_post_is_guarded_and_never_accepts_wrong_version(self) -> None:
        guard = {
            "target_version": "candidate",
            "consecutive_required": 3,
            "attempts": 3,
        }
        response = (
            200,
            {"CF-Ray": "old"},
            {"worker_version": {"id": "old"}, "receipt": {"status": "succeeded"}},
        )
        with (
            mock.patch.object(
                release_controller,
                "wait_for_version_propagation",
                return_value=guard,
            ) as wait,
            mock.patch.object(
                release_controller,
                "signed_request",
                return_value=response,
            ) as request,
            self.assertRaises(release_controller.ReleaseError),
        ):
            release_controller.smoke_operation(
                release_controller.EdgeConfig(
                    endpoint="https://edge.invalid",
                    key_id="runtime-v1",
                    secret=b"x" * 32,
                ),
                "candidate",
                "/v1/fetch",
                b"{}",
                "req_test",
            )
        wait.assert_called_once()
        request.assert_called_once()

    def test_release_no_change_skips_ci_and_upload(self) -> None:
        commit = "a" * 40
        digest = "b" * 64
        active = "active-version"
        version_payload = [{"id": active, "annotations": {"workers/tag": f"git-{commit[:12]}-src-{digest[:16]}-1"}}]
        deployment_payload = [{"created_on": "2026-08-02T00:00:00Z", "versions": [{"version_id": active, "percentage": 100}]}]
        output = io.StringIO()
        with (
            mock.patch.object(release_controller, "cloudflare_environment", return_value={}),
            mock.patch.object(release_controller, "load_edge_config", return_value=release_controller.EdgeConfig(endpoint="https://edge.invalid", key_id="runtime-v1", secret=b"x" * 32)),
            mock.patch.object(release_controller, "verify_release_source", return_value=commit),
            mock.patch.object(release_controller, "worker_release_digest", return_value=digest),
            mock.patch.object(release_controller, "expected_policy", return_value=("p1.6.test", {"artifacts": 91})),
            mock.patch.object(release_controller, "versions", return_value=version_payload),
            mock.patch.object(release_controller, "deployments", return_value=deployment_payload),
            mock.patch.object(release_controller, "run") as run,
            mock.patch.object(release_controller, "wrangler") as wrangler,
            redirect_stdout(output),
        ):
            result = release_controller.release(argparse.Namespace(message=None))
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "no_change")
        run.assert_not_called()
        wrangler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
