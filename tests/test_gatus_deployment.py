from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "observability/gatus/config.yaml"
UNIT = ROOT / "observability/gatus/ordivon-gatus.service"
DEPLOY = ROOT / "scripts/deploy-gatus"


class GatusDeploymentTests(unittest.TestCase):
    def test_operations_owns_config_unit_and_deploy_paths(self) -> None:
        deploy = DEPLOY.read_text()
        self.assertIn('$ROOT/observability/gatus/config.yaml', deploy)
        self.assertIn('$ROOT/observability/gatus/ordivon-gatus.service', deploy)
        self.assertNotIn('/root/workstation-lab', deploy)

    def test_reviewed_binary_identity_is_preserved(self) -> None:
        text = DEPLOY.read_text()
        self.assertIn('GATUS_EXPECTED_VERSION="${GATUS_EXPECTED_VERSION:-5.36.0}"', text)
        self.assertIn('99c60412a77edd1dd887e68a49754d4ba9e06a48e1812e32fde155fd092815f6', text)
        self.assertIn('github.com/TwiN/gatus/v5', text)
        self.assertIn('sha256:c5f210d095fa78e6efaa20ffeb14803f2ba4f10615e16a6d12087697149617f0', text)
        self.assertIn('ed1107b41a30e22047eecfb6dbc3be5e39829d5a', text)
        self.assertNotIn('curl ', text.split('== 1. 安装二进制 ==')[0])

    def test_service_remains_loopback_only_and_hardened(self) -> None:
        text = UNIT.read_text()
        self.assertIn('Environment=GATUS_ADDRESS=127.0.0.1', text)
        self.assertIn('Environment=GATUS_PORT=8080', text)
        self.assertIn('NoNewPrivileges=true', text)
        self.assertIn('ProtectSystem=strict', text)

    def test_direct_profile_probes_use_exact_existing_loopback_proxies(self) -> None:
        text = CONFIG.read_text()
        for name, proxy in (
            ('native-a cloudflare trace', 'http://127.0.0.1:19081'),
            ('native-a github', 'http://127.0.0.1:19081'),
            ('native-b cloudflare trace', 'http://127.0.0.1:19082'),
            ('native-b github', 'http://127.0.0.1:19082'),
        ):
            self.assertIn(f'- name: {name}', text)
            self.assertIn(f'proxy-url: "{proxy}"', text)
        self.assertIn('point-in-time target reachability only', text)


if __name__ == '__main__':
    unittest.main()
