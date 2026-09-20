from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from playwright_browserless_provider_preflight import safe_page_ref, result  # noqa: E402


class BrowserlessProviderPreflightTests(unittest.TestCase):
    def test_safe_page_ref_drops_query_and_fragment(self):
        self.assertEqual(
            safe_page_ref("https://chatgpt.com/?__cf_chl_rt_tk=secret#x"), "https://chatgpt.com/"
        )

    def test_rate_limit_modal_is_a_read_only_non_ready_admission_state(self):
        source = (ROOT / "scripts/playwright_browserless_provider_preflight.py").read_text()
        self.assertIn("PROVIDER_RATE_LIMIT_SELECTOR", source)
        self.assertIn('"PROVIDER_RATE_LIMITED"', source)
        first_ready = source.index('result(a.endpoint_id, "READY"')
        rate_limited = source.index('result(a.endpoint_id, "PROVIDER_RATE_LIMITED"')
        self.assertLess(rate_limited, first_ready)

    def test_result_is_explicitly_read_only(self):
        row = result(
            "carrier-a", "CHALLENGE_GATED", page_url="https://chatgpt.com/?__cf_chl_x=secret"
        )
        self.assertFalse(row["providerEffectAttempted"])
        self.assertFalse(row["clicked"])
        self.assertFalse(row["composerFilled"])
        self.assertFalse(row["sendAttempted"])
        self.assertFalse(row["assistantOutputRead"])
        self.assertNotIn("secret", str(row))


if __name__ == "__main__":
    unittest.main()
