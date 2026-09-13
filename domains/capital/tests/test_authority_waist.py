from pathlib import Path
import json
import tempfile
import unittest

from market_capital.authority_waist import (
    AuthorityWaistError,
    evaluate_external_write,
    evaluate_non_live,
    verify_authority_binding,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/authority_waist.json"


class AuthorityWaistTests(unittest.TestCase):
    def test_external_provider_is_revision_and_digest_bound(self):
        result = verify_authority_binding(CONFIG)
        self.assertEqual(
            result["providerRevision"],
            "fd0a15db0152a1c35b4820b72e047df9db7a9e63",
        )
        self.assertEqual(result["productionState"], "BLOCK_NOT_GRANTED")
        self.assertFalse(result["productionGranted"])

    def test_current_non_live_lane_requires_block_not_granted(self):
        result = evaluate_non_live(CONFIG)
        self.assertEqual(result["standing"], "AUTHORITY_WAIST_BOUND_NON_LIVE")
        self.assertFalse(result["externalFinancialWritesAllowed"])
        self.assertFalse(result["effectAuthorityAvailableForExternalWrites"])

    def test_external_write_fails_closed_before_envelope_validation(self):
        with self.assertRaisesRegex(AuthorityWaistError, "external financial write admission is not admitted"):
            evaluate_external_write(CONFIG, None)

    def test_revision_drift_is_rejected(self):
        doc = json.loads(CONFIG.read_text())
        doc["provider"]["revision"] = "0" * 40
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "binding.json"
            path.write_text(json.dumps(doc))
            with self.assertRaisesRegex(AuthorityWaistError, "revision drift"):
                verify_authority_binding(path)

    def test_contract_digest_drift_is_rejected(self):
        doc = json.loads(CONFIG.read_text())
        doc["provider"]["contracts"]["productionAuthorization"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "binding.json"
            path.write_text(json.dumps(doc))
            with self.assertRaisesRegex(AuthorityWaistError, "contract digest drift"):
                verify_authority_binding(path)


if __name__ == "__main__":
    unittest.main()
