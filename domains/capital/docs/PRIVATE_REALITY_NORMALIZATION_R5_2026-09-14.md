# Private Reality Normalization R5 — 2026-09-14

R5 adopts an intentionally thin normalization layer over authoritative venue observer envelopes. It does not migrate the historical Finance VenueWorld/portfolio subsystem.

- Binance source truth remains the Spot USER_DATA observer / first-party SDK response.
- OKX source truth remains the fixed allowlisted private GET observer response.
- Market Capital maps only balances, positions, open orders, order history and fills into a small common read model.
- Permission standing is fail-closed: Binance requires Reading=true with Spot/withdraw permissions false; OKX requires an observed read-only permission string.
- The normalizer is a pure function: no credential reads, no sockets, no order APIs, no authority mutation.

The Owner Principal mandate already authorizes use of the explicitly bound observer credentials for read-only private-Reality observation. That mandate is separate from provider permission/currentness: `credentialPermissionStanding=PENDING_FRESH_PROVIDER_VERIFICATION`, `privateAccountDataAdmission=NOT_ADMITTED`, and `privateAccountDataAllowed=false` remain current until fresh provider-native permission verification succeeds. The combined historical standing `CREDENTIALS_LOCATED_PENDING_FRESH_PERMISSION_VERIFICATION` is retired from current semantics.
