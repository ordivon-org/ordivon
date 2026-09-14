# Private Reality Read-Only Preflight — 2026-09-14

## Standing

`PASS_COMPONENT_SURFACE_PREPARED_CREDENTIALS_NOT_ADMITTED`

The next Market Capital boundary is authoritative private account/order/trade reality, but no credential is admitted yet.

## Composition

### OKX

Use the already-installed NautilusTrader `OKXHttpClient` for the read path. The installed 2.0.0rc4 client exposes the required read surfaces directly: balance, account state, order status reports, fill reports and trades. The future credential must be **Read** only; Trade and Withdraw are forbidden for this admission.

### Binance

Use Binance's official `binance-sdk-spot`, pinned externally at version 11.3.0. The installed SDK directly exposes account, open-order, order-history, trade-history and single-order query methods. The future credential admission is USER_DATA only; TRADE is not required and remains forbidden.

## Why asymmetric

There is no value in forcing both venues behind one custom client. OKX already has a qualified mature client inside the selected Nautilus runtime. Binance has a current first-party generated SDK with the exact account/order/trade query surface needed. Market Capital should normalize their returned state, not replace either client.

## Security boundary

While `credentialUseAdmission=NOT_ADMITTED`:

- no API key, secret or passphrase may be read;
- no ambient environment, config file, shell history or local secret store may be searched for credentials;
- no private venue endpoint may be called;
- no TRADE or Withdraw permission is admitted;
- no demo/live order may be submitted.

The preflight checker instantiates only blank/no-credential client surfaces and performs no network call.

The next step requires separate explicit user authorization for **read-only** credentials. That authorization would not grant order submission.
