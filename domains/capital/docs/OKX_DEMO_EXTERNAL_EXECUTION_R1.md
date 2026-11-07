# OKX Demo external execution — current operational boundary

Canonical consumer: trading.okx_demo_execution.OkxSpotDemoClient and
scripts/run-okx-demo-execution. Supports Demo-only SPOT cash limit orders,
order-by-ordId, recovery-by-clOrdId, recent fills, cancel, account config,
and balance. Reuses the current read-only client's HMAC signing, not a
second OMS. Requests always carry x-simulated-trading: 1. Redirects
carrying authenticated headers are disabled; origins are HTTPS OKX hosts.

## Human first exercise

1. Qualify an API key generated in OKX Demo, in an appropriate region,
   on the actual Demo account and supported SPOT instrument.
2. Read account config/balance through a versioned request:
   {"schemaVersion":1,"operation":"ACCOUNT_CONFIG","parameters":{}}
   Execute through credential-bound Runtime; do not put secrets in requests.
3. Determine actual lot size, tick size, spendable cash, fees, account mode.
   Freeze the exact limit intent, get Risk/Governance approval and store
   it in the natural PostgreSQL owner before an external write.
4. After policy/provider admission, PLACE_LIMIT using instrument_id,
   side, size, limit_price, client_order_id. Query resulting order,
   fills, and cancellation; then read back PG and external balances.
   The operator itself never chooses a position or order size.

## Agent recovery and authority

The systemd credential directory must contain separate Demo names:
okx_demo_api_key, okx_demo_secret_key, okx_demo_passphrase. Use existing
Runtime LoadCredentialEncrypted/credential bound tools.

The CLI denies order/cancel unless Governance declares current admitted
Demo policy, with credential binding, network session and write admission.
Default PREPARED_NOT_ADMITTED is intentionally not upgraded without
actual account/provider observations.

After uncertain POST, preserve UNKNOWN and do read-only
RECOVER_UNKNOWN_PLACE with the persisted clOrdId; never resubmit it
just because an HTTP or Runtime Job failed. OKX can reuse a clOrdId
after an order finishes, and its lookup returns the latest matching
order. An observed row therefore needs correlation with the precise
frozen intent and independent venue order identity/time/fill facts.
Even a cancellation ACK does not establish final cancellation.
GET /api/v5/trade/fills is recent-history only, so empty rows cannot
prove a completed order never traded.

## Source versus external business effect

Focused tests cover Demo HMAC request bytes, bound URL, provider order ID,
negative/mismatched recovery, unknown POST effects, cancellation semantics,
and the default Governance admission gate. Successful mocks/test runs do
not prove external provider authorization, real Demo orders or PG settlement.
Runtime process success is distinct from authority, custody and business
semantic completion.

Official provider reference: https://www.okx.com/docs-v5/en/
(Place order, Cancel order, Order details, Transaction details, Demo).
