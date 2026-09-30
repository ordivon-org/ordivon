# X Reality consumer network profile

This consumer owns transport authority only for `https://api.x.com:443`. It exposes `127.0.0.1:19681` as an HTTP proxy and lowers admitted traffic through the single Network v2 shared provider carrier at `10.252.246.2:19680`. Unknown destinations are rejected and there is no direct fallback.

Authentication is a separate authority. This Network consumer does not read, materialize, forward, inspect, fingerprint, or expose Bearer/OAuth credential bytes and does not claim a user-context principal. An unauthenticated `GET /2/users/me` returning HTTP 401 is the bounded transport consequence used for readiness; it is not an authentication attempt or principal proof.

Historical continuity remains `task:ordivon-x-reality-source-connector-20260904`. The prior network blocker is satisfied only when this exact bounded route is live; app-only Bearer binding and user-context OAuth remain separate owner work.
