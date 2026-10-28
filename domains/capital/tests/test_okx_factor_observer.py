import math
import unittest
from unittest.mock import patch

from ordivon_capital.research.okx_factor_observer import (
    OkxFactorObserverError,
    capture_okx_factor_observatory,
    parse_completed_daily_returns,
)


class OkxFactorObserverTests(unittest.TestCase):
    def test_parser_excludes_incomplete_candle_and_sorts_provider_reverse_order(self):
        day = 86_400_000
        payload = {
            "code": "0",
            "data": [
                [str(3 * day), "0", "0", "0", "130", "0", "0", "0", "0"],
                [str(2 * day), "0", "0", "0", "121", "0", "0", "0", "1"],
                [str(day), "0", "0", "0", "110", "0", "0", "0", "1"],
                ["0", "0", "0", "0", "100", "0", "0", "0", "1"],
            ],
        }
        out = parse_completed_daily_returns(instrument_id="X", payload=payload)
        self.assertEqual(set(out), {day, 2 * day})
        self.assertAlmostEqual(out[day], 0.0953101798)
        self.assertAlmostEqual(out[2 * day], 0.0953101798)

    def test_daily_return_rejects_missing_calendar_bar(self):
        """A two-day compounded change must never be issued as 1D_LOG_RETURN."""
        day = 86_400_000
        rows = [
            [str(3 * day), "0", "0", "0", "121", "0", "0", "0", "1"],
            [str(day), "0", "0", "0", "110", "0", "0", "0", "1"],
            ["0", "0", "0", "0", "100", "0", "0", "0", "1"],
        ]
        with self.assertRaisesRegex(OkxFactorObserverError, "nonconsecutive completed 1D"):
            parse_completed_daily_returns(
                instrument_id="BTC-USDT", payload={"code": "0", "data": rows}
            )

    def test_daily_return_rejects_unconfirmed_middle_day(self):
        """Filtering an unfinished candle must not secretly span two days."""
        day = 86_400_000
        rows = [
            [str(3 * day), "0", "0", "0", "121", "0", "0", "0", "1"],
            [str(2 * day), "0", "0", "0", "115", "0", "0", "0", "0"],
            [str(day), "0", "0", "0", "110", "0", "0", "0", "1"],
            ["0", "0", "0", "0", "100", "0", "0", "0", "1"],
        ]
        with self.assertRaisesRegex(OkxFactorObserverError, "nonconsecutive completed 1D"):
            parse_completed_daily_returns(
                instrument_id="BTC-USDT", payload={"code": "0", "data": rows}
            )

    def test_daily_return_rejects_subdaily_or_duplicate_bar(self):
        """A provider payload cannot forge a one-day observation grid."""
        day = 86_400_000
        for times in ([0, day // 2, day], [0, day, day]):
            with self.subTest(times=times):
                rows = [
                    [str(ts), "0", "0", "0", str(100 + i), "0", "0", "0", "1"]
                    for i, ts in enumerate(times)
                ]
                with self.assertRaisesRegex(OkxFactorObserverError, "nonconsecutive completed 1D"):
                    parse_completed_daily_returns(
                        instrument_id="BTC-USDT", payload={"code": "0", "data": rows}
                    )

    def test_parser_fails_closed_on_provider_error(self):
        with self.assertRaises(OkxFactorObserverError):
            parse_completed_daily_returns(
                instrument_id="X",
                payload={"code": "50000", "data": []},
            )


class OkxFactorCompositionTests(unittest.TestCase):
    """Actual material -> factor method -> tail-risk business consumer chain."""

    @staticmethod
    def _payload(phase: float, *, missing_day: int | None = None):
        day = 86_400_000
        rows = []
        for i in range(104, -1, -1):
            if i == missing_day:
                continue
            close = 100 * math.exp(0.01 * math.sin(i / 7 + phase) + i * 0.0001)
            rows.append([str(i * day), "0", "0", "0", str(close), "0", "0", "0", "1"])
        return {"code": "0", "data": rows}

    def _capture(self, payloads):
        # No actual external provider, credential or financial-write authority.
        with patch(
            "ordivon_capital.research.okx_factor_observer._request",
            side_effect=lambda proxy, inst, limit: payloads[inst],
        ):
            return capture_okx_factor_observatory(
                base_instrument_id="BASE",
                factor_proxies=[{"factor": "sector", "instrumentId": "PROXY"}],
                proxy="http://127.0.0.1:8080",
                limit=105,
                include_validation=True,
                validation_splits=5,
                include_monitoring=True,
                monitoring_holdout=30,
            )

    def test_factor_observer_composition_requires_genuine_daily_return_horizon(self):
        valid = {"BASE": self._payload(0.0), "PROXY": self._payload(0.3)}
        product = self._capture(valid)
        self.assertEqual(product["factorObservatory"]["factorCount"], 1)
        self.assertEqual(product["modelValidation"]["rows"][0]["validation"]["nSplits"], 5)
        self.assertEqual(product["tailRisk"]["series"][0]["returnHorizon"], "1D_LOG_RETURN")
        self.assertFalse(product["brokerCredentialsUsed"])
        self.assertFalse(product["externalFinancialWriteAttempted"])

        # Either source can poison the common aligned-return timeline.
        # No partially labeled high-level factor or 1D tail report is returned.
        for invalid_instrument in ("BASE", "PROXY"):
            with self.subTest(instrument=invalid_instrument):
                mutated = dict(valid)
                mutated[invalid_instrument] = self._payload(
                    0.0 if invalid_instrument == "BASE" else 0.3,
                    missing_day=41,
                )
                with self.assertRaisesRegex(
                    OkxFactorObserverError, "nonconsecutive completed 1D"
                ):
                    self._capture(mutated)


if __name__ == "__main__":
    unittest.main()
