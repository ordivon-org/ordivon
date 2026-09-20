from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .document import build_pandoc_docx
from .passthrough import copy_exact

PresentationBuilder = Callable[[Path, Path, Path], dict[str, Any]]


def execute_build_adapter(
    adapter_id: str,
    *,
    source_path: Path,
    profile_path: Path,
    output_path: Path,
    presentation_builders: Mapping[str, PresentationBuilder],
    pandoc: Path,
) -> dict[str, Any]:
    """Execute one already-selected build adapter.

    Adapter selection belongs to Artifact core binding data. This module owns provider
    dispatch only; it does not select profiles or decide final artifact acceptance.
    """
    presentation = presentation_builders.get(adapter_id)
    if presentation is not None:
        return presentation(source_path, profile_path, output_path)
    if adapter_id == "pandoc-docx":
        return build_pandoc_docx(source_path, output_path, pandoc)
    if adapter_id in {"standards-web-source", "native-artifact-pass-through"}:
        return copy_exact(source_path, output_path)
    return {"status": "FAIL", "error": f"unimplemented adapter: {adapter_id}"}
