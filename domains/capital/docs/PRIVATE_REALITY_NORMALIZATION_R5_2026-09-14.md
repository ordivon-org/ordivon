# Private Reality Normalization R5 — 2026-09-14

R5 adopts an intentionally thin normalization layer over authoritative venue observer envelopes. It does not migrate the historical Finance VenueWorld/portfolio subsystem.

- Binance source truth remains the Spot USER_DATA observer / first-party SDK response.
- OKX source truth remains the fixed allowlisted private GET observer response.
- Market Capital maps only balances, positions, open orders, order history and fills into a small common read model.
- Permission standing is fail-closed: Binance requires Reading=true with Spot/withdraw permissions false; OKX requires an observed read-only permission string.
- The normalizer is a pure function: no credential reads, no sockets, no order APIs, no authority mutation.

The user has explicitly authorized use of the already located observer credentials, but fresh private-account permission verification has not graduated in the current tool environment. Therefore `privateAccountDataAllowed` remains false and the standing is `CREDENTIALS_LOCATED_PENDING_FRESH_PERMISSION_VERIFICATION`.
