from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_review_console_route_and_components_exist():
    page = read("apps/web/src/app/reviews/page.tsx")
    console = read("apps/web/src/components/features/reviews/ReviewConsole.tsx")
    recommendation_panel = read("apps/web/src/components/features/reviews/RecommendationWorkspacePanel.tsx")
    frame = read("apps/web/src/components/workspace/ConsolePageFrame.tsx")

    assert "ReviewConsole" in page
    assert "ConsolePageFrame" in page
    assert "/api/v1/reviews/pending?limit=20" in console
    assert "Review Workbench" in console
    assert "Queue-first supervision" in console
    assert "Pending Review Queue" in console
    assert "Supporting Views" in console
    assert "recommendation_detail" in console
    assert "trace_detail" in console
    assert "searchParams.get('recommendation_id')" in console
    assert "item.recommendation_id === requestedRecommendationId" in console
    assert "/api/v1/recommendations/${recommendationId}" in recommendation_panel
    assert "ConsoleWorkspaceSeed" in frame
