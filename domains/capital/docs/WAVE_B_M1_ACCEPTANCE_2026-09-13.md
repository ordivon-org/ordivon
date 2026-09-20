# Market Capital Clean-Room — Wave B / M1 Acceptance

Date: 2026-09-13

## Standing

**PASS_BOUNDED_HISTORICAL_FIXTURE** — the first external trading-engine slice is operational with no broker credentials and no external financial writes.

## Admitted engine

- QuantConnect LEAN tag `18074`.
- GitHub source commit `8ee075a39918f2df6fe9e0a5944e366fb60d10dc`.
- Source tarball SHA-256 `a1a87dd28d610f08204f23442dbb6f9ca51c1a97db6510e828946d5d5a067a24`.
- Local .NET SDK `10.0.112`.
- LEAN engine reports v2.5.0.0 RELEASE.

Docker Hub transport was unavailable from the current host, so M1 admits the exact tagged upstream source build rather than depending on QuantConnect CLI/SaaS or an unpinned container pull.

## Proven chain

`Wave A research-gated target portfolio -> LEAN BacktestingBrokerage -> BacktestingTransactionHandler -> orders -> fills -> fees -> modeled slippage -> resulting holdings/portfolio state`.

The exact Wave A target fixture SHA-256 is `137265667683455c302adff94466eaf38444ed7d51b5959c4ad065505792c14d`.

Validation data for AAPL/MSFT/NVDA is deterministic synthetic fixture data and is explicitly **not market truth**. LEAN's upstream SPY sample and interest-rate sample are used only for engine/statistics auxiliary inputs.

## Execution evidence

- AAPL: 332 shares filled at 100.8055552896; fee USD 1.66.
- MSFT: 664 shares filled at 50.3110885344; fee USD 3.32.
- NVDA: 1329 shares filled at 25.32234294865; fee USD 6.645.
- Total fees: USD 11.63.
- Slippage model: `VolumeShareSlippageModel(0.30, 0.05)`.
- Fill model: `EquityFillModel`.
- Fee model: `InteractiveBrokersFeeModel`.
- Data requests: 5 succeeded / 0 failed.
- Engine errors: 0.
- Order list hash: `81ddc01794082b9eba9424f59bcbe701`.

## Important finding: target feasibility is not execution feasibility

The Wave A target has gross exposure 1.0 and cash weight 0.0. Orders are sized from the decision-time prices, while fills occur at later prices and incur fees/slippage. The resulting M1 account therefore ends with negative cash under a margin account. This is not hidden or normalized away.

Wave B / M2 must add a pre-trade feasibility/sizing gate that consumes buying power, fees, fill/slippage assumptions and a configured cash buffer before orders are emitted. A target portfolio is an intention, not a guaranteed feasible order set.

## Supply-chain boundary

The upstream LEAN build completed successfully, but NuGet emitted known vulnerability warnings for legacy upstream packages, including critical/high advisories. M1 is therefore admitted only for isolated historical validation. Production/live admission requires a separate dependency/security review or a newer upstream pin that closes the relevant findings.

## Authority boundary

- broker credentials: forbidden / unused;
- live brokerage: not configured;
- external financial writes: none;
- production authorization: not granted.
