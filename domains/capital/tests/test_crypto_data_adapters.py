import json
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config/crypto_data_adapters.json'

class CryptoDataAdapterPolicyTests(unittest.TestCase):
    def test_public_only_and_no_credential_workaround(self):
        x=json.loads(CFG.read_text())
        self.assertEqual(x['standing'],'PUBLIC_DATA_ONLY')
        self.assertFalse(x['okx']['credentialsAllowed'])
        self.assertFalse(x['binance']['credentialsAllowed'])
        self.assertFalse(x['binance']['sbeCredentialsWorkaroundAllowed'])
        self.assertFalse(x['okx']['executionClientAllowed'])
        self.assertFalse(x['binance']['executionClientAllowed'])

    def test_asymmetric_adapter_admission_is_explicit(self):
        x=json.loads(CFG.read_text())
        self.assertEqual(x['okx']['nativeAdapterStanding'],'PASS_NATIVE_OKX_PUBLIC_QUOTES')
        self.assertEqual(x['binance']['nativeAdapterStanding'],'BLOCKED_DATA_CLIENT_STARTUP')
        self.assertEqual(x['binance']['primaryPublicDataPath'],'BINANCE_OFFICIAL_PUBLIC_REST_WS')

    def test_policy_checker(self):
        out=subprocess.check_output([str(ROOT/'scripts/check-crypto-data-adapter-policy')],text=True)
        x=json.loads(out)
        self.assertEqual(x['standing'],'PASS_CRYPTO_PUBLIC_DATA_ADAPTER_POLICY')
        self.assertFalse(x['credentialsAllowed'])
        self.assertFalse(x['executionClientsAllowed'])

if __name__=='__main__':
    unittest.main()
