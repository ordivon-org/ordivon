from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_finance_pack_frontend_surface_options_are_pack_owned():
    helper = read("packs/finance/analyze_surface.ts")
    profile = read("packs/finance/analyze_profile.py")
    options = read("packs/finance/analyze_surface_options.json")

    assert "getFinanceAnalyzeSurfaceOptions" in helper
    assert "defaultSymbol" in options
    assert "supportedSymbols" in options
    assert "supportedTimeframes" in options
    assert "analyze_surface_options.json" in profile


def test_generic_frontend_analyze_components_consume_pack_surface_options():
    quick_analyze = read("apps/web/src/components/features/dashboard/QuickAnalyze.tsx")
    analyze_input = read("apps/web/src/components/features/analyze/AnalyzeInput.tsx")

    assert "getFinanceAnalyzeSurfaceOptions" in quick_analyze
    assert "getFinanceAnalyzeSurfaceOptions" in analyze_input
    assert '<option value="BTC/USDT">' not in quick_analyze
    assert '<option value="BTC/USDT">' not in analyze_input
    assert "['15m', '1h', '4h', '1d']" not in analyze_input
