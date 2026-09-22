# External Pull Worker Security R3

## Implemented

- Ed25519 verification uses cryptography; no custom cryptographic primitive.
- Private worker key never enters Gateway.
- Every worker request binds worker id, generation, timestamp, nonce, method, path and body digest.
- Nonces are durable and replayed requests fail closed.
- Worker replacement requires a higher generation.
- Revoked workers fail closed.
- Enrollment fixes an operator-admitted capability ceiling.
- Heartbeat may only advertise a subset of that ceiling.
- Attempts bind operation, worker, generation, lease id and expiry.
- Expired or superseded attempts cannot commit.
- Artifacts and events are idempotent only when bytes/payload agree.

## Explicit non-claims

Worker authentication is not AF-S2 northbound capability authorization.
Worker identity is not a Security Principal/Agent identity.
A successful worker result is not domain semantic completion or EffectAuthority.
Cloudflare authentication is not upgraded into per-capability authorization.

## Production edge requirement

The current interactive Cloudflare Access rail may require browser/OAuth before requests
reach Gateway. Muse needs a non-browser H3 route. Before production enrollment, create a
narrow edge policy for only the worker paths or an equivalent workload-native edge route.
The application signature remains required even if the edge permits those paths.

Enrollment bootstrap credentials must be scoped to enrollment, stored outside chat, rotated
or disabled after the ceremony, and never reused as a Gateway master credential.
