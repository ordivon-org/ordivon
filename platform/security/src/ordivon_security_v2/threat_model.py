from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SOURCE_BINDING_KEY = "ordivon.dev/security/source-binding"


def architecture_envelope_digest(root: Path, paths: Iterable[str]) -> str:
    root = root.resolve()
    h = hashlib.sha256()
    normalized = sorted(set(paths))
    if not normalized:
        raise ValueError("architecture envelope must contain at least one path")
    for rel in normalized:
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(f"unsafe architecture-envelope path: {rel}")
        full = (root / p).resolve()
        if root not in full.parents and full != root:
            raise ValueError(f"architecture-envelope path escapes repository: {rel}")
        data = full.read_bytes()
        rel_bytes = p.as_posix().encode("utf-8")
        h.update(len(rel_bytes).to_bytes(8, "big"))
        h.update(rel_bytes)
        h.update(len(data).to_bytes(8, "big"))
        h.update(data)
    return "sha256:" + h.hexdigest()


def source_binding(model: dict[str, Any]) -> dict[str, Any]:
    extensions = model.get("extensions")
    if not isinstance(extensions, dict):
        raise ValueError("threat model has no extensions object")
    binding = extensions.get(SOURCE_BINDING_KEY)
    if not isinstance(binding, dict):
        raise ValueError(f"threat model has no {SOURCE_BINDING_KEY} extension")
    return binding


def validate_model_binding(model: dict[str, Any], root: Path) -> dict[str, Any]:
    binding = source_binding(model)
    if binding.get("schemaVersion") != 1:
        raise ValueError("unsupported source-binding schemaVersion")
    paths = binding.get("architecturePaths")
    expected = binding.get("architectureEnvelopeSha256")
    if not isinstance(paths, list) or not all(isinstance(x, str) for x in paths):
        raise ValueError("architecturePaths must be an array of strings")
    if not isinstance(expected, str) or not expected.startswith("sha256:"):
        raise ValueError("architectureEnvelopeSha256 must be sha256:<hex>")
    actual = architecture_envelope_digest(root, paths)
    if actual != expected:
        raise ValueError(f"stale threat model: expected {expected}, observed {actual}")
    return {
        "standing": "CURRENT",
        "architectureEnvelopeSha256": actual,
        "architecturePaths": sorted(set(paths)),
        "modelVersion": model.get("version"),
    }


def load_and_validate(model_path: Path, root: Path) -> dict[str, Any]:
    model = json.loads(model_path.read_text())
    return validate_model_binding(model, root)
