# Crypto Public Shadow R1

This milestone qualifies a repeatable public-data observation path for OKX + Binance Spot without account access or order submission.

The runner performs a fresh scoped Surfshark discovery for both exchange targets, selects one point-in-time qualified Singapore OpenVPN-TCP path, captures OKX/Binance public REST data concurrently inside that single VPN session, and evaluates observation quality using monotonic request intervals.

Cross-venue price comparison is admitted only when the three price-request uncertainty intervals overlap, maximum request RTT is <= 1500 ms, and the two exchange server-time offset estimates agree within 250 ms. The comparison is explicitly observational: it is not an arbitrage, fill, fee, latency, transfer, or execution claim.

Host wall-clock quality is a separate gate. A host/exchange offset above 1000 ms does not invalidate monotonic public shadow observation, but blocks future private/demo/live execution qualification until corrected or otherwise proven safe.

## First accepted run

Standing: `PASS_BOUNDED_DUAL_VENUE_PUBLIC_SHADOW_HOST_CLOCK_WARN`.

- price-request common intersection: about 684 ms;
- full price-request union: about 824 ms;
- maximum price-request RTT: about 824 ms;
- OKX/Binance server-time offset estimates agree within about 11.5 ms;
- host wall clock is about 2.20 seconds ahead of the exchange clocks.

Therefore bounded contemporaneous public quote comparison is admitted, while private/demo/live execution remains blocked by the host-clock gate. Observed gross cross-venue differences are retained only as quote observations and are not interpreted as executable arbitrage.

