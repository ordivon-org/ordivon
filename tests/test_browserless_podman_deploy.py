from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class BrowserlessPodmanDeploymentTests(unittest.TestCase):
    def binding(self):
        return {
            "kind": "network-v2",
            "name": "browserless-prod",
            "namespace": "nv2-browserless-prod",
            "generationDigest": "sha256:" + "3" * 64,
            "serviceUnit": "network-v2-browserless.target",
            "receiptPath": "/receipt",
        }

    def _contract(self, path, receipt):
        path.write_text(
            '[agent_automation.browserless_network]\nkind="network-v2"\nname="browserless-prod"\nnamespace="nv2-browserless-prod"\nservice_unit="network-v2-browserless.target"\nreceipt="%s"\n'
            % receipt
        )

    def test_quadlet_consumes_network_v2_authority(self):
        text = (ROOT / "containers/ordivon-browserless@.container").read_text()
        self.assertIn("ghcr.io/browserless/chromium@sha256:b1ba7b054af2891a8199f884d4bd249cf8c3bd2fa8a97b339077e40f92803ba8", text)
        self.assertIn("Environment=TZ=Asia/Shanghai", text)
        self.assertIn("Network=ns:/run/netns/@NETWORK_NAMESPACE@", text)
        self.assertIn("BindsTo=@NETWORK_AUTHORITY_SERVICE@", text)
        self.assertNotIn("@SURFPATH_NAMESPACE@", text)
        self.assertNotIn("@EXTERIOR_ANCHOR_SERVICE@", text)
        self.assertIn("Secret=ordivon-browserless-token,type=env,target=TOKEN", text)
        self.assertIn("Volume=/var/lib/ordivon/browserless/%i:/data:U", text)
        self.assertIn("Environment=DISPLAY=:1%i", text)
        self.assertIn("Requires=ordivon-browserless-display@%i.service", text)
        self.assertIn("Pull=never", text)
        self.assertNotIn("docker", text.lower())

    def test_contract_declares_only_network_v2_browserless_authority(self):
        import tomllib

        contract = tomllib.loads((ROOT / "config/agent-automation.toml").read_text())
        cfg = contract["agent_automation"]["browserless_network"]
        self.assertEqual(cfg["kind"], "network-v2")
        self.assertEqual(cfg["name"], "browserless-prod")
        self.assertEqual(cfg["namespace"], "nv2-browserless-prod")
        self.assertEqual(cfg["service_unit"], "network-v2-browserless.target")
        self.assertEqual(
            cfg["receipt"], "/var/lib/network-v2/browserless-cutover/production-cutover.json"
        )
        self.assertNotIn("browserless_anchor_recovery", contract["agent_automation"])

    def test_network_v2_resolution_requires_graduated_receipt_namespace_and_service(self):
        import browserless_podman_deploy as deploy

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            netns = root / "netns"
            netns.mkdir()
            (netns / "nv2-browserless-prod").touch()
            receipt = root / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "standing": "PRODUCTION_CUTOVER_PASS",
                        "generationDigest": "sha256:" + "2" * 64,
                    }
                )
            )
            contract = root / "contract.toml"
            self._contract(contract, receipt)
            active = mock.Mock(returncode=0, stdout=b"active\n", stderr=b"")
            with mock.patch.object(deploy, "run", return_value=active):
                binding = deploy.resolve_network_binding(contract, netns_root=netns)
            self.assertEqual(binding["kind"], "network-v2")
            self.assertEqual(binding["namespace"], "nv2-browserless-prod")
            self.assertEqual(binding["generationDigest"], "sha256:" + "2" * 64)
            bad = json.loads(receipt.read_text())
            bad["standing"] = "HOLD"
            receipt.write_text(json.dumps(bad))
            with self.assertRaisesRegex(RuntimeError, "not graduated"):
                deploy.resolve_network_binding(contract, netns_root=netns, check_service=False)

    def test_network_v2_resolution_rejects_missing_namespace(self):
        import browserless_podman_deploy as deploy

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            netns = root / "netns"
            netns.mkdir()
            receipt = root / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "standing": "PRODUCTION_CUTOVER_PASS",
                        "generationDigest": "sha256:" + "2" * 64,
                    }
                )
            )
            contract = root / "contract.toml"
            self._contract(contract, receipt)
            with self.assertRaisesRegex(RuntimeError, "namespace is absent"):
                deploy.resolve_network_binding(contract, netns_root=netns, check_service=False)

    def test_rendered_config_and_units_bind_network_v2(self):
        import browserless_podman_deploy as deploy

        binding = self.binding()
        q = deploy.render_quadlet(binding)
        o = deploy.render_operator_proxy(binding)
        c = deploy.render_config(binding)
        self.assertIn("Network=ns:/run/netns/nv2-browserless-prod", q)
        self.assertIn("BindsTo=network-v2-browserless.target", q)
        self.assertIn("ip netns exec nv2-browserless-prod", o)
        self.assertIn("BindsTo=network-v2-browserless.target", o)
        self.assertEqual(
            c["browserNetworkAuthority"],
            {k: binding[k] for k in ("kind", "name", "generationDigest", "serviceUnit")},
        )
        self.assertTrue(
            all(
                x["networkNamespace"] == "nv2-browserless-prod"
                for x in c["browserSubstrate"]["endpoints"]
            )
        )
        b = deploy.render_browser_use_config(binding)
        self.assertEqual(
            [x["id"] for x in b["browserSubstrate"]["endpoints"]], ["browser-agent-22"]
        )
        self.assertTrue(
            all(
                x["networkNamespace"] == "nv2-browserless-prod"
                for x in b["browserSubstrate"]["endpoints"]
            )
        )
        self.assertTrue(
            set(x["id"] for x in c["browserSubstrate"]["endpoints"]).isdisjoint(
                x["id"] for x in b["browserSubstrate"]["endpoints"]
            )
        )

    def test_runtime_config_prefers_immutable_production_source_when_present(self):
        import browserless_podman_deploy as deploy

        with mock.patch.dict(
            deploy.os.environ,
            {
                "ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT": "/opt/ordivon/agent-automation/releases/exact"
            },
        ):
            value = deploy.render_config(self.binding())
        for key in (
            "browserlessSubmitScript",
            "browserlessReconcileScript",
            "browserlessTurnScript",
            "browserlessPreflightScript",
            "browserlessHumanResumeScript",
            "temporalLaunchScript",
        ):
            self.assertTrue(
                value[key].startswith("/opt/ordivon/agent-automation/releases/exact/"), key
            )

    def test_source_tree_has_no_legacy_browserless_network_recovery_owners(self):
        for rel in (
            "scripts/browserless_anchor_recover.py",
            "scripts/browserless_netns_reconcile.py",
            "systemd/ordivon-browserless-anchor-recover.path",
            "systemd/ordivon-browserless-anchor-recover.service",
            "systemd/ordivon-browserless-netns-reconcile.path",
            "systemd/ordivon-browserless-netns-reconcile.service",
            "systemd/ordivon-exterior-anchor-chatgpt-browserless-r1.service",
        ):
            self.assertFalse((ROOT / rel).exists(), rel)
        source = (ROOT / "scripts/browserless_podman_deploy.py").read_text()
        self.assertNotIn("chatgpt-browserless-r1", source)
        self.assertNotIn("browserless-anchor-recover", source)
        self.assertNotIn("browserless-netns-reconcile", source)

    def test_websockify_resolution_consumes_stable_v2_equipment_binding_carrier(self):
        import browserless_podman_deploy as deploy

        completed = __import__("subprocess").CompletedProcess(
            [],
            0,
            stdout=json.dumps(
                {
                    "state": "AVAILABLE",
                    "equipmentId": deploy.WEBSOCKIFY_EQUIPMENT_ID,
                    "executionTarget": "local_linux",
                    "executable": "/opt/ordivon/external/websockify/0.13.0/bin/websockify",
                    "executableDigest": "sha256:" + "1" * 64,
                    "bindingDigest": "sha256:" + "2" * 64,
                }
            ).encode(),
            stderr=b"",
        )
        with mock.patch.object(deploy, "run", return_value=completed) as run:
            binding = deploy.resolve_websockify_binding(Path("/root/tools/bin/equipment-binding"))
        run.assert_called_once_with(
            [
                "/root/tools/bin/equipment-binding",
                "managed",
                "--equipment-id",
                deploy.WEBSOCKIFY_EQUIPMENT_ID,
            ],
            check=False,
        )
        self.assertEqual(binding["equipmentId"], deploy.WEBSOCKIFY_EQUIPMENT_ID)

    def test_human_transport_materialization_consumes_managed_equipment_binding(self):
        import browserless_podman_deploy as deploy

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            nv = root / "novnc"
            ws = root / "websockify"
            nv.mkdir()
            (ws / "bin").mkdir(parents=True)
            (nv / ".ordivon-source-sha256").write_text(deploy.NOVNC_SOURCE_SHA256)
            (nv / "vnc.html").write_text("x")
            (ws / ".ordivon-source-sha256").write_text(deploy.WEBSOCKIFY_SOURCE_SHA256)
            launcher = ws / "bin/websockify"
            launcher.write_bytes(b"launcher")
            fake = {
                "state": "AVAILABLE",
                "equipmentId": deploy.WEBSOCKIFY_EQUIPMENT_ID,
                "executionTarget": "local_linux",
                "executable": str(launcher),
                "executableDigest": "sha256:" + "1" * 64,
                "bindingDigest": "sha256:" + "2" * 64,
            }
            with (
                mock.patch.object(deploy, "NOVNC_ROOT", nv),
                mock.patch.object(deploy, "WEBSOCKIFY_ROOT", ws),
            ):
                value = deploy.human_transport_materialization(fake)
            self.assertTrue(value["current"])
            self.assertEqual(value["websockifyExecutable"], str(launcher))

    def test_human_interaction_units_use_authenticated_loopback_mature_substrate(self):
        display = (ROOT / "systemd/ordivon-browserless-display@.service").read_text()
        vnc = (ROOT / "systemd/ordivon-browserless-human-vnc@.service").read_text()
        import browserless_podman_deploy as deploy

        self.assertIn("-nolisten tcp", display)
        self.assertNotIn("-ac", display)
        self.assertIn("-listen 127.0.0.1", vnc)
        rendered = deploy.render_human_web_unit(
            {"executable": "/managed/websockify", "executionTarget": "local_linux"}
        )
        self.assertIn("/managed/websockify", rendered)
        self.assertNotIn(deploy.WEBSOCKIFY_EXECUTABLE_TOKEN, rendered)
        self.assertIn("127.0.0.1:160%i", rendered)

    def test_systemd_mask_observation_preserves_operator_policy(self):
        import browserless_podman_deploy as deploy

        masked = subprocess.CompletedProcess([], 1, stdout=b"masked\n", stderr=b"")
        disabled = subprocess.CompletedProcess([], 1, stdout=b"disabled\n", stderr=b"")
        with mock.patch.object(deploy, "run", side_effect=[masked, disabled]):
            self.assertTrue(deploy.systemd_unit_is_masked("example@21.service"))
            self.assertFalse(deploy.systemd_unit_is_masked("example@22.service"))

    def test_general_browser_lane_is_cold_on_demand(self):
        import browserless_podman_deploy as deploy

        target = (ROOT / "systemd/ordivon-browser-agent.target").read_text()
        self.assertIn("Requires=ordivon-browserless@22.service", target)
        self.assertIn("Requires=ordivon-browserless-operator-proxy@22.service", target)
        self.assertNotIn("WantedBy=multi-user.target", target)

        source = (ROOT / "scripts/browserless_podman_deploy.py").read_text()
        self.assertIn("BROWSER_AGENT_TARGET_DEST", source)
        self.assertNotIn('enable", "--now", "ordivon-browser-agent.target"', source)
        self.assertIn('disable", "--now", "ordivon-browser-agent.target"', source)
        self.assertNotIn('enable", "--now", *[f"ordivon-browserless@{instance}.service"', source)
        self.assertIn('"serviceUnit": f"ordivon-browserless@{instance}.service"', source)
        self.assertIn('"activationUnit": "ordivon-browser-agent.target"', source)
        self.assertIn('"idleStopUnits": [', source)
        self.assertIn('"browserlessIdleTtlSeconds": 900', source)
        self.assertIn("WARM_CHATGPT_INSTANCES = (11,)", source)
        self.assertIn('ordivon-browserless-idle-reaper.timer', source)

        browser = deploy.render_browser_use_config(self.binding())
        endpoint = browser["browserSubstrate"]["endpoints"][0]
        self.assertEqual(endpoint["id"], "browser-agent-22")
        self.assertEqual(endpoint["activationUnit"], "ordivon-browser-agent.target")
        self.assertEqual(
            endpoint["idleStopUnits"],
            [
                "ordivon-browser-agent.target",
                "ordivon-browserless@22.service",
                "ordivon-browserless-operator-proxy@22.service",
            ],
        )

    def test_warm_chatgpt_instance_materializes_quadlet_template_instance(self):
        import browserless_podman_deploy as deploy

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            template = root / "ordivon-browserless@.container"
            template.write_text("[Container]\nImage=example\n")
            with mock.patch.object(deploy, "QUADLET_DEST", template):
                first = deploy.converge_warm_quadlet_instance(11)
                second = deploy.converge_warm_quadlet_instance(11)

            instance = root / "ordivon-browserless@11.container"
            self.assertTrue(first)
            self.assertFalse(second)
            self.assertTrue(instance.is_symlink())
            self.assertEqual(instance.readlink(), Path(template.name))

    def test_agent_birth_config_projects_verified_cloudflare_handoff_origins(self):
        import browserless_podman_deploy as deploy

        cfg = deploy.render_config(self.binding())
        self.assertEqual(
            cfg["browserlessHumanPublicOrigins"],
            {
                "chatgpt-carrier-11": "https://handoff-11.ordivon.com",
                "chatgpt-carrier-12": "https://handoff-12.ordivon.com",
                "chatgpt-carrier-13": "https://handoff-13.ordivon.com",
            },
        )

    def test_only_declared_warm_chatgpt_instance_is_boot_materialized(self):
        import browserless_podman_deploy as deploy

        self.assertEqual(deploy.WARM_CHATGPT_INSTANCES, (11,))
        cfg = deploy.render_config(self.binding())
        self.assertEqual(cfg["browserlessWarmEndpointIds"], ["chatgpt-carrier-11"])

    def test_browserless_executes_podman_without_docker_execution_path(self):
        source = (ROOT / "scripts/browserless_podman_deploy.py").read_text()
        self.assertIn("/usr/bin/podman", source)
        self.assertNotIn("/usr/bin/docker", source)
        self.assertNotIn("/usr/bin/containerd", source)


if __name__ == "__main__":
    unittest.main()
