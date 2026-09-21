# QuickFIX/n comparative qualification R1 — 2026-09-21

## Exact contract

The active Market Capital contract is not a FIX session engine. It is a mechanics-only,
sessionless projection of one legacy FIX 4.4 NewOrderSingle field sequence.

The semantic owner remains FIX Trading Community FIX Latest / FIX Orchestra. FIX 4.4 is
only the explicitly retained legacy profile for this qualification surface.

## Current external candidate

QuickFIX/n 1.14.1 is current in the local qualification environment, targets net10.0, builds
with .NET SDK 10.0.401, and the current NuGet vulnerability scan reports no known vulnerable
packages.

Its sessionless Message.ToString output for this use does not emit BodyLength tag 9 or
CheckSum tag 10. Therefore the current Ordivon use is not complete FIX wire framing.

The built QuickFIX assemblies used by the projector are approximately 3.5 MB before the
additional logging/dependency-injection abstractions.

## Differential

A local deterministic projector was compared byte-for-byte against QuickFIX/n 1.14.1 on
120 cases spanning:

- BUY and SELL;
- DAY, GTC, and IOC;
- multiple decimal scales;
- multiple symbols and destinations;
- sequence numbers;
- timestamps with sub-second precision.

Result:

- byte-exact matches: 120 / 120;
- mismatches: 0.

## Decision

The local bounded projector owns the exact current sessionless projection contract.
QuickFIX/n is retained as a differential oracle, not a canonical runtime dependency.

This does not generalize to a real FIX session. If a future contract requires BodyLength,
CheckSum, socket/session transport, resend/sequence recovery, dictionary negotiation,
multiple message types, or counterparty Rules of Engagement, reopen qualification and
prefer a mature FIX engine unless a new comparison proves otherwise.
