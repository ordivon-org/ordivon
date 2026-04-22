from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_workspace_tabs_support_three_object_view_types():
    types_source = read("apps/web/src/components/workspace/types.ts")
    hook = read("apps/web/src/components/workspace/useWorkspaceTabs.ts")
    review_console = read("apps/web/src/components/features/reviews/ReviewConsole.tsx")

    assert "review_detail" in types_source
    assert "recommendation_detail" in types_source
    assert "trace_detail" in types_source
    assert "openTab" in hook
    assert "replaceTabs" in hook
    assert "closeTab" in hook
    assert "RecommendationWorkspacePanel" in review_console
