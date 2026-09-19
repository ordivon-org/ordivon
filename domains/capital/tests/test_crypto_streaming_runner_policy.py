from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class StreamingRunnerPolicyTests(unittest.TestCase):
    def test_public_only_endpoints_and_exact_network_v2_ws_proxies(self):
        s=(ROOT/'src/ordivon_capital/market/crypto_public_streaming.py').read_text()
        self.assertIn('wss://ws.okx.com:8443/ws/v5/public',s)
        self.assertIn('wss://data-stream.binance.vision/stream?streams=btcusdt@ticker/ethusdt@ticker',s)
        self.assertIn('ORDIVON_MC_OKX_WS_PROXY',s)
        self.assertIn('ORDIVON_MC_BINANCE_SPOT_WS_PROXY',s)
        self.assertIn('proxy=proxy',s)
        self.assertIn('brokerCredentialsUsed',s)
    def test_master_has_no_surfpath_candidate_matrix(self):
        master=(ROOT/'scripts/run-crypto-public-shadow-r2').read_text()
        candidate=(ROOT/'scripts/run-crypto-public-streaming-r2-candidate').read_text()
        self.assertNotIn('surfpath',master.lower()+candidate.lower())
        self.assertNotIn('--ingresses',candidate)
        self.assertIn('check-network-v2-public-data',candidate)
        self.assertIn('/usr/bin/uv run --frozen --project',candidate)
        self.assertNotIn('.venv/bin/python',candidate)
        self.assertIn('network-v2-provider-auto',master)
if __name__=='__main__': unittest.main()
