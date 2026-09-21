from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HISTORICAL_NAUTILUS_DOCS = (
    "docs/CRYPTO_EXECUTION_LANE_OKX_BINANCE_2026-09-13.md",
    "docs/CRYPTO_NATIVE_ADAPTER_QUALIFICATION_R1_2026-09-13.md",
    "docs/DEMO_EXECUTION_PREFLIGHT_R7_2026-09-14.md",
    "docs/PRIVATE_REALITY_READONLY_PREFLIGHT_2026-09-14.md",
    "docs/OKX_LIVE_PROVIDER_BINDING_2026-09-14.md",
    "docs/CRYPTO_FIX44_PROJECTION_R4_2026-09-14.md",
)


def test_historical_nautilus_docs_declare_non_authoritative_currentness():
    for rel in HISTORICAL_NAUTILUS_DOCS:
        text = (ROOT / rel).read_text()
        first_block = chr(10).join(text.splitlines()[:8])
        assert "Historical qualification notice — 2026-09-21" in first_block
        assert (
            "docs/ARCHITECTURE.md" in first_block
            or "config/" in first_block
        ), rel
        assert any(
            marker in first_block
            for marker in (
                "candidate",
                "superseded",
                "not current",
                "not a current",
            )
        ), rel
