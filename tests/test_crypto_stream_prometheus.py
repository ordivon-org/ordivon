from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class CryptoStreamPrometheusTests(unittest.TestCase):
    def test_metrics_truth_and_safety_boundary(self):
        out=subprocess.check_output([str(ROOT/'scripts/render-crypto-stream-prometheus')],text=True)
        self.assertIn('ordivon_market_capital_crypto_public_stream_r2_qualified 1',out)
        self.assertIn('ordivon_market_capital_crypto_stream_resilience_local_fault_model_qualified 1',out)
        self.assertIn('ordivon_market_capital_crypto_stream_reconnect_live_qualified 1',out)
        self.assertIn('ordivon_market_capital_crypto_stream_reconnect_latency_ms{venue="okx"}',out)
        self.assertIn('ordivon_market_capital_crypto_stream_reconnect_latency_ms{venue="binance"}',out)
        self.assertIn('ordivon_market_capital_crypto_surfpath_control_plane_blocked 0',out)
        self.assertIn('ordivon_market_capital_crypto_execution_authority_write_admitted 0',out)
        self.assertIn('ordivon_market_capital_crypto_clock_private_gate_passed 0',out)
        self.assertIn('ordivon_market_capital_crypto_clock_remediation_admin_required 1',out)
        self.assertIn('ordivon_market_capital_crypto_private_execution_allowed 0',out)
        self.assertIn('ordivon_market_capital_crypto_external_financial_writes_attempted 0',out)
    def test_atomic_file_render(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'market-capital.prom'
            subprocess.check_call([str(ROOT/'scripts/render-crypto-stream-prometheus'),'--output',str(p)])
            self.assertTrue(p.exists()); self.assertFalse(Path(str(p)+'.tmp').exists())
if __name__=='__main__': unittest.main()
