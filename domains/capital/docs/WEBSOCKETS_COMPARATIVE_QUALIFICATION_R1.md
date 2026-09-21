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

## HTTP-proxy TLS lifecycle hardening — 2026-09-21

Canonical Network v2 WebSocket access uses websockets through exact loopback HTTP
CONNECT authorities. During canonical-path supersession acceptance, an unstable proxy/TLS
opening path reproduced upstream python-websockets issue #1629: ClientConnection.connection_lost()
can run after the HTTP proxy transport has been handed to the WebSocket protocol but before
connection_made() initializes recv_messages and transport.

The current upstream 17.1 implementation and upstream main both retain the ordering:

1. establish HTTP CONNECT tunnel;
2. construct ClientConnection;
3. hand the transport to the connection protocol;
4. perform asyncio TLS upgrade;
5. only after TLS succeeds, call connection_made().

Therefore a TLS/transport loss between steps 3 and 5 can invoke callbacks against a
partially initialized connection. This isn't a WebSocket framing responsibility and isn't
specific to Ordivon's synthetic disconnect.

Ordivon uses the library's documented create_connection extension point with
NetworkV2ProxyClientConnection. The subclass guards only connection_lost() and
eof_received() before connection_made(); once connection_made() occurs, all lifecycle
and protocol mechanics delegate unchanged to upstream 17.1. No site-package monkey patch,
vendored fork, protocol framing implementation, or deadline relaxation is admitted.

Qualification evidence:

- unit tests exercise pre-connection_made loss and EOF plus the normal upstream path;
- the R3 35-second reconnect contract remains unchanged;
- a fresh post-guard R3 run passed OKX at 803 ms / generation 2 and Binance at 5.67 s /
  generation 2 with zero connection errors and three measured rounds per venue;
- a five-round opening-handshake soak through exact Network v2 proxies passed 5/5 for each
  venue; maximum observed opening latencies were approximately 1.07 s for OKX and 1.38 s
  for Binance;
- a separate stress run later encountered ambient opening-handshake tail latency before
  the synthetic fault was injected. R3 evidence was corrected so ambient generations
  cannot be recorded as post-injection reconnect generations. The global 35-second
  deadline was not increased.

External owner standing remains websockets 17.1: Ordivon owns only this narrow lifecycle
seam, venue payload normalization, qualification policy, and evidence. Requalify and delete
the guard when upstream removes the pre-connection_made callback hazard.
