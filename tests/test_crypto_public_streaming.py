import unittest

from ordivon_capital.markets.crypto_public_streaming import KEYS, evaluate_snapshot


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


class StreamingFailureAttributionTests(unittest.IsolatedAsyncioTestCase):
    async def test_reader_failure_is_not_masked_by_queue_timeout(self):
        import asyncio
        from unittest.mock import patch

        from ordivon_capital.markets import crypto_public_streaming as cps

        async def fail_reader(*_args, **_kwargs):
            await asyncio.sleep(0)
            raise ConnectionResetError(104, "connection reset by peer")

        async def queue_timeout(awaitable, *, timeout):
            await asyncio.sleep(0)
            if hasattr(awaitable, "close"):
                awaitable.close()
            raise TimeoutError

        with (
            patch.object(cps, "network_v2_ws_proxies", return_value=("http://a", "http://b")),
            patch.object(cps, "_okx_reader", side_effect=fail_reader),
            patch.object(cps, "_binance_reader", side_effect=fail_reader),
            patch.object(cps.asyncio, "wait_for", side_effect=queue_timeout),
        ):
            with self.assertRaises(ConnectionResetError):
                await cps.capture_streaming(rounds=1, warmup_rounds=0, deadline_seconds=0.1)
