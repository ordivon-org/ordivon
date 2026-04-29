# Finance Observation — Red-Team Closure (Phase 6Z)

Status: **PUBLISHED** (Phase 6Z)
Date: 2026-04-29
Phase: 6Z
Tags: `red-team`, `closure`, `finance`, `observation`, `alpaca`, `paper`, `security`, `exposure`

## 1. Purpose

This document records the red-team review of the Ordivon Finance Observation layer
as built through Phases 6G–6L. It identifies threat vectors, assesses mitigations,
and declares which are CLEARED and which require future attention.

## 2. Red-Team Vector Matrix

### Vector 1: Paper equity mistaken as real money

**Threat**: An operator or downstream system treats Alpaca Paper simulated
balance ($100,000) as real capital, leading to incorrect risk calculations or
false confidence.

**Mitigation**:
- `environment` field hardcoded to `"paper"` in all responses
- Health endpoint response always includes `environment: "paper"`
- `/finance-prep` displays "Paper account only — not live trading"
- Stage summit explicitly states equity is simulated
- `ReadOnlyAdapterCapability.adapter_id = "alpaca-paper"`

**Verdict**: CLEARED.

---

### Vector 2: Health endpoint mistaken as broker control plane

**Threat**: An operator or external system treats `GET /health/finance-observation`
as a broker API endpoint capable of placing orders, cancelling orders, or
modifying account state.

**Mitigation**:
- Endpoint only responds to GET — no POST/PATCH/PUT/DELETE routes exist
- Response includes `write_capabilities: []`
- Response includes `environment: "paper"`
- Route is in the health router, not a finance/trading router
- No order-related fields in response

**Verdict**: CLEARED.

---

### Vector 3: Provider connected mistaken as trade-enabled

**Threat**: The UI shows "PROVIDER CONNECTED" (or similar) and an operator
infers that trading is possible through this connection.

**Mitigation**:
- Phase 6J-S changed `"connected"` → `"configured"` for static preview state
- `"connected"` variant only used when live runtime health read succeeds
- ProviderStatusBanner always states "No orders can be placed"
- AdapterCapabilityTable shows 4 BLOCKED write capabilities
- DisabledHighRiskAction for Place Live Order persists regardless of provider status

**Verdict**: CLEARED.

---

### Vector 4: Account alias exposure

**Threat**: Full Alpaca account ID (e.g., `PA37AKH0E5AT`) is exposed in API
responses or rendered UI, enabling account enumeration or impersonation.

**Mitigation**:
- `get_alpaca_health_snapshot()` masks account ID server-side: `PA37****E5AT`
- Short IDs (< 8 chars) also masked
- Frontend test verifies full ID is not in rendered HTML
- `FinanceObservationHealthResponse` schema field is `account_alias: str` (already masked)

**Verdict**: CLEARED.

---

### Vector 5: Secret exposure

**Threat**: Alpaca API key or secret appears in API responses, error messages,
logs, or rendered UI.

**Mitigation**:
- API keys read from `.env` server-side only — never serialized to response
- `AlpacaObservationProvider.__repr__()` masks key: `PKTE...1234`
- `_redacted_url()` strips query params from URLs in error messages
- `AlpacaHealthSnapshot.to_dict()` contains no key/secret/token fields
- Frontend test verifies no `PKIGUNUW`, `7v2Uxq3`, or similar patterns in HTML
- Error messages containing env var names (e.g., "Set ALPACA_API_KEY") are guidance text, not secrets

**Verdict**: CLEARED.

---

### Vector 6: Stale / degraded data shown as current

**Threat**: The observation layer returns data with a `CURRENT` freshness label
when the underlying Alpaca response is hours old or after-hours.

**Mitigation**:
- `DataFreshnessStatus` computed from server-side timestamps
- Alpaca provides per-response timestamps (account `created_at`, quote `t`)
- After-hours data correctly maps to STALE/DEGRADED
- `StaleDataWarning` renders when any source is not CURRENT
- Mock provider deliberately returns data 30 minutes old to test freshness

**Verdict**: CLEARED.

---

### Vector 7: Browser directly calling broker API

**Threat**: The frontend JavaScript bundle contains code that calls
`paper-api.alpaca.markets` directly, bypassing the server-side health endpoint
and potentially exposing the API key.

**Mitigation**:
- `/finance-prep` fetches from `GET /health/finance-observation` only
- No Alpaca URL appears in frontend code except as display text
- API key never present in frontend bundle
- All Alpaca communication is server-side through `AlpacaObservationProvider`
- Documented in exposure boundary (§13.4)

