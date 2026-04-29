# Alpaca Paper Execution Boundary

Status: **DOCUMENTED** (Phase 7P-1)
Date: 2026-04-29
Phase: 7P-1
Tags: `alpaca`, `paper`, `execution`, `boundary`, `adapter`, `read-only`, `separation`

## 1. Purpose

This document defines the architectural boundary between:

1. **`ReadOnlyAdapterCapability`** (Phase 6G) — observation only, write=False
2. **Paper execution** (Phase 7P-2) — paper orders only, live=False

These two concerns **must not** share a class, capability contract, or code path.
A paper execution adapter is a fundamentally different thing from a read-only
observation adapter. Mixing them would undermine the safety guarantees that
Phase 6 spent 16 sub-phases building.

## 2. Boundary Table

| Property | ReadOnlyAdapterCapability | Future PaperExecutionCapability |
|----------|--------------------------|-------------------------------|
| Class | `ReadOnlyAdapterCapability` (frozen) | `PaperExecutionCapability` (new, separate) |
| File | `domains/finance/read_only_adapter.py` | `adapters/finance/paper_execution.py` (new) |
| can_read_market_data | ✅ True | ✅ True |
| can_read_account | ✅ True | ✅ True |
| can_read_positions | ✅ True | ✅ True |
| can_read_fills | ✅ True | ✅ True |
| can_place_paper_order | ❌ False | ✅ True (paper only) |
| can_place_live_order | ❌ False | ❌ False |
| can_cancel_order | ❌ False | ❌ False |
| can_withdraw | ❌ False | ❌ False |
| can_transfer | ❌ False | ❌ False |
| Endpoint | paper-api (GET only) | paper-api (GET + POST paper orders) |
| Enforced at | Post-init (frozen) | Post-init (frozen) |
| Live URL allowed? | ❌ | ❌ |
| Mutability | Frozen (cannot change) | Frozen (cannot change) |

## 3. What Must NOT Happen

| Forbidden Action | Why |
|-----------------|-----|
| Adding `can_place_order` to `ReadOnlyAdapterCapability` | Violates Phase 6 safety guarantees |
| Subclassing `ReadOnlyAdapterCapability` to add write | Inheritance bypasses frozen enforcement |
| Pointing paper execution adapter to `api.alpaca.markets` | Live URL — blocked at init |
| Reusing `ObservationProvider` Protocol for execution | Protocol has no write methods by design |
| Sharing API key between read-only and paper execution | Separate keys enforce separation of concerns |
| Allowing paper adapter to accept non-paper base URL | Must enforce `paper-api` at init |

## 4. Implementation Guard Contract (Phase 7P-2)

The `PaperExecutionCapability` class (to be implemented) must:

```python
@dataclass(frozen=True)
class PaperExecutionCapability:
    adapter_id: str = "alpaca-paper-execution"
    can_read_market_data: bool = True
    can_read_account: bool = True
    can_read_positions: bool = True
    can_read_fills: bool = True
    can_place_paper_order: bool = True       # NEW — paper only
    # All live write = False
    can_place_live_order: bool = False
    can_cancel_order: bool = False
    can_withdraw: bool = False
    can_transfer: bool = False

    def __post_init__(self):
        if self.can_place_live_order:
            raise ValueError("PaperExecutionCapability: live orders forbidden")
        if self.can_cancel_order:
            raise ValueError("PaperExecutionCapability: cancel forbidden")
        if self.can_withdraw or self.can_transfer:
            raise ValueError("PaperExecutionCapability: withdraw/transfer forbidden")
```

## 5. URL Enforcement

| URL | ReadOnlyAdapterCapability | PaperExecutionCapability |
|-----|--------------------------|-------------------------|
| `paper-api.alpaca.markets` | ✅ GET only | ✅ GET + POST paper orders |
| `api.alpaca.markets` (live) | ❌ rejected at init | ❌ rejected at init |
| `paper-api.alpaca.markets` + live key prefix (AK...) | ❌ rejected (PK required) | ❌ rejected (PK required) |

## 6. API Key Separation

| Key | ReadOnlyAdapter | PaperExecution |
|-----|----------------|----------------|
| `ALPACA_API_KEY` (paper, PK...) | Used for GET | Used for GET + POST paper orders |
| `ALPACA_SECRET_KEY` | Used for GET | Used for GET + POST paper orders |
| Live Alpaca key (AK...) | ❌ rejected | ❌ rejected |

Phase 7P-2 may reuse the same paper API key pair (PK...) since the paper
endpoint is the same and Alpaca paper keys support both read and paper-order
operations. What matters is that the **capability contract** is separate,
not necessarily the keys.

If a separate key pair is preferred for defense in depth, that is acceptable
but not required for Phase 7P-2.

## 7. Test Requirements (Phase 7P-2)

Before any paper order is placed:

- [ ] `PaperExecutionCapability` cannot have live write True
- [ ] Paper URL enforcement at init
- [ ] Live URL rejected at init
- [ ] Live key prefix (AK) rejected
- [ ] `ReadOnlyAdapterCapability` is unchanged (write=False)
- [ ] No method on read-only adapter accepts POST
- [ ] Paper order method exists only on paper execution adapter
- [ ] All paper orders include "paper" in method name or annotation
- [ ] No secrets in repr/logs/errors
- [ ] Mocked HTTP tests (no real API calls in CI)

## 8. ReadOnlyAdapterCapability — Freeze Confirmation

The existing `ReadOnlyAdapterCapability` is **frozen and immutable**.
It was finalized in Phase 6G and has 6 safety guards:

1. Post-init: keys present check
2. Post-init: paper flag check
3. Post-init: paper URL check
4. Post-init: key prefix check (PK only)
5. Runtime: HTTP GET-only guard in `_request()`
6. Structural: frozen dataclass (cannot setattr)

**No changes to this class are permitted in Phase 7P.**
The paper execution adapter is a completely separate implementation.
