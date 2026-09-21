import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class StreamingRunnerPolicyTests(unittest.TestCase):
    def test_public_only_endpoints_and_exact_network_v2_ws_proxies(self):
        s=(ROOT/'src/ordivon_capital/markets/crypto_public_streaming.py').read_text()
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
        self.assertIn('run-capability-python',candidate)
        self.assertIn('-m ordivon_capital.markets.crypto_public_streaming',candidate)
        self.assertNotIn('/usr/bin/uv run',candidate)
        self.assertNotIn('src/ordivon_capital/markets/crypto_public_streaming.py',candidate)
        self.assertNotIn('.venv/bin/python',candidate)
        self.assertIn('network-v2-provider-auto',master)


    def test_r3_session_uses_canonical_python_runner_and_always_aggregates_both_venues(self):
        session=(ROOT/'scripts/run-crypto-stream-resilience-r3-session').read_text()
        assert 'run-capability-python" -m ordivon_capital.markets.crypto_stream_resilience' in session
        assert '/usr/bin/uv run' not in session
        assert 'okx_rc=$?' in session
        assert 'binance_rc=$?' in session
        assert '"returnCode": okx_rc' in session
        assert '"returnCode": bn_rc' in session
        assert 'PARTIAL_DUAL_VENUE_PUBLIC_STREAM_RECONNECT' in session

if __name__=='__main__': unittest.main()
