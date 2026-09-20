# Private Reality Read-Only Preflight — 2026-09-14

## Standing

`OWNER_MANDATE_PRESENT_PERMISSION_NOT_CURRENT`

The Owner Principal has already authorized use of the explicitly bound read-only observer credentials for private-reality observation. What is not current yet is provider permission standing; private account data remains unadmitted until that provider-native permission/currentness check succeeds.

## Composition

### OKX

Use the already-installed NautilusTrader `OKXHttpClient` for the read path. The installed 2.0.0rc4 client exposes the required read surfaces directly: balance, account state, order status reports, fill reports and trades. The future credential must be **Read** only; Trade and Withdraw are forbidden for this admission.

### Binance

Use Binance's official `binance-sdk-spot`, pinned externally at version 11.3.0. The installed SDK directly exposes account, open-order, order-history, trade-history and single-order query methods. The future credential admission is USER_DATA only; TRADE is not required and remains forbidden.

## Why asymmetric

There is no value in forcing both venues behind one custom client. OKX already has a qualified mature client inside the selected Nautilus runtime. Binance has a current first-party generated SDK with the exact account/order/trade query surface needed. Market Capital should normalize their returned state, not replace either client.

## Security boundary

The current state is intentionally split:

- `ownerCredentialUseMandate=AUTHORIZED_READ_ONLY_PRIVATE_REALITY_OBSERVATION` records the Owner Principal mandate;
- `credentialPermissionStanding=PENDING_FRESH_PROVIDER_VERIFICATION` records that provider-native permission currentness has not yet graduated;
- `privateAccountDataAdmission=NOT_ADMITTED` prevents those observations from becoming current Market Capital private Reality before verification.

Ambient credential discovery remains forbidden. Only the explicitly bound observer credentials may be used for the bounded provider-permission verification/read path; executor credentials remain excluded. No TRADE or Withdraw authority is inferred from the owner mandate, and no demo/live order may be submitted.

The preflight checker itself still instantiates only blank/no-credential client surfaces and performs no network call. The next missing step is fresh provider-native permission verification, **not another Human/user approval**.