**Verdict**: CLEARED.

---

### Vector 8: write_capabilities accidentally becoming non-empty

**Threat**: A code change accidentally sets `can_place_order = True` or similar,
enabling write operations through the observation provider.

**Mitigation**:
- `ReadOnlyAdapterCapability` is a **frozen dataclass** — cannot be mutated after construction
- `__post_init__` raises `ValueError` if any write field is True
- All write fields hardcoded `False` with no setter
- `ObservationProvider` Protocol has NO write methods
- `_request()` rejects any non-GET HTTP method
- Alpaca read-only API key provides server-side defense in depth
- Test `test_write_permissions_never_true` verifies all 4 are False

**Verdict**: CLEARED.

---

### Vector 9: Future live endpoint lacking authentication

**Threat**: When Phase 7 adds a live brokerage health endpoint, it inherits the
paper endpoint's no-auth pattern, exposing real account data without protection.

**Mitigation** (design-time only — not implemented):
- Documented in exposure boundary (§13.2): live endpoint must be SEPARATE route
- Must require authentication (API token, session, or IP whitelist)
- Current `/health/finance-observation` remains paper-only
- Live endpoint must not be accessible without explicit authorization

**Implementation required**: Phase 7 must implement this before exposing any
live account data.

**Verdict**: DOCUMENTED — requires Phase 7 implementation.

---

### Vector 10: UI action implying Ordivon placed an order

**Threat**: A button, link, or text on `/finance-prep` implies that Ordivon
placed a trade, executed an order, or performed a broker action.

**Mitigation**:
- All 3 trading actions permanently disabled: Place Live Order, Connect Broker API, Enable Auto Trading
- Test verifies no button with "submit", "execute order", "place trade", "buy", "sell" exists
- Provider banner states "No orders can be placed through this surface"
- FinanceLivePrepBanner states "No live trading is enabled"
- ObservationModeBanner states "Cannot place orders, cancel orders, withdraw funds, or transfer assets"

**Verdict**: CLEARED.

## 3. Summary

| # | Vector | Verdict |
|---|--------|---------|
| 1 | Paper equity mistaken as real money | ✅ CLEARED |
| 2 | Health endpoint mistaken as broker control plane | ✅ CLEARED |
| 3 | Provider connected mistaken as trade-enabled | ✅ CLEARED |
| 4 | Account alias exposure | ✅ CLEARED |
| 5 | Secret exposure | ✅ CLEARED |
| 6 | Stale / degraded data as current | ✅ CLEARED |
| 7 | Browser directly calling broker API | ✅ CLEARED |
| 8 | write_capabilities becoming non-empty | ✅ CLEARED |
| 9 | Future live endpoint lacking auth | 📋 DOCUMENTED (Phase 7) |
| 10 | UI action implying order placement | ✅ CLEARED |

**9 of 10 vectors CLEARED. 1 requires Phase 7 implementation (live auth).**
**No vectors represent an active security risk in the current Phase 6 state.**

## 4. Design / UI Red-Team Summary

The Design Pack and UI Governance surfaces were reviewed for these vectors:

| # | Vector | Mitigation | Status |
|---|--------|-----------|--------|
| D1 | Preview UI overclaiming production readiness | PreviewDataBanner required on all preview surfaces | ✅ |
| D2 | Shadow policy mistaken for enforcement | AdvisoryBoundaryBanner + "ADVISORY ONLY" labels | ✅ |
| D3 | CandidateRule mistaken for Policy | CandidateRuleIsNotPolicyBanner on all CR surfaces | ✅ |
| D4 | High-risk disabled action accidentally enabled | Tests assert `disabled=true`, no enable path | ✅ |
| D5 | Mock/sample data unlabeled | SAMPLE/MOCK labels on all data tables | ✅ |
| D6 | Color-only risk communication | Text labels paired with all color badges (a11y) | ✅ |
| D7 | Too many consoles before core workflow maturity | Only implemented P0/P1 consoles; P2 deferred | ✅ |

**All 7 Design vectors CLEARED.**

## 5. Overall Verdict

The Finance Observation layer is **safe for Phase 7 preparation**. All code-level
threat vectors are mitigated with at least 2 layers of defense (code + protocol +
server-side). The one outstanding item (live auth) is design-documented and
required for Phase 7 implementation, but does not affect current Phase 6 state.

Phase 7A may begin under the constraints documented in the Stage Summit.
