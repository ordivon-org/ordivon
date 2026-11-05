# X Reality consumer network profile

This consumer owns transport authority only for `https://api.x.com:443`. It exposes `127.0.0.1:19681` as an HTTP proxy and lowers admitted traffic through the single Network v2 shared provider carrier at `10.252.246.2:19680`. Unknown destinations are rejected and there is no direct fallback.

Authentication is a separate authority. This Network consumer does not read, materialize, forward, inspect, fingerprint, or expose Bearer/OAuth credential bytes and does not claim a user-context principal. An unauthenticated `GET /2/users/me` returning HTTP 401 is the bounded transport consequence used for readiness; it is not an authentication attempt or principal proof.

The selected physical carrier Owner is the Gluetun adapter
(network-v2-gluetun-owned-adapter.service), not the inactive legacy
Browserless WireGuard provider. The Network namespace retains its
historical nv2-browserless-prod identifier; that identifier does not
authorize a second WireGuard identity. No fixed providerSite is part of
the current X Reality policy.

The previous fault-smoke used systemctl stop/start on an obsolete
shared Browserless carrier, while the real network used the Gluetun
adapter; it could not prove failure of the selected physical carrier and
was removed from source and the installed libexec tree. Native real
positive/negative sing-box proof is owned by the Network egress
acceptance; X Reality readiness does not require credential access.

Historical continuity remains `task:ordivon-x-reality-source-connector-20260904`. The prior network blocker is satisfied only when this exact bounded route is live; app-only Bearer binding and user-context OAuth remain separate owner work.
