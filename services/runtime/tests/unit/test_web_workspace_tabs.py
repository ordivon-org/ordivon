from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_workspace_tabs_support_three_object_view_types():
    types_source = read("apps/web/src/components/workspace/types.ts")
    hook = read("apps/web/src/components/workspace/useWorkspaceTabs.ts")
    review_console = read("apps/web/src/components/features/reviews/ReviewConsole.tsx")
    provider = read("apps/web/src/components/workspace/WorkspaceProvider.tsx")
    frame = read("apps/web/src/components/workspace/ConsolePageFrame.tsx")
    seed = read("apps/web/src/components/workspace/ConsoleWorkspaceSeed.tsx")
    audits_page = read("apps/web/src/app/audits/page.tsx")
    reports_page = read("apps/web/src/app/reports/page.tsx")
    history_page = read("apps/web/src/app/history/page.tsx")

    assert "review_detail" in types_source
    assert "recommendation_detail" in types_source
    assert "trace_detail" in types_source
    assert "openTab" in hook
    assert "replaceTabs" in hook
    assert "closeTab" in hook
    assert "useWorkspaceContext" in provider
    assert "ConsoleWorkspacePanel" in frame
    assert "ConsoleWorkspaceSeed" in frame
    assert "searchParams.get('review_id')" in seed
    assert "searchParams.get('recommendation_id')" in seed
    assert "searchParams.get('trace_ref')" in seed
    assert "replaceTabs" in review_console
    assert "ConsolePageFrame" in audits_page
    assert "ConsolePageFrame" in reports_page
    assert "ConsolePageFrame" in history_page
