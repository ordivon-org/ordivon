from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact, sha256_file

from .toolchain import GLOBAL_PANDOC, LEGACY_PANDOC, selected_external_file


def _pandoc_inline_text(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    parts: list[str] = []
    for node in values:
        if not isinstance(node, dict):
            continue
        kind = node.get("t")
        content = node.get("c")
        if kind == "Str" and isinstance(content, str):
            parts.append(content)
        elif kind in {"Space", "SoftBreak", "LineBreak"}:
            parts.append(" ")
        elif kind in {
            "Emph", "Strong", "Strikeout", "Superscript", "Subscript",
            "SmallCaps", "Underline",
        }:
            parts.append(_pandoc_inline_text(content))
        elif kind in {"Code", "Math"} and isinstance(content, list) and len(content) >= 2:
            parts.append(str(content[1]))
        elif kind in {"Link", "Image"} and isinstance(content, list) and len(content) >= 2:
            parts.append(_pandoc_inline_text(content[1]))
        elif kind in {"Span", "Cite"} and isinstance(content, list) and len(content) >= 2:
            parts.append(_pandoc_inline_text(content[1]))
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _pandoc_semantic_projection(blocks: Any) -> list[dict[str, Any]]:
    if not isinstance(blocks, list):
        return []
    projection: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        kind = block.get("t")
        content = block.get("c")
        if kind == "Header" and isinstance(content, list) and len(content) >= 3:
            projection.append(
                {
                    "kind": "heading",
                    "level": int(content[0]),
                    "text": _pandoc_inline_text(content[2]),
                }
            )
        elif kind in {"Para", "Plain"}:
            projection.append(
                {"kind": "paragraph", "text": _pandoc_inline_text(content)}
            )
        elif (
            kind == "OrderedList"
            and isinstance(content, list)
            and len(content) >= 2
            and isinstance(content[1], list)
        ):
            for item in content[1]:
                text = " | ".join(
                    entry["text"]
                    for entry in _pandoc_semantic_projection(item)
                    if entry.get("text")
                )
                projection.append({"kind": "ordered-item", "text": text})
        elif kind == "BulletList" and isinstance(content, list):
            for item in content:
                text = " | ".join(
                    entry["text"]
                    for entry in _pandoc_semantic_projection(item)
                    if entry.get("text")
                )
                projection.append({"kind": "bullet-item", "text": text})
        elif kind == "BlockQuote":
            projection.extend(_pandoc_semantic_projection(content))
        elif kind == "Div" and isinstance(content, list) and len(content) >= 2:
            projection.extend(_pandoc_semantic_projection(content[1]))
        elif kind == "CodeBlock" and isinstance(content, list) and len(content) >= 2:
            projection.append({"kind": "code-block", "text": str(content[1])})
        elif kind == "HorizontalRule":
            projection.append({"kind": "horizontal-rule", "text": ""})
    return projection


def _pandoc_meta_text(value: Any) -> str | list[str] | None:
    if not isinstance(value, dict):
        return None
    kind = value.get("t")
    content = value.get("c")
    if kind == "MetaString" and isinstance(content, str):
        return content
    if kind == "MetaInlines":
        return _pandoc_inline_text(content)
    if kind == "MetaList" and isinstance(content, list):
        return [
            str(item)
            for item in (_pandoc_meta_text(entry) for entry in content)
            if item is not None
        ]
    return None


def _run_pandoc_ast(pandoc: Path, source: Path, from_format: str) -> dict[str, Any]:
    proc = subprocess.run(
        [str(pandoc), "--from", from_format, "--to", "json", str(source)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Pandoc semantic parse failed for {from_format}: {proc.stderr[-2000:]}"
        )
    value = json.loads(proc.stdout)
    if not isinstance(value, dict) or not isinstance(value.get("blocks"), list):
        raise RuntimeError(
            f"Pandoc semantic parse did not return a document AST for {from_format}"
        )
    return value


def verify_document_semantic_correspondence(
    source: Path,
    document: Path,
    pandoc: Path | None = None,
) -> dict[str, Any]:
    executable = pandoc or selected_external_file(
        "ARTIFACT_PANDOC", GLOBAL_PANDOC, LEGACY_PANDOC
    )
    failures: list[str] = []
    if not executable.is_file() or not os.access(executable, os.X_OK):
        return {
            "status": "FAIL",
            "source": file_fact(source),
            "artifact": file_fact(document),
            "pandoc": {"path": str(executable), "status": "NOT_AVAILABLE"},
            "failures": ["Pandoc semantic verifier is unavailable"],
        }
    version_proc = subprocess.run(
        [str(executable), "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    version = (
        version_proc.stdout.splitlines()[0]
        if version_proc.returncode == 0 and version_proc.stdout
        else "unknown"
    )
    try:
        source_ast = _run_pandoc_ast(executable, source, "markdown")
        document_ast = _run_pandoc_ast(executable, document, "docx")
    except Exception as error:
        return {
            "status": "FAIL",
            "source": file_fact(source),
            "artifact": file_fact(document),
            "pandoc": {
                "path": str(executable.resolve()),
                "sha256": sha256_file(executable),
                "version": version,
            },
            "failures": [str(error)],
        }

    source_projection = _pandoc_semantic_projection(source_ast.get("blocks"))
    document_projection = _pandoc_semantic_projection(document_ast.get("blocks"))
    if not source_projection:
        failures.append("source semantic projection is empty")
    if source_projection != document_projection:
        failures.append(
            "normalized Pandoc source/document semantic projections differ"
        )

    source_meta = (
        source_ast.get("meta", {})
        if isinstance(source_ast.get("meta"), dict)
        else {}
    )
    document_meta = (
        document_ast.get("meta", {})
        if isinstance(document_ast.get("meta"), dict)
        else {}
    )
    compared_meta: dict[str, Any] = {}
    for key in ("title", "subtitle", "author"):
        if key not in source_meta:
            continue
        expected = _pandoc_meta_text(source_meta.get(key))
        observed = _pandoc_meta_text(document_meta.get(key))
        compared_meta[key] = {
            "source": expected,
            "document": observed,
            "matched": expected == observed,
        }
        if expected != observed:
            failures.append(f"document metadata did not preserve source {key}")

    return {
        "status": "PASS" if not failures else "FAIL",
        "source": file_fact(source),
        "artifact": file_fact(document),
        "pandoc": {
            "path": str(executable.resolve()),
            "sha256": sha256_file(executable),
            "version": version,
        },
        "sourceProjection": source_projection,
        "documentProjection": document_projection,
        "metadata": compared_meta,
        "failures": failures,
        "boundary": (
            "PASS establishes normalized Markdown->DOCX semantic correspondence "
            "through the locked Pandoc parser on both sides. The builder and semantic "
            "parser share Pandoc and therefore this is not independent IV&V; Word "
            "target behavior, visual review and accessibility remain separate gates."
        ),
    }
