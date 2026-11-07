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

## Durable order-intent acceptance now enforced

Trading source postgres_demo_intent.PostgresDemoIntentStore uses native
PostgreSQL ordivon_capital.demo_order_intents, separately from Accounting
transfers. It uses transactional uniqueness, immutable SHA-256 canonical
content, and single-winner compare-and-set before any external POST.

Native CLI operation STAGE_INTENT (parameters matching DemoIntent fields)
and INSPECT_INTENT (top-level intentId) establish and read back the
durable operator state. Writes require the same intentId, exact
identity/economic match to PG, actual Governance Demo admission and
native Demo credentials. Claim is EFFECT_UNKNOWN until independently
resolved; neither a failed Runtime Job nor HTTP timeout proves no effect.
PLACE_LIMIT ACK records ordId; cancel has its own one-time uncertainty.

Physical PostgreSQL qualification uses a disposable PostgreSQL 18.6,
including exact replay, uniqueness collision, eight-way concurrent
single claim, restart/reopen readback and CLI-to-Governance no-write
consumer. This is not provider Demo transaction proof and does not
claim settled Accounting balance.

## Official upstream mechanics qualified at exact version 1.5.0

Official OKX Agent Trade Kit @okx_ai/okx-trade-cli 1.5.0 is the default
Trading transport, pinned in a scoped pnpm package and lockfile. It
replaces hand-written HMAC and HTTP mechanics in the default path,
while retaining the immutable PostgreSQL intent, Governance source and
existing Accounting ownership. The old local transport remains
--transport reference for differential fallback pending real Demo
account/order/fill and Accounting parity.

Physical local-protocol qualification used the actual installed official
Node executable with a controlled signed loopback HTTP endpoint. It
verified --demo --json --env, x-simulated-trading:1 and provider HMAC
for account/config, balance, order-by-clOrdId, cash-limit order, recent
fills, and cancellation. The official order body includes tag=CLI and
banAmend=false, which differ from the original minimal local wire but
do not prove changed economic or settlement behavior.

The official client currently does not retry ordinary POST automatically.
Ordivon still treats any ambiguous provider response as effect UNKNOWN.
The exact credential file is read from Runtime's CredentialAuthority
and passed through the official CLI's documented native environment
credential interface for that single child process. The temporary
isolated HOME contains no persisted API credentials; no TOML credentials
are written to disk or tmpfs. Secrets do not go into Git, argv,
global user configuration or output receipts.

In domains/capital, install with mise run provider:okx:install and
qualify with mise run verify:provider:okx-official. These checks
are NOT a Demo order or account authorization receipt.
