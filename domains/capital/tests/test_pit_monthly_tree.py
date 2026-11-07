"""Historical monthly joint paths and nonanticipative multi-period boundary.

Synthetic finance figures are adversarial fixture values, not recommended leverage.
"""
import hashlib
import json
import subprocess
import sys
import unittest
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ordivon_capital.research.pit_monthly_paths import (  # noqa: E402
    PointInTimeError,
    PriceVintage,
    completed_monthly_sessions,
    from_multiperiod_json_payload,
    historical_multiperiod_tree,
)

DIGEST = hashlib.sha256(b'frozen-vintage-fixture').hexdigest()


def snapshot():
    # Every listed monthly session is last known source-calendar trading day.
    months = ('2026-01-30', '2026-02-27', '2026-03-31',
              '2026-04-30', '2026-05-29', '2026-06-30', '2026-07-31')
    sessions = tuple(date.fromisoformat(x) for x in months)
    data = []
    for ticker, closes in (
        ('A', (100, 110, 99, 108.9, 119.79, 107.811, 118.5921)),
        ('B', (100, 90, 99, 89.1, 80.19, 88.209, 79.3881)),
    ):
        for s, close in zip(sessions, closes, strict=True):
            data.append(PriceVintage(ticker, s,
                  datetime.fromisoformat(s.isoformat()+'T22:00:00+00:00'),
                  close, DIGEST, 'SECONDARY_VENDOR_NOT_ATTESTED'))
    return sessions, data


def args():
    sessions, records = snapshot()
    return dict(records=records, assets=('A','B'), trading_sessions=sessions,
        as_of=datetime.fromisoformat('2026-08-01T04:00:00+00:00'),
        horizon_months=2, gamma=2,
        initial_margin_by_stage=((.4,.4),(.5,.5)),
        turnover_cost_by_stage=((.01,.01),(.02,.02)),
        maintenance_by_stage=((.35,.35),(.45,.45)),
        cash_gross_by_stage=(1.005,1.006), debt_gross_by_stage=(1.008,1.009))


def monthly_json_payload():
    x = args()
    payload = {
        "as_of": x["as_of"].isoformat(),
        "assets": list(x["assets"]),
        "trading_sessions": [d.isoformat() for d in x["trading_sessions"]],
        "prices": [
            {
                "asset": r.asset,
                "session": r.session.isoformat(),
                "published_at": r.published_at.isoformat(),
                "adjusted_close": r.adjusted_close,
                "raw_source_sha256": r.raw_source_sha256,
                "source_standing": r.source_standing,
            }
            for r in x["records"]
        ],
        "horizon_months": 2,
        "economic_contract": {
            k: [list(z) for z in v]
            if k.endswith("by_stage") and k not in (
                "cash_gross_by_stage", "debt_gross_by_stage",
            )
            else list(v)
            for k, v in x.items() if k.endswith("by_stage")
        },
    }
    payload["economic_contract"]["gamma"] = 2
    return payload


