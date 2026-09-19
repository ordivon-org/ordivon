import unittest
from ordivon_capital.market.crypto_public_streaming import evaluate_snapshot, KEYS

def row(t,mono,bid='100',ask='101'):
    return {'sourceTimeMs':t,'recvMonoNs':mono,'bid':bid,'ask':ask,'recvWallNs':0,'venue':'X','asset':'X'}

class StreamingSnapshotTests(unittest.TestCase):
    def test_qualified_snapshot_requires_all_streams_and_bounded_spans(self):
        latest={
          'OKX:BTC':row(1000,1_000_000_000), 'OKX:ETH':row(1010,1_010_000_000),
          'BINANCE:BTC':row(1100,1_100_000_000), 'BINANCE:ETH':row(1110,1_110_000_000),
        }
        x=evaluate_snapshot(latest)
        self.assertTrue(x['qualified']); self.assertEqual(x['reason'],'PASS')
        self.assertLessEqual(x['sourceTimeSpanMs'],1200); self.assertLessEqual(x['receiveTimeSpanMs'],1200)
    def test_previous_snapshot_requires_every_stream_to_advance(self):
        prev={k:row(1000,1_000_000_000) for k in KEYS}
        cur={k:row(1001,1_100_000_000) for k in KEYS}; cur['OKX:BTC']=row(1000,1_100_000_000)
        x=evaluate_snapshot(cur,prev)
        self.assertFalse(x['qualified']); self.assertEqual(x['reason'],'NOT_ALL_STREAMS_ADVANCED')
    def test_span_gate_fails_closed(self):
        latest={
          'OKX:BTC':row(1000,1_000_000_000), 'OKX:ETH':row(1010,1_010_000_000),
          'BINANCE:BTC':row(2300,2_300_000_000), 'BINANCE:ETH':row(2310,2_310_000_000),
        }
        x=evaluate_snapshot(latest)
        self.assertFalse(x['qualified']); self.assertEqual(x['reason'],'SPAN_GATE_FAILED')
if __name__=='__main__': unittest.main()
