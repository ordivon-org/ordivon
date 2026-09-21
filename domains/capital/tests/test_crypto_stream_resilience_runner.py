import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class ResilienceRunnerTests(unittest.TestCase):
    def test_both_venues_are_fault_injected_in_one_network_v2_session(self):
        s=(ROOT/'scripts/run-crypto-stream-resilience-r3-session').read_text()
        self.assertIn('--target-venue OKX',s)
        self.assertIn('--target-venue BINANCE',s)
        self.assertIn('PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT',s)
    def test_candidate_uses_exact_network_v2_authority_without_surfpath(self):
        s=(ROOT/'scripts/run-crypto-stream-resilience-r3-candidate').read_text()
        self.assertNotIn('surfpath',s.lower())
        self.assertNotIn('--ingresses',s)
        self.assertIn('check-network-v2-public-data',s)
        self.assertIn('ORDIVON_MC_OKX_WS_PROXY',s)
        self.assertIn('ORDIVON_MC_BINANCE_SPOT_WS_PROXY',s)
        session=(ROOT/'scripts/run-crypto-stream-resilience-r3-session').read_text()
        self.assertIn('run-capability-python',session)
        self.assertIn('-m ordivon_capital.market.crypto_stream_resilience',session)
        self.assertNotIn('/usr/bin/uv run',session)
        self.assertNotIn('.venv/bin/python', (ROOT/'scripts/run-crypto-stream-resilience-r3-session').read_text())
    def test_master_keeps_authority_and_clock_gates(self):
        s=(ROOT/'scripts/run-crypto-stream-resilience-r3').read_text()
        self.assertIn('check-execution-policy',s)
        self.assertIn('check-clock-quality-gate',s)
        self.assertIn('PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_NETWORK_V2_FAILOVER',s)
        self.assertNotIn('candidates=(',s)
if __name__=='__main__': unittest.main()
