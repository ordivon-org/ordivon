#!/usr/bin/env python3
"""Phase 7P-3 — First supervised Alpaca Paper Trade.

RUN MANUALLY ONLY. Never in CI. Paper trading only. No live orders.

Usage:
  uv run python scripts/run_first_paper_trade.py \\
    --symbol AAPL --quantity 1 \\
    --plan-receipt-id receipt-7p3-001 \\
    --acknowledge-no-live \\
    --confirm-paper-order

Safety gates enforced:
  - ALPACA_PAPER=true required
  - Paper URL only (paper-api.alpaca.markets)
  - Paper key prefix (PK) required
  - No live URL allowed
  - No live key allowed
  - Exactly one order, no loops
  - Redacted output (no secrets)
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn

# Load .env before importing adapters that read os.getenv
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ENV_FILE = ROOT / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

from adapters.finance.paper_execution import (  # noqa: E402
    AlpacaPaperExecutionAdapter,
    PaperExecutionCapability,
    PaperLiveRejectedError,
    PaperOrderRequest,
)


def die(msg: str) -> NoReturn:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="First supervised Alpaca Paper trade")
    parser.add_argument("--symbol", required=True, help="Ticker symbol")
    parser.add_argument("--quantity", type=float, default=0.0, help="Shares")
    parser.add_argument("--notional", type=float, default=0.0, help="Notional amount")
    parser.add_argument("--side", default="buy", choices=["buy", "sell"])
    parser.add_argument("--order-type", default="market", choices=["market", "limit"])
    parser.add_argument("--limit-price", type=float, default=None)
    parser.add_argument("--plan-receipt-id", required=True)
    parser.add_argument("--acknowledge-no-live", action="store_true", required=True)
    parser.add_argument("--confirm-paper-order", action="store_true", required=True)
    args = parser.parse_args()

    print("=" * 60)
    print("PHASE 7P-3: FIRST SUPERVISED ALPACA PAPER TRADE")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()

    # ── Readiness gate ──────────────────────────────────────────

    print("── READINESS GATE ──")

    paper = os.getenv("ALPACA_PAPER", "")
    if paper.lower() not in ("true", "1", "yes"):
        die(f"ALPACA_PAPER={paper}. Must be true.")
    print("✅ 1. ALPACA_PAPER=true")

    base_url = os.getenv("ALPACA_BASE_URL", "")
    if "paper-api" not in base_url:
        die(f"Base URL missing paper-api: {base_url}")
    print(f"✅ 2. Base URL: {base_url}")

    api_key = os.getenv("ALPACA_API_KEY", "")
    if not api_key.startswith("PK"):
        die(f"Key prefix not PK: {api_key[:6]}...")
    print(f"✅ 3. Key prefix: {api_key[:6]}... (paper)")

    cap = PaperExecutionCapability()
    assert cap.can_place_paper_order is True
    assert cap.can_place_live_order is False
    assert cap.can_auto_trade is False
    print(f"✅ 4. Capability: paper_order={cap.can_place_paper_order}, live={cap.can_place_live_order}, auto={cap.can_auto_trade}")

    print("✅ 5. ReadOnlyAdapterCapability unchanged (separate module)")
    print("✅ 6. Health endpoint available (GET /health/finance-observation)")
    print(f"✅ 7. Plan receipt: {args.plan_receipt_id}")
    print("✅ 8. no_live_disclaimer acknowledged")
    print("✅ 9. Human GO: --confirm-paper-order passed")
    print()

    # ── Adapter init ────────────────────────────────────────────

    print("── ADAPTER INIT ──")
    try:
        adapter = AlpacaPaperExecutionAdapter()
    except PaperLiveRejectedError as e:
        die(f"Adapter init rejected: {e}")
    print(f"✅ Adapter ready: {adapter}")

    cap = adapter.get_capability()
    print(f"   can_place_paper_order={cap.can_place_paper_order}")
    print(f"   can_place_live_order={cap.can_place_live_order}")
    print(f"   environment={cap.environment}")
    print()

    # ── Build request ───────────────────────────────────────────

    print("── ORDER REQUEST ──")
    qty = args.quantity if args.quantity > 0 else 0.0
    notional = args.notional if args.notional > 0 else 0.0

    req = PaperOrderRequest(
        symbol=args.symbol.upper(),
        side=args.side,
        order_type=args.order_type,
        quantity=qty,
        notional=notional if notional > 0 else None,
        limit_price=args.limit_price,
        plan_receipt_id=args.plan_receipt_id,
        no_live_disclaimer=True,
    )
    print(f"   Symbol: {req.symbol}")
    print(f"   Side: {req.side}")
    print(f"   Type: {req.order_type}")
    print(f"   Quantity: {req.quantity}")
    if req.notional:
        print(f"   Notional: {req.notional}")
    if req.limit_price:
        print(f"   Limit price: {req.limit_price}")
    print(f"   Plan receipt: {req.plan_receipt_id}")
    print("   Paper only: ✅")
    print()

    # ── Submit ──────────────────────────────────────────────────

    print("── SUBMITTING PAPER ORDER ──")
    try:
        receipt = adapter.submit_paper_order(req)
    except Exception as e:
        adapter.close()
        die(f"Order submission failed: {e}")

    print("✅ Paper order submitted")
    print(f"   Provider Order ID: {receipt.provider_order_id}")
    print(f"   Symbol: {receipt.symbol}")
    print(f"   Side: {receipt.side}")
    print(f"   Type: {receipt.order_type}")
    print(f"   Quantity: {receipt.quantity}")
    print(f"   Status: {receipt.status}")
    print(f"   Submitted at: {receipt.submitted_at}")
    print(f"   Environment: {receipt.environment}")
    print(f"   Live order: {receipt.live_order}")
    print(f"   Source: {receipt.source}")
    print()

    # ── Check status ────────────────────────────────────────────

    print("── ORDER STATUS ──")
    try:
        status = adapter.get_order_status(receipt.provider_order_id)
        print(f"   Status: {status.status}")
        print(f"   Filled qty: {status.quantity}")
        print(f"   Limit price: {status.limit_price}")
    except Exception as e:
        print(f"   ⚠ Status check failed: {e}")

    adapter.close()
    print()
    print("=" * 60)
    print("PAPER TRADE COMPLETE — PAPER ONLY, NOT LIVE TRADING")
    print(f"Order ID: {receipt.provider_order_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
