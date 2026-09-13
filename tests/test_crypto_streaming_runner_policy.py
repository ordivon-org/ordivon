from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class StreamingRunnerPolicyTests(unittest.TestCase):
    def test_public_only_endpoints_and_no_execution(self):
        s=(ROOT/'src/market_capital/crypto_public_streaming.py').read_text()
        self.assertIn('wss://ws.okx.com:8443/ws/v5/public',s)
        self.assertIn('wss://data-stream.binance.vision/stream?streams=btcusdt@ticker/ethusdt@ticker',s)
        self.assertIn('hostWallClockUsedForAdmission',s)
        self.assertIn('brokerCredentialsUsed',s)
    def test_failover_is_concrete_node_protocol_ingress_and_runs_real_streaming(self):
        s=(ROOT/'scripts/run-crypto-public-shadow-r2').read_text()
        self.assertIn("hk-hkg|openvpn-udp|native-a|30",s)
        self.assertIn("hk-hkg|openvpn-udp|native-b|30",s)
        self.assertIn("jp-tok|openvpn-udp|native-a|30",s)
        self.assertIn("sg-sng|openvpn-tcp|native-a|30",s)
        c=(ROOT/'scripts/run-crypto-public-streaming-r2-candidate').read_text()
        self.assertIn('--ingresses "$ingress"',c)
        self.assertIn('https://data-api.binance.vision',c)
        self.assertIn('crypto_public_streaming',c)
if __name__=='__main__': unittest.main()
