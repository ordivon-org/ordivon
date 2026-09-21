import unittest

from ordivon_capital.research.okx_factor_observer import (
    OkxFactorObserverError,
    parse_completed_daily_returns,
)


class OkxFactorObserverTests(unittest.TestCase):
    def test_parser_excludes_incomplete_candle_and_sorts_provider_reverse_order(self):
        payload = {
            "code": "0",
            "data": [
                ["3000", "0", "0", "0", "130", "0", "0", "0", "0"],
                ["2000", "0", "0", "0", "121", "0", "0", "0", "1"],
                ["1000", "0", "0", "0", "110", "0", "0", "0", "1"],
                ["0", "0", "0", "0", "100", "0", "0", "0", "1"],
            ],
        }
        out = parse_completed_daily_returns(instrument_id="X", payload=payload)
        self.assertEqual(set(out), {1000, 2000})
        self.assertAlmostEqual(out[1000], 0.0953101798)
        self.assertAlmostEqual(out[2000], 0.0953101798)

    def test_parser_fails_closed_on_provider_error(self):
        with self.assertRaises(OkxFactorObserverError):
            parse_completed_daily_returns(
                instrument_id="X",
                payload={"code": "50000", "data": []},
            )


if __name__ == "__main__":
    unittest.main()
