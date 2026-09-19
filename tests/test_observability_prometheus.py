import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "observability/prometheus.yml"

class PrometheusDesiredStateTests(unittest.TestCase):
    def test_external_owner_rule_files_are_preserved_without_copying_rule_semantics(self):
        text = CONFIG.read_text()
        self.assertIn('rule_files:', text)
        self.assertIn('/etc/prometheus/rules/*.yml', text)
        self.assertNotIn('MarketCapitalCrypto', text)

    def test_cloudflared_a_b_metrics_are_scraped_as_provider_telemetry(self):
        text = CONFIG.read_text()
        self.assertIn('job_name: operations-v2-cloudflared-production', text)
        self.assertIn('127.0.0.1:20243', text)
        self.assertIn('127.0.0.1:20244', text)
        self.assertIn('ordivon_scope: cloudflare-connector-metrics', text)
        self.assertIn('connector_profile: A', text)
        self.assertIn('connector_profile: B', text)

if __name__ == '__main__': unittest.main()
