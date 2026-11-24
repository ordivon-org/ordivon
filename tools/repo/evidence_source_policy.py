"""Evidence consumer binding for the shared exact-Git selector contract."""
from __future__ import annotations

from pathlib import Path

from selector_source_contract import control_inputs, qualify_selector_source

CONTROL_INPUTS = control_inputs("evidence")


def qualify_current_selector(repo: Path, source_cut: str) -> None:
    repo = repo.resolve()
    if repo != Path(__file__).resolve().parents[2]:
        raise ValueError("selector policy checkout differs from requested SourceCut")
    qualify_selector_source(repo, source_cut, scope="evidence")
