import json
import subprocess
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class CryptoShadowMechanicsTests(unittest.TestCase):
    def test_config_is_non_economic_and_non_live(self):
        cfg=json.loads((ROOT/'tools/nautilus_rc4/config/crypto_shadow_mechanics.json').read_text())
        self.assertEqual(cfg['purpose'],'MECHANICS_ONLY_NON_ECONOMIC')
        self.assertFalse(cfg['brokerConnectivityAllowed'])
        self.assertFalse(cfg['externalFinancialWritesAllowed'])
        self.assertFalse(cfg['economicDecisionClaimed'])
        self.assertFalse(cfg['alphaClaimed'])

    @pytest.mark.provider_qualification
    def test_nautilus_candidate_crypto_mechanics_passes(self):
        out=subprocess.check_output([str(ROOT/'tools/nautilus_rc4/run-crypto-shadow-mechanics-r1')],text=True)
        x=json.loads(out)
        self.assertEqual(x['standing'],'PASS_LOCAL_CRYPTO_SPOT_OMS_MECHANICS')
        self.assertEqual(len(x['orders']),4)
        self.assertTrue(all(o['status']=='FILLED' for o in x['orders']))
        self.assertFalse(x['brokerConnected'])
        self.assertFalse(x['externalFinancialWritesAttempted'])


if __name__=='__main__':
    unittest.main()
