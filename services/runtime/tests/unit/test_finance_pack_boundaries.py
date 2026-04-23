from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_generic_web_surfaces_do_not_inline_finance_defaults():
    generic_surface_paths = [
        "apps/web/src/app/page.tsx",
        "apps/web/src/app/analyze/page.tsx",
        "apps/web/src/components/features/dashboard/RecentRecommendations.tsx",
        "apps/web/src/components/features/dashboard/PendingReviews.tsx",
        "apps/web/src/components/status/SystemStatusBar.tsx",
    ]

    forbidden_literals = ("BTC/USDT", "ETH/USDT", "SOL/USDT", "15m", "1h", "4h", "1d")

    for rel_path in generic_surface_paths:
        source = _read(rel_path)
        for literal in forbidden_literals:
            assert literal not in source, f"{literal} leaked into generic surface: {rel_path}"


def test_api_v1_routes_do_not_depend_on_compatibility_service_facades():
    api_v1_dir = ROOT / "apps/api/app/api/v1"
    offending_imports: list[str] = []

    for path in api_v1_dir.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "apps.api.app.services" in source:
            offending_imports.append(path.name)

    assert offending_imports == [], f"API v1 routes should not import compatibility facades: {offending_imports}"