class MonthlyTree(unittest.TestCase):
    def test_month_end_calendar_never_finalizes_partial_month(self):
        sessions, _ = snapshot()
        m = completed_monthly_sessions(sessions, as_of=datetime(2026,7,10,tzinfo=UTC))
        self.assertEqual(m[-1], date(2026,6,30))
        self.assertNotIn(date(2026,7,31), m)
        with self.assertRaisesRegex(PointInTimeError, 'offset'):
            completed_monthly_sessions(sessions, as_of=datetime(2026,8,1))

    def test_prefix_trie_merges_same_observed_history_and_sums_probability(self):
        r = historical_multiperiod_tree(**args())
        nodes = r['optimizer_input']['nodes']
        self.assertEqual(r['standing'], 'STRUCTURAL_HISTORICAL_PATH_TREE_NOT_PREDICTIVE_ADMISSIBLE')
        self.assertEqual(r['forecast_evidence']['single_successor_states'], 1)
        self.assertEqual(r['forecast_evidence']['post_observation_states'], 2)
        self.assertEqual(r['forecast_evidence']['predictive_recursion'], 'NOT_IDENTIFIED_UNCALIBRATED_EXACT_HISTORY_PREFIXES')
        self.assertEqual(r['forecast_evidence']['path_count'], 5)
        # Price-divisions with algebraically identical return ratios must
        # share one public information state, not split on float artifacts.
        self.assertEqual(r['forecast_evidence']['distinct_paths'], 3)
        self.assertEqual(r['forecast_evidence']['tree_node_count'], 6)
        self.assertEqual(r['forecast_evidence']['excluded_incomplete_paths'], 0)
        self.assertEqual(len(nodes[0]['initial_margin']), 2)
        byid = {node['id']:node for node in nodes}
        self.assertEqual(sum(n['conditional_probability'] for n in nodes if n['parent']=='root'), 1)
        for parent in (n for n in nodes if n['t']==1):
            children=[n for n in nodes if n['parent']==parent['id']]
            self.assertAlmostEqual(sum(n['conditional_probability'] for n in children),1)
            self.assertEqual(len(parent['initial_margin']),2)
            self.assertEqual(parent['cash_gross'],1.005)
            self.assertEqual(parent['debt_gross'],1.008)
        for node in nodes:
            if node['terminal']:
                self.assertEqual(node['t'],2)
                self.assertEqual(node['initial_margin'],[])
                self.assertEqual(node['turnover_cost'],[])
            elif node['t']>0:
                self.assertEqual(node['initial_margin'],[.5,.5])
                self.assertEqual(node['turnover_cost'],[.02,.02])
            if node['parent']:
                self.assertLess(byid[node['parent']]['t'],node['t'])

    def test_later_revisions_cannot_affect_old_tree_and_no_unknown_broker_terms(self):
        x=args(); original=historical_multiperiod_tree(**x)
        revised=PriceVintage('A', date(2026,3,31),
             datetime.fromisoformat('2026-08-02T13:00:00+00:00'),
             9999,DIGEST,'SECONDARY_VENDOR_NOT_ATTESTED')
        x['records']=[*x['records'],revised]
        self.assertEqual(historical_multiperiod_tree(**x),original)
        x['debt_gross_by_stage']=()
        with self.assertRaisesRegex(PointInTimeError,'financing'):
            historical_multiperiod_tree(**x)

    def test_missing_month_price_excludes_all_path_windows_not_forward_fill(self):
        x=args(); x['records']=[r for r in x['records']
                                 if not (r.asset=='B' and r.session==date(2026,3,31))]
        result=historical_multiperiod_tree(**x)
        self.assertGreater(result['forecast_evidence']['excluded_incomplete_paths'],0)
        self.assertLess(result['forecast_evidence']['path_count'],5)

    def test_cli_evidence_json_contract_exact_and_not_execution(self):
        payload = monthly_json_payload()
        a=from_multiperiod_json_payload(payload)
        self.assertEqual(set(a['optimizer_input']),{'gamma','nodes'})
        self.assertEqual(a['effects'],'NONE_NO_TRADE_NO_ACCOUNTING')
        self.assertEqual(len(a['input_sha256']),64)
        self.assertNotIn('forecast_evidence',a['optimizer_input'])
        # Native CLI belongs to Research and emits only JSON, no side effects.
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            src=Path(directory)/'input.json'
            src.write_text(json.dumps(payload))
            proc=subprocess.run([sys.executable,'-m','ordivon_capital.research.pit_joint_forecast',
                                '--mode','monthly-tree','--input',str(src)],
                                capture_output=True,text=True,env={**__import__('os').environ,
                                     'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')})
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertEqual(json.loads(proc.stdout),a)

    def test_cli_monthly_solves_native_portfolio_with_explicit_terminal_claims(self):
        # Historical structural valuation is not a forward-calibrated forecast.
        import tempfile

        payload = monthly_json_payload()
        raw = from_multiperiod_json_payload(payload)
        terminal_ids = {
            n["id"] for n in raw["optimizer_input"]["nodes"] if n["terminal"]
        }
        self.assertTrue(terminal_ids)
        payload["terminal_liabilities_r"] = {leaf: .25 for leaf in terminal_ids}
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "monthly.json"
            src.write_text(json.dumps(payload))
            command = [
                sys.executable, "-m", "ordivon_capital.research.pit_joint_forecast",
                "--mode", "monthly-tree", "--solve", "--input", str(src),
            ]
            env = {
                **__import__("os").environ,
                "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
            }
            proc = subprocess.run(
                command, capture_output=True, text=True, env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(proc.stdout)
            self.assertEqual(
                data["allocation_standing"],
                "STRUCTURAL_HISTORICAL_PATH_POLICY_NUMERIC_NOT_PREDICTIVE",
            )
            self.assertEqual(data["effects"], "NONE_NO_TRADE_NO_ACCOUNTING")
            self.assertEqual(
                set(data["optimizer_input"]["terminal_liabilities_r"]), terminal_ids,
            )
            solution = data["conditional_allocation"]
            self.assertEqual(solution["contributions_r_per_path"], 2)
            self.assertEqual(set(solution["terminal_distribution"]), terminal_ids)
            self.assertAlmostEqual(
                solution["expected_terminal_r"]
                - solution["expected_disposable_terminal_r"],
                .25, places=6,
            )
            self.assertGreaterEqual(
                solution["concavity_global_utility_gap_upper"], 0,
            )
            # Missing terminal obligations are not silently filled with zero.
            missing = dict(payload)
            missing["terminal_liabilities_r"] = {
                next(iter(sorted(terminal_ids))): .25
            }
            src.write_text(json.dumps(missing))
            rejected = subprocess.run(
                command, capture_output=True, text=True, env=env,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("terminal", rejected.stderr.lower())

    def test_monthly_pit_tree_consumed_by_existing_terminal_liability_solver(self):
        # This is a synthetic contract-consumption witness, not a predictive backtest.
        producer = historical_multiperiod_tree(**args())
        self.assertEqual(
            producer['standing'], 'STRUCTURAL_HISTORICAL_PATH_TREE_NOT_PREDICTIVE_ADMISSIBLE'
        )
        payload = dict(producer['optimizer_input'])
        terminal_ids = [n['id'] for n in payload['nodes'] if n['terminal']]
        self.assertTrue(terminal_ids)
        # An explicit economic obligation belongs to the consumer, not to price history.
        payload['terminal_liabilities_r'] = {name: .25 for name in terminal_ids}
        proc = subprocess.run(
            [sys.executable, '-m', 'ordivon_capital.portfolio.multistage_policy',
             '--input', '-'],
            input=json.dumps(payload), capture_output=True, text=True,
            env={**__import__('os').environ,
                 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = json.loads(proc.stdout)
        self.assertEqual(output['inputStanding'], 'CALLER_SUPPLIED_NOT_MARKET_ATTESTED')
        self.assertEqual(output['effectStanding'], 'READ_ONLY_NO_BROKER_NO_PAPER_LEDGER')
        solution = output['solution']
        self.assertEqual(set(solution['terminal_distribution']), set(terminal_ids))
        self.assertAlmostEqual(
            solution['expected_terminal_r'] - solution['expected_disposable_terminal_r'],
            .25, places=6,
        )
        self.assertTrue(all(
            abs(item['obligationR'] - .25) < 1e-12 and item['disposableTerminalR'] > 0
            for item in solution['terminal_distribution'].values()
        ))
        self.assertGreaterEqual(solution['concavity_global_utility_gap_upper'], 0)

if __name__ == '__main__':
    unittest.main()
