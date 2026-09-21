# Provider-client comparative qualification R1 — 2026-09-21

## Authority split

OKX and Binance APIs own private account, permission, order, fill, position, and risk truth.
A client library or CLI only implements transport/signing/request mechanics and cannot become
the owner of provider facts.

## OKX current authenticated read contract

The implementation-qualification contract contains exactly three authenticated GET operations through the
frozen Network v2 OKX REST authority. The exercised credential is the live-trade provider credential, so this
contract is a provider-capability audit and not private-Reality observer admission:

- account configuration;
- trading-account balance;
- open Spot orders.

The previous implementation used @okx_ai/okx-trade-cli 1.4.7. That package is current,
MIT-licensed, and its production dependency audit reports zero vulnerabilities, but it also
contains broad place/cancel/amend/leverage and other financial-write command surfaces.

A Python 3.14 stdlib baseline was therefore qualified. It implements only the three admitted
GET endpoints plus OKX HMAC-SHA256 authentication and HTTPS-over-proxy.

Comparative evidence:

- synthetic HMAC signing cases: 120;
- signing mismatches versus Node crypto / OKX CLI formula: 0;
- live authenticated GET methods compared: 3;
- live structural mismatches: 0;
- account-config row count: 1 vs 1;
- balance row count: 1 vs 1;
- open Spot order count: 0 vs 0;
- provider permission sets matched;
- response field sets matched;
- no sensitive values were emitted;
- no external financial write was attempted.

Decision: use the local bounded GET-only client for this provider-capability audit. Keep the OKX CLI as a differential/reference
client. Provider truth remains OKX. Because the audited credential carries Trade permission, it is not promoted into the
private-Reality observer lane; the dedicated observer credential remains pending fresh provider-permission verification.

## Binance current standing

Binance Spot 11.3.0 and Binance USD-M 17.4.0 plus Wallet 13.4.0 pass current method-surface
preflights in isolated environments, but those preflights load no credentials and perform no
network calls.

Private account-data admission remains NOT_ADMITTED for Spot and pending for USD-M. Therefore
the SDKs are candidates, not current implementation owners. Method existence is qualification
evidence, not adoption.

When a Binance private-read contract is actually admitted, compare the official SDK with the
smallest credible GET-only signing/client baseline under the same provider responses and
failure semantics before choosing the implementation owner.
