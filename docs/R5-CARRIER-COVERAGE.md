# Distribution v2 R5 — Real Carrier Coverage

R5 changes the optimization target from control-plane abstraction to vertical carrier proof.

A carrier is counted as covered only when the local environment can execute the relevant lane and obtain provider-native readback. An external project's advertised support is not counted as Ordivon-local coverage.

## GitHub provider-native lane

Current local credential capability is sufficient to read the target repository and has authenticated `push/admin` capability. Exact-effect authority still blocks the proposed `create_issue` write.

Provider-native readback is now separately proven against an existing real issue (`ordivon-org/ordivon-runtime#72`). The readback test addresses the provider object by number and verifies stable provider identity (`id`, `node_id`, `number`). This is the acceptance pattern for a future bounded write: the create response must return provider object identity, and an independent GET must resolve the same identity. HTTP success alone is insufficient.

## rclone remote lane

`rclone` is installed and local copy/check works, but `rclone listremotes` returns no configured remote. Therefore remote/object/cloud distribution is not currently proven and is blocked on provisioning one real remote authority/configuration.

## Postiz social lane

The Postiz public API surface is reachable and correctly rejects unauthenticated integrations requests, but no Postiz API credential or local Postiz service was observed. Consequently no connected social integration is visible and no social publish/readback claim is admitted.

Postiz upstream platform breadth is substrate capability only; it does not become local Distribution coverage until a connected integration is observed and a bounded publish/readback episode succeeds.

## YouTube native lane

No YouTube OAuth installed/web credential or authenticated upload identity was observed. Five `google*.json` files exist, but their safe structure is generic provider/model API-key configuration rather than YouTube OAuth. YouTube upload is therefore blocked before admission to any external write.

## R5 rule

Coverage requires:

`local identity/config -> exact intent -> authority -> provider dispatch -> provider object identity -> provider-native readback -> reconciliation standing`.

Anything shorter is capability discovery, not carrier coverage.
