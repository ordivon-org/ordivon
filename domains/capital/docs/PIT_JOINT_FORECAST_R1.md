# Capital Research — Point-in-time joint scenario evidence R1

**Status:** read-only research component, not an authenticated live forecast, a brokerage authorization, or Accounting/Paper Ledger settlement. The component is deliberately a *thin adapter* into the existing `Portfolio/multistage_policy.py` contract, not a duplicate optimizer, provider or execution platform.

## Mathematical representation

Let \(o=(i,s,v,p,h)\) denote a price vintage: asset \(i\), exchange session \(s\), a price \(v>0\) with an explicit price-basis label, the declared effective availability instant \(p\), and the raw source SHA256 commitment \(h\). This is a conditional mathematical model, not proof that a declared provider publication time is genuine. For information time \(t\), the selected price table is

\[
P_{i,s}^{(t)}=\operatorname*{argmax}_{o:\,o.i=i,\,o.s=s,\,o.p\le t}\operatorname{publishedAt}(o).\text{value}
\]

No observation after the declared effective availability time is selected for a decision. Late revisions are visible only after their declared admissible instant; equally timed contradictory claims are rejected. A source SHA256 proves byte identity, not vendor authenticity. Caller-supplied provider verification labels are not evidence: Research rejects an unauthenticated PROVIDER_ORIGIN_VERIFIED assertion until Markets has a real independent authentication consumer.

Let \(\mathcal C\) be the externally owned, consecutive monthly valuation endpoint series (one observable month-end closing session per month; not a daily trading calendar). The joint complete-case return observations are:

\[
G_s^{(t)}=\left(P_{1,s}^{(t)}/P_{1,s^-}^{(t)},\ldots,P_{d,s}^{(t)}/P_{d,s^-}^{(t)}\right)
\quad\text{with }s,s^-\in\mathcal C,\;s\le t.
\]

Missing calendar endpoints are explicitly excluded and counted: **no forward-fill or synthetic time-stretching**. The estimator preserves contemporaneous co-movement by resampling whole vectors rather than applying independent ETF marginals. The simplest coherent historical baseline is the empirical joint probability measure:

\[
\widehat{\mathbb P}_t=\frac{1}{n_t}\sum_{s\in\mathcal I_t}\delta_{G_s^{(t)}}.
\]

Identical vectors are aggregated with observed frequency weights. This is **unconditional, uncalibrated** historical research; it does *not* claim to estimate the true conditional law \(\mathbb P(R_{t+1},Z_{t+1}\mid\mathcal F_t)\). Future conditional-factor, regime and stochastic-volatility models must be compared against this baseline using prequential, strictly past-only forecasts.

## Conservative Markets ETF EOD capture -> Research PIT adapter

Reuse the Markets-owned admit_etf_eod_snapshot result with
etf_eod_capture_to_pit_vintages, rather than adding another provider,
source registry or research scheduler. The Markets admission checks
exact raw USD-cent bytes and digest, operator source/right/action references,
exchange session closes and capture/decision ordering; it does NOT authenticate
the operator's vendor, rights or market-calendar assertions.

The adapter uses captured_at as the effective Research published_at for
EVERY mark. Even if a historic row claims an earlier SOURCE_REPORTED
availableAt, an archive downloaded today cannot enter a past decision.
Revisions appear under their separate snapshot digests only after their
respective captures.

The currently admitted ETF snapshot excludes nonempty corporate action
events. The Research consumer therefore labels the prices as
RAW_UNADJUSTED_ACTION_FREE_DECLARED, distinct from the legacy
PROVIDER_ADJUSTED_CLOSE_UNATTESTED. This is an operator declaration of
an action-free interval, not verified dividend/split truth. The estimator
rejects a return interval mixing these bases; no silent raw/adjusted ratio.
The output forecast_evidence carries price_bases and source_standings
alongside training sessions and source digests. All projected ETF records
remain SECONDARY_VENDOR_NOT_ATTESTED.

The read-only adapter limits its float research values to exactly
representable integer USD cents, without changing Markets source limits;
no market/provider/Accounting write effects occur.

