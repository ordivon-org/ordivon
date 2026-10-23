import json
import os
import subprocess
import tempfile
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


    def _run_isolated_checker(self, data: dict, *, optimized: bool):
        # Exercise the REAL shell/Python policy validator with isolated JSON.
        # A fixture-only prerequisite verifies the expected non-live guard call.
        # No provider network, account, credential or financial effects.
        with tempfile.TemporaryDirectory(prefix="ordivon-capital-crypto-policy-") as directory:
            root = Path(directory)
            scripts = root / "scripts"
            config = root / "config"
            scripts.mkdir()
            config.mkdir()
            script = scripts / "check-crypto-data-adapter-policy"
            script.write_bytes((ROOT / "scripts/check-crypto-data-adapter-policy").read_bytes())
            script.chmod(0o755)
            guard = scripts / "check-execution-policy"
            guard.write_text(
                '#!/usr/bin/env bash\n'
                '[[ "$1" == "--mode" && "$2" == "non-live" ]]\n',
                encoding="utf-8",
            )
            guard.chmod(0o755)
            (config / "crypto_data_adapters.json").write_text(json.dumps(data), encoding="utf-8")
            env = dict(os.environ)
            env["PYTHONOPTIMIZE"] = "1" if optimized else "0"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            return subprocess.run(
                [str(script)], env=env, text=True, capture_output=True, check=False, timeout=20
            )

    def test_checker_keeps_valid_public_only_policy_in_both_python_modes(self):
        data = json.loads(CFG.read_text(encoding="utf-8"))
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self._run_isolated_checker(data, optimized=optimized)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_checker_rejects_forbidden_credentials_and_execution_under_python_o(self):
        baseline = json.loads(CFG.read_text(encoding="utf-8"))
        mutations = (
            ("okx.credentialsAllowed", "okx", "credentialsAllowed"),
            ("binance.executionClientAllowed", "binance", "executionClientAllowed"),
            ("binance.sbeCredentialsWorkaroundAllowed", "binance", "sbeCredentialsWorkaroundAllowed"),
        )
        for label, venue, key in mutations:
            for optimized in (False, True):
                with self.subTest(policy=label, optimized=optimized):
                    invalid = json.loads(json.dumps(baseline))
                    invalid[venue][key] = True
                    result = self._run_isolated_checker(invalid, optimized=optimized)
                    self.assertNotEqual(
                        result.returncode, 0,
                        "unsafe crypto policy was accepted: " + label + " in optimized=" + str(optimized),
                    )


if __name__=='__main__':
    unittest.main()
