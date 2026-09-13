# Market Capital Clean-Room — Wave B / M4 Acceptance

Date: 2026-09-13

## Standing

**PASS_BOUNDED_FIX44_ORDER_SEMANTICS**.

M4 inserts standard FIX order semantics between LEAN's pre-trade sizing decision and the bounded LEAN execution path without introducing a second sizing or execution engine.

## Standard and implementation

- protocol: FIX 4.4;
- application message: `NewOrderSingle`, MsgType `D`;
- library: QuickFIX/n `1.14.1`;
- packages: `QuickFIXn.Core 1.14.1` and `QuickFIXn.FIX44 1.14.1`;
- order type: Market (`40=1`);
- time in force: Day (`59=0`);
- sender semantic endpoint: `ORDIVON_SHADOW`;
- target semantic endpoint: `LEAN_VALIDATION`;
- session network: disabled.

The package dependency graph is committed through `packages.lock.json`, and locked restore succeeds. NuGet's current vulnerability audit reports no vulnerable packages for this adapter project.

## Proven chain

`Wave A target -> LEAN buying-power sizing -> QuickFIX/n FIX 4.4 NewOrderSingle -> deterministic ClOrdID/message digest -> exact FIX-to-LEAN order link -> LEAN fill -> resulting portfolio`.

The FIX message is not sent to a broker or venue. It is a standard semantic order-intent object used to remove the previous direct `target -> MarketOrder` semantic gap.

## Exact bounded evidence

Provider-origin historical data remains the M3 Nasdaq 2026-09-01..2026-09-11 non-causal validation interval.

Three FIX intents were produced and linked one-to-one to LEAN fills:

- AAPL: quantity 101, side Buy, `35=D`, `40=1`, `59=0` -> LEAN order 1 -> fill quantity 101.
- MSFT: quantity 65, side Buy, `35=D`, `40=1`, `59=0` -> LEAN order 2 -> fill quantity 65.
- NVDA: quantity 151, side Buy, `35=D`, `40=1`, `59=0` -> LEAN order 3 -> fill quantity 151.

Each FIX message has a deterministic `ClOrdID` derived from the exact target portfolio digest, event time, symbol and signed quantity, plus a SHA-256 of the serialized QuickFIX/n message.

## Runtime integration boundary

LEAN loads algorithms from memory, so the algorithm assembly has no reliable filesystem `Assembly.Location`. M4 therefore does not copy third-party DLLs into the pinned LEAN installation and does not replace LEAN's Composer directory. The M4 runner explicitly binds the algorithm output directory through `MARKET_CAPITAL_FIX_ASSEMBLY_DIRECTORY`; a narrow assembly resolver admits only the expected QuickFIX/n and Microsoft abstraction dependencies.

## Authority boundary

- no FIX network session;
- no broker target;
- no broker credential;
- no venue write;
- no external financial write;
- no live authorization.

M4 closes FIX order semantics only. It does not claim paper/live brokerage connectivity or execution authority.
