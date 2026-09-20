# Crypto Public Shadow R2 — Persistent Streaming

R2 validates repeatable bounded public observation using persistent WebSocket market-data sessions rather than repeated REST/TLS setup.

## Mature transport boundary

- OKX: public `bbo-tbt` Level-1 channel for `BTC-USDT` and `ETH-USDT`.
- Binance: market-data-only `data-stream.binance.vision` combined `btcusdt@ticker` and `ethusdt@ticker` streams. The ticker stream supplies exchange event time plus best bid/ask.
- `aiohttp` is an explicit Market Capital dependency and is locked in `uv.lock`.
- Surfpath only qualifies fresh VPN reachability to each venue's public HTTPS surface. WebSocket availability is qualified by the actual streaming workload inside that same VPN session.

## Frozen acceptance protocol

One coherent snapshot is always retained as warm-up and excluded from acceptance. The next three snapshots are measured. An accepted snapshot requires all four streams to have advanced since the previous accepted snapshot, maximum exchange source-time span <= 1200 ms, and maximum local monotonic receive-time span <= 1200 ms. All three measured snapshots must pass.

Host wall clock is not used for R2 admission because the host clock is independently known to be outside the private-execution clock gate. Exchange source timestamps and monotonic receive timestamps define the public-observation cut.

R2 remains observational only: quote differences are not promoted to arbitrage, alpha, fill, fee, transfer, ownership, or execution claims. No credentials, private streams, execution clients, demo orders, or live orders are admitted.

## Superseded exploratory protocol

An uncommitted exploratory R2 used repeated public REST requests. It correctly failed because fresh TLS/request latency, especially to Binance through the VPN path, repeatedly exceeded the 1500 ms request gate. That experiment motivated moving R2 to the exchanges' mature persistent WebSocket market-data interfaces; its data is not counted toward R2 acceptance.

## Accepted run

Standing: `PASS_STREAMING_REPEATED_PUBLIC_SHADOW_WITH_WORKLOAD_FAILOVER`.

The accepted fresh route was `hk-hkg / openvpn-udp / native-a`. The persistent streaming session lasted about 4885.7 ms. One coherent warm-up snapshot was retained and excluded from acceptance. All three measured snapshots passed without changing the frozen 1200 ms limits.

Measured exchange source-time spans: 783 ms, 504 ms, and 609 ms. Measured local monotonic receive-time spans: 781.7 ms, 506.2 ms, and 610.1 ms. Host wall clock was not used for admission.

This graduates repeatable public streaming observation only. The independent private-execution clock gate remains failed and continues to block private account access and every order-capable lane.

