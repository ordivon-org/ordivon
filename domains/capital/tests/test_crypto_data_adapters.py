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

    def test_provider_native_public_data_is_primary_and_nautilus_is_candidate_only(self):
        x=json.loads(CFG.read_text())
        self.assertEqual(x['okx']['primaryPublicDataPath'],'OKX_OFFICIAL_PUBLIC_REST_WS')
        self.assertEqual(x['binance']['primaryPublicDataPath'],'BINANCE_OFFICIAL_PUBLIC_REST_WS')
        self.assertEqual(x['okx']['historicalNautilusNativeAdapter']['standing'],'PASS_NATIVE_OKX_PUBLIC_QUOTES')
        self.assertEqual(x['binance']['historicalNautilusNativeAdapter']['standing'],'BLOCKED_DATA_CLIENT_STARTUP')
        self.assertEqual(x['okx']['historicalNautilusNativeAdapter']['role'],'HISTORICAL_CANDIDATE_EVIDENCE_ONLY')
        self.assertEqual(x['binance']['historicalNautilusNativeAdapter']['role'],'HISTORICAL_CANDIDATE_EVIDENCE_ONLY')

    def test_policy_checker(self):
        out=subprocess.check_output([str(ROOT/'scripts/check-crypto-data-adapter-policy')],text=True)
        x=json.loads(out)
        self.assertEqual(x['standing'],'PASS_CRYPTO_PUBLIC_DATA_ADAPTER_POLICY')
        self.assertEqual(x['okxPrimary'],'OKX_OFFICIAL_PUBLIC_REST_WS')
        self.assertEqual(x['binancePrimary'],'BINANCE_OFFICIAL_PUBLIC_REST_WS')
        self.assertTrue(x['nautilusCandidateOnly'])
        self.assertFalse(x['credentialsAllowed'])
        self.assertFalse(x['executionClientsAllowed'])


if __name__=='__main__':
    unittest.main()
