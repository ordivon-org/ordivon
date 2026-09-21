# websockets comparative qualification R1 — 2026-09-21

## Exact contract

The active contract is an async public WebSocket client for OKX and Binance through exact
Network v2 HTTP proxy bindings. Required mechanics include the WebSocket handshake, TLS,
framing, control frames, Ping/Pong, Close, bounded message size, and async message delivery.

Venue JSON semantics, quote normalization, health policy, reconnect policy, evidence, and
Network v2 route selection are not owned by the WebSocket library.

## Current candidate

websockets 17.1 is installed on canonical Python 3.14.7. It has no third-party runtime
dependencies in the installed metadata and an installed footprint of about 830 KB.

The current code uses the documented asyncio client API with explicit proxy, open timeout,
Ping/Pong interval and timeout, close timeout, and 1 MiB max message size.

## Local baseline question

Python 3.14 provides asyncio, TLS, sockets, and HTTP primitives but no contract-equivalent
WebSocket client. A credible local replacement would need to implement and maintain the
WebSocket handshake, framing/masking, control-frame rules, fragmentation behavior,
connection closure, proxy integration, and protocol error handling. A raw-socket toy is
therefore not a contract-equivalent baseline.

Unlike the bounded FIX projection, there is no small local composition that passes the same
semantic gate while materially reducing the trusted surface.

## Runtime evidence

Historical live evidence already records successful dual-venue public streaming and injected
disconnect/reconnect qualification.

The first fresh 2026-09-21 rerun failed simultaneously on both venue paths. Network v2
sing-box logs identified the common root cause as DNS lookup failure for ws.okx.com and
data-stream.binance.vision (context deadline exceeded / EOF), not WebSocket framing or venue
payload handling. Subsequent HTTP CONNECT + TLS checks passed for both authorities.

After DNS recovery, fresh R2 streaming passed again. Fresh R3 reconnect qualification also
passed after repairing two runner defects: the session runner now uses the canonical
run-capability-python module path, and both venues are always attempted and aggregated even
when one returns nonzero. After the dual-provider DNS response-race remediation and hardened transport binding, the latest clean run reconnected OKX in about 689.3 ms and Binance in about 5826.4 ms; both recovered on generation 2, passed recovery, and completed all three measured rounds with zero connection-error events. The evidence binds the live egress bytes (sha256:6be738...) and protected provider-endpoint bytes by digest without disclosing endpoint secrets. An earlier post-deployment run reached PASS but took 19.66 s / generation 4 for Binance; it is retained as transient-outlier evidence rather than discarded.

The audit also fixed an Ordivon error-attribution defect: a queue timeout could mask a
completed reader task's real exception. The streaming loop now re-checks reader tasks and
propagates the underlying connection failure.

## Decision

Retain websockets 17.1 as the narrow implementation owner for WebSocket protocol/client
mechanics. Do not expand that ownership to venue payload semantics, reconnect policy,
Network v2 routing, or execution authority.
