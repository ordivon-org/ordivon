# finance-okx consumer profile

This directory contains the network policy and migration artifacts for the `finance-okx` consumer. It is deliberately outside generic Network core.

Consumer-specific semantics include:

- two admitted provider paths;
- no direct fallback;
- exact destination fencing for the OKX public endpoint;
- all-provider loss fails closed;
- persistent production systemd lifecycle after explicit authority cutover.

Network v2 is the intended production network authority. Consumer cutover is explicit and must bind the exact source-owned authority contract before legacy transport retirement.

Historical R5/R6/R7 evidence is preserved under `history/`.

## Production authorities

The production target exposes two independent, fail-closed loopback HTTP CONNECT authorities over the same provider A/B WireGuard carriers:

- REST: `http://127.0.0.1:19283`, `openapi.okx.com:443`, authority `config/authority.json`, urltest group `finance-okx-auto`.
- WebSocket: `http://127.0.0.1:19288`, `ws.okx.com:8443`, authority `config/ws-authority.json`, urltest group `finance-okx-ws-auto`.

Route rules are inbound-tag fenced, so the REST proxy cannot reach the WS destination and the WS proxy cannot reach the REST destination. Neither authority has direct fallback. Both reuse the same provider A/B namespaces, WireGuard tunnels, and carrier proxies; only destination selection/health is independent.
