from __future__ import annotations

import ast
from pathlib import Path

from ordivon_composition import canonical_digest

from ordivon_experimental_episode_store.ingest import build_ingest_identity

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src" / "ordivon_experimental_episode_store"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def test_ingest_identity_reuses_composition_canonical_digest() -> None:
    ingest_id, material = build_ingest_identity(
        corpus_id="corpus-r1",
        profile_id="runtime-r5c-v1",
        source_file_digest=_sha("1"),
        projection_set_digest=_sha("2"),
        schema_digest=_sha("3"),
        adapter_digest=_sha("4"),
    )
    assert ingest_id == "ingest:" + canonical_digest(material)


def test_episode_store_does_not_reintroduce_private_canonical_digest() -> None:
    offenders: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "_canonical_digest"
            ):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert offenders == [], "reuse ordivon_composition.canonical_digest"
