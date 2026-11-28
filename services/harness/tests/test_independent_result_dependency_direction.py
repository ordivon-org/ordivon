from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "ordivon_harness"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_result_projection_is_below_recorder_and_continuity() -> None:
    recorder = _imports(SRC / "independent_result.py")
    continuity = _imports(SRC / "ordivon" / "run_continuity.py")
    projection = _imports(SRC / "independent_result_projection.py")

    assert "ordivon.run_continuity" in recorder
    assert "independent_result_projection" in continuity
    assert "independent_result" not in continuity
    assert "ordivon.run_continuity" not in projection
    assert "independent_result" not in projection

def test_independent_result_model_identity_remains_compatible() -> None:
    from ordivon_harness.independent_result import (
        IndependentCompletionProposal,
        IndependentHarnessRunReceipt,
        StoredIndependentRunResult,
    )
    from ordivon_harness.independent_result_projection import (
        IndependentCompletionProposal as ProjectionCompletionProposal,
        IndependentHarnessRunReceipt as ProjectionHarnessRunReceipt,
        StoredIndependentRunResult as ProjectionStoredRunResult,
    )

    assert IndependentHarnessRunReceipt is ProjectionHarnessRunReceipt
    assert IndependentCompletionProposal is ProjectionCompletionProposal
    assert StoredIndependentRunResult is ProjectionStoredRunResult
    assert IndependentHarnessRunReceipt.__module__ == "ordivon_harness.independent_result"
    assert IndependentCompletionProposal.__module__ == "ordivon_harness.independent_result"
    assert StoredIndependentRunResult.__module__ == "ordivon_harness.independent_result"