Mature reference semantics: Databento distinguishes ts_event and ts_recv
(https://databento.tech/docs/conventions/common-fields-enums-types);
LEAN distinguishes Raw and Adjusted normalization
(https://www.lean.io/docs/v2/lean-engine/class-reference/namespaceQuantConnect.html).

## Proper probability scoring

For a frozen forecast distribution \(F\) over joint gross-return vectors and subsequently realized outcome \(y\), the energy score is:

\[
ES(F,y)=\mathbb E\lVert X-y\rVert_2-\frac12\mathbb E\lVert X-X'\rVert_2.
\]

Lower is better; no arbitrary absolute score threshold is supplied. Evaluate across decisions only after the outcome is published, and preserve the forecast as originally known. The score measures distributional accuracy, **not** investment profitability. Use the same information time and observed outcomes to compare competing forecasters, and employ appropriate dependent-series uncertainty analysis before preferring a complex model.

## Real consumer, economic boundaries

`python -m ordivon_capital.research.pit_joint_forecast --input source-and-economic-contract.json` writes only an output JSON with:

- `optimizer_input`: **exact** `{"gamma":...,"nodes":[...]}` grammar consumed by `ordivon_capital.portfolio.multistage_policy` (first-period root plus terminal sample nodes).
- `forecast_evidence`: data timing, sample counts, duplicate aggregation, source digests, price bases, source standings and explicit uncalibrated status.
- `effects`: `NONE_NO_TRADE_NO_ACCOUNTING`.
- `input_sha256`: reproducible canonical input commitment.

The **caller must supply** risk aversion \(\gamma\), the cash and debt gross return for the horizon, broker initial margin, per-scenario maintenance margin, and turnover charges. No default 40% drawdown, leverage maximum, financing APR, fake broker rate, or investor utility exists. Scenario probability is estimated from observed historical joint vectors and is explicitly not forward validated. The output is a **research valuation tree**, never an executable at-the-same-close order.

The resulting `optimizer_input` can be passed unchanged to the already published `solve_multistage` Python JSON consumer; **do not create a second optimizer**. When the future model is truly multistage, a different research producer must provide a validated **conditional state-transition model**, not merely duplicate these one-month nodes across future months and pretend independent shocks are known.

## Human / Agent practices

**Human:** specify economic objectives rather than a chosen "safe" MDD percentage. Historical correlations, macro series revisions and published-at dates are distinct. Require actual source and broker credentials before treating research as prospectively actionable. An older revised price that is available today may be legally used today, but must not be inserted into a historical decision when it was not yet known.

**Agent:** reuse Capital/Markets for source/corporate-action rules and calendar; Capital/Research owns PIT vintage selection and the empirical baseline; Capital/Risk owns joint-tail diagnostics; Capital/Portfolio owns CRRA optimization; Capital/Trading owns actual broker contract; Capital/Accounting remains the single book. Unknown arrival/publication metadata is **UNKNOWN**, never guessed. Do not write to databases or trigger transactions from this research component. Correct detection of invalid publication times and duplicated indistinguishable scenarios is fundamental, not "overly cautious" specialized tests.

## Established external approaches

- Federal Reserve ALFRED: observation vintages and `realtime_start/realtime_end` time-revision semantics, https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- Gneiting & Raftery, *Strictly Proper Scoring Rules, Prediction and Estimation*, JASA 2007, https://doi.org/10.1198/016214506000001437
- Gneiting et al., energy score and multivariate probabilistic forecasts, https://doi.org/10.1198/016214506000001437
- Boyd et al., *Multi-Period Trading via Convex Optimization*, https://web.stanford.edu/~boyd/papers/cvx_portfolio.html
- Cvxportfolio published multi-period optimizer, https://www.cvxportfolio.com/en/stable/optimization_policies.html
- QuantConnect LEAN's actual brokerage/margin/fill-model boundaries, https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/trading-and-orders

**Verification command** (using Python standard library only):

```bash
python -m unittest discover -s domains/capital/tests -p test_pit_joint_forecast.py -v
```

Ordivon `mise run //domains/capital:verify` must additionally pass after integrating the module into the authoritative repository. No independently authenticated historical release-time data or real broker contract was provided with this standalone component; therefore historical portfolio outperformance remains **unproven**.

## Horizon consistency
Portfolio receives exactly one 1r contribution per month. The input forecast therefore MUST use consecutive monthly valuation endpoints, not daily/weekly gross returns or overnight financing. The data owner must independently certify the exchange-specific last-trading-session calendar and adjusted-price publication vintage. This is not a statistical guarantee.


## Conditional joint pilot and proper dependence falsification

The same existing input schema accepts an optional top-level
"forecast_method": "lagged_knn" (default "empirical"). It uses
k = ceil(sqrt(N)) previous complete consecutive monthly return transitions
matched by Euclidean distance on log-gross joint returns. The
conditioning month, eligible transitions and selected outcome sessions
are reported. The value of k is disclosed as a pilot heuristic, **not**
the result of validated hyperparameter selection. A missing latest
return or fewer than two lagged transitions fails rather than reverting
silently to unconditional probabilities.

Only information available at each historical decision timestamp enters
both models. Prequential energy score is a strictly proper distribution
score (under its moment assumptions); pairwise variogram score p=1 is a
proper complementary dependence diagnostic, not strictly proper on
its own. There is **no** guarantee of excess returns, conditional
calibration, margin realism, or ETF executable closes. Authenticate
vendor vintages before drawing economic conclusions. This reuses the
single existing multistage Portfolio consumer and changes no ledger
or live-execution authority.


For the one-step economic input, the caller can provide an explicit
broker-side "maintenance_by_asset" array when the same margin schedule
applies to every modeled return state. This eliminates the circular
requirement to know the forecast's scenario count before constructing
economic_contract. If the real brokerage requires different maintenance
by liquidation/volatility state, use the original per-scenario
"scenario_maintenance" matrix. Neither form supplies defaults.

## Prequential outcome-vintage consistency (same-clock realized returns)

The forecast is frozen at the actual decision time t and must use only
published-at-or-before-t vintages. Once the next month is observable, the
realized **retrospective adjusted-price** return is evaluated with both
endpoint prices selected at the SAME later information cutoff T:

\[
G^{(T)}_{i,s\to s+1}=
\frac{P_{i,s+1}^{(T)}}{P_{i,s}^{(T)}} ,
\qquad T>t,\quad
\widehat F_t\in\mathcal F_t.
\]

The earlier mixed-clock ratio
\(P_{i,s+1}^{(T)}/P_{i,s}^{(t)}\) was not invariant to
backward adjustment of both ETF closes after splits/dividends. It could
generate synthetic profits/losses despite unchanged economic holding-period
returns. The existing prequential and paired comparison consumers now
compute consistent same-T ratios and emit per-asset
reference_revision_evidence (frozen/evaluation closes, revision ratio,
both endpoint hashes, release times and source standing).

This is **retrospective scoring evidence only**, not the actually executable
share-account cash flow: Market Owner must certify corporate-action history,
adjustment convention, dividends and historical vendor release times.
Equal as-of selection does not itself authenticate normalization, and
revisions to genuinely erroneous prices can still change retrospective
outcome labels after the declared evaluation cutoff.

Native mature patterns to reuse rather than invent a new adjustment engine:
- QuantConnect LEAN raw/split-adjusted/total-return vs backward-adjusted
  normalization: https://www.lean.io/docs/v2/lean-engine/class-reference/py/QuantConnect/
- JPX J-Quants retroactive adjusted-price revision warning and raw-price /
  historical corporate-action reconstruction: https://jpx-jquants.com/en/spec/eq-bars-daily/adj
- CRSP holding-period returns and split/distribution factors:
  https://www.crsp.org/wp-content/uploads/guides/CRSP_Calculations_and_Index_Methodologies.pdf

Do not treat the scenario score as an investment P&L or evidence of alpha.
Historical data still require externally authenticated point-in-time
availability. Prefer existing Markets normalization/broker operators for
any future actual trading or settlement consumer.