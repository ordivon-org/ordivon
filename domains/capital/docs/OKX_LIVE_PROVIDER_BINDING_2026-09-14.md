# OKX LIVE provider binding — 2026-09-14

> **Historical qualification notice — 2026-09-21:** this document preserves the 2026-09-14 binding evidence. Current OKX capability audit uses the bounded Python 3.14 GET-only client and does not execute Nautilus rc4. The Nautilus live config is now an unadmitted candidate reference only; see config/okx_live_provider.json, config/candidate_tool_surface_registry.json, and docs/ARCHITECTURE.md.


## Standing

`PASS_OKX_LIVE_PROVIDER_BOUND_CURRENT_NO_EFFECT_ADMISSION`

Market Capital now binds the existing owner-authorized OKX LIVE API credential directly from the unified secret root rather than from the retired Finance repository.

Current provider evidence proves:

- Network v2 scoped OKX REST authority is current and reachable at `openapi.okx.com` through `127.0.0.1:19283`.
- `@okx_ai/okx-trade-cli` 1.4.7 successfully performs authenticated private `account config` and `account balance` queries.
- The current provider permission set is `read_only + trade`; `withdraw` is absent.
- The private open-orders query is current.
- NautilusTrader 2.0.0rc4 constructs an OKX `LIVE` execution client configuration from the same external credential binding, `openapi.okx.com`, and the same scoped Network v2 proxy.

No credential bytes are stored in the repository. The canonical binding is:

`/root/.config/ordivon/secrets/okx/live-trade/config.toml`

## Authority boundary

Provider capability and Market Capital effect admission are separate facts:

```text
OKX provider Trade permission          = CURRENT
OKX authenticated private API          = CURRENT
Nautilus LIVE execution config          = BOUND
ExternalFinancialWriteAdmission         = NOT_ADMITTED
orderSubmissionAllowed                  = false
withdrawalAllowed                       = false
transferAllowed                         = false
```

Binding an order-capable credential is therefore allowed for capability/currentness qualification, but no order-submitting runner may consume it until a separate external-effect admission exists.

## Fresh verification

Run:

```text
scripts/check-okx-live-provider-binding --output evidence/okx-live-provider-binding-20260914.json
```

The probe contains private GET/currentness checks and execution-client configuration construction only; it does not contain a place/cancel/amend/transfer operation.
