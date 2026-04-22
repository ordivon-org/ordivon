from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_review_console_route_and_components_exist():
    page = read("apps/web/src/app/reviews/page.tsx")
    console = read("apps/web/src/components/features/reviews/ReviewConsole.tsx")
    recommendation_panel = read("apps/web/src/components/features/reviews/RecommendationWorkspacePanel.tsx")

    assert "ReviewConsole" in page
    assert "/api/v1/reviews/pending?limit=20" in console
    assert "/api/v1/reviews/${selectedReviewId}" in console
    assert "/api/v1/traces/reviews/" in console
    assert "/api/v1/recommendations/recent?limit=50" in recommendation_panel
