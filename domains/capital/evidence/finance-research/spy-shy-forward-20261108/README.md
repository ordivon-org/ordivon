# ETF investment research: a real retrospective result and prospective plan

Date: 2026-11-08. This is a real data-driven, strictly non-live Finance
research result, not a claimed statistical trading edge.

## Real historical economic comparison

Pre-existing Capital example: 60% SPY / 40% SHY daily constant-mix vs 100%
SPY. Virtual initial USD 100,000; 2025-01-02 through 2026-08-10, 400
return periods; strategy/benchmark annual expense assumptions 0.002/0.001
charged per observation as fraction divided by 252.

- Mixed terminal NAV: USD 122,561.63.
- SPY reference terminal NAV: USD 134,273.58.
- Mixed minus SPY: negative USD 11,711.96.
- Maximum drawdown: mixed 11.15%, SPY 18.77%.

The fixed mix has lower historical return and lower historical drawdown.
Without an investor utility objective, neither path is proved superior.
This daily adjusted-close simulation does not include actual closing fills,
taxes, realistic trading slippage, total-return provider certification, or
reliable evidence the historical data was available at each trading date.

## Upstream GitHub source and independent verification

Source is the existing reference example in
examples/paper_fixed_mix_etf_20261106.json:

- Repository: https://github.com/manisahni/marketdata
- Commit: 65a079329e379e104495f459e12e76a8f995585a
- Path: daily_adjclose.csv
- Git Blob SHA-1: 29175a3fd8700cab31762bd72ced772ea5d1c807
- File SHA-256: 361efb287116fc8200582c15fcd315bcce2e218fa1e50b416bacc5acebff37b9
- File size: 1,511,995 bytes

The GitHub API confirmed the commit-to-path identity; retrieved raw
bytes matched both digests. No copied upstream CSV is checked into Ordivon.
A separate Python csv/Decimal daily wealth, expense and drawdown calculation
reproduced the official Portfolio replay over all 400 intervals to less
than USD 0.000001 discrepancy. Source-host identity and numerical arithmetic
are qualified here; the original price vendor, PIT history and true
market total-return adjustment are NOT independently authenticated.

## Actual forward research freeze

The source's existing fixed 60/40 policy was frozen on
2026-11-08T15:10:58Z through the native Research freeze-experiment CLI.
Training uses 2025, validation 2026-01-02 to 2026-08-10, and the untouched
future holdout is planned for 2026-11-09 to 2027-03-31. The exact
research-plan.json, frozen-plan.json, retrospective-result.json and
current-assessment.json are retained in this directory.

Plan digest: sha256:3798e0f219081439f0679dd57f1e4c77aa0842bb11e7561517d28c94023b9501.
configDigest commits to the bytes of the existing example policy;
environmentDigest commits to the pinned local uv.lock + mise.toml byte
combination. Source baseline revision and GitHub source identity are
included in the frozen plan. This plan was fixed **after looking at**
retrospective results; it is an honest new forward experiment rather than
independently pre-registered historical research. When this branch is
published, Git history witnesses the prospective plan's publication; the
frozen receipt itself does not attest a trusted third-party clock.

Current native Finance assessment: UNKNOWN / NO_HOLDOUT_EVIDENCE.
No forward returns or market events have been fabricated, and research
artifacts grant no capital allocation or actual broker effects.

## Reproduce the economics using existing tools, without a new backtester

From repository root, with authenticated gh and the owner toolchain:

~~~bash
tmp="$(mktemp -d)"
gh api repos/manisahni/marketdata/git/blobs/29175a3fd8700cab31762bd72ced772ea5d1c807 --jq .content | base64 -d > "$tmp/source.csv"
sha256sum "$tmp/source.csv"
git hash-object "$tmp/source.csv"
cd domains/capital
scripts/run-paper-etf-replay-r1 --request examples/paper_fixed_mix_etf_20261106.json --source "$tmp/source.csv" --output "$tmp/paper-result.json"
scripts/run-finance-lego freeze-experiment < evidence/finance-research/spy-shy-forward-20261108/research-plan.json
~~~

These commands consume the original existing Markets, Portfolio and
Research LEGO. Never classify a retrospectively obtained source as
precommitted historical investment information.

**Decision:** NO_VERIFIED_ACTIVE_EDGE_NO_ORDER. Future evidence requires
real newly observed sessions, provider/rights/corporate-action evidence,
a complete cost basis and independent experiment evaluation.
