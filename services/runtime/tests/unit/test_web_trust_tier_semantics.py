from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_trust_tier_is_centralized_and_review_surface_reuses_it():
    semantic = read("apps/web/src/lib/semanticSignals.ts")
    product_signals = read("apps/web/src/components/state/ProductSignals.tsx")
    review_console = read("apps/web/src/components/features/reviews/ReviewConsole.tsx")

    assert "TrustTier" in semantic
    assert "outcome_signal" in semantic
    assert "hint" in semantic
    assert "missing" in product_signals
    assert "Review Workbench" in review_console
