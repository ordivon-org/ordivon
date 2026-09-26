#!/usr/bin/env python3
"""Fail-closed traceability gate between RuntimeDispatchR1 and current Runtime code/tests.

This deliberately proves only current trace bindings. It is not a Rust↔TLA+ refinement proof.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "formal/RuntimeDispatchR1.trace-r1.json"
INVARIANTS = ROOT / "planning/invariants-r1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_slice(text: str, symbol: str) -> str:
    pattern = re.compile(
        rf"^(?P<indent>[ \t]*)(?:(?:pub(?:\([^)]*\))?)[ \t]+)?fn[ \t]+{re.escape(symbol)}[ \t]*\(",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"symbol not found: {symbol}")
    indent = match.group("indent")
    next_fn = re.compile(
        rf"^{re.escape(indent)}(?:(?:pub(?:\([^)]*\))?)[ \t]+)?fn[ \t]+[A-Za-z0-9_]+[ \t]*\(",
        re.MULTILINE,
    ).search(text, match.end())
    return text[match.start() : next_fn.start() if next_fn else len(text)]


def require_fragments(path: Path, symbol: str, fragments: list[str]) -> list[str]:
    errors: list[str] = []
    try:
        body = function_slice(path.read_text(encoding="utf-8"), symbol)
    except (OSError, UnicodeError, ValueError) as error:
        return [f"{path.relative_to(ROOT)}::{symbol}: {error}"]
    for fragment in fragments:
        if fragment not in body:
            errors.append(
                f"{path.relative_to(ROOT)}::{symbol} missing required trace fragment: {fragment!r}"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    try:
        trace = json.loads(TRACE.read_text(encoding="utf-8"))
        invariant_manifest = json.loads(INVARIANTS.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"formal trace: cannot load manifests: {error}", file=sys.stderr)
        return 1

    if trace.get("schemaVersion") != 1 or trace.get("kind") != "ordivon.runtime-formal-implementation-trace":
        errors.append("trace manifest identity is invalid")
    if trace.get("truthRole") != "traceability-gate-not-mechanized-refinement-proof":
        errors.append("trace manifest must retain the non-refinement truth boundary")

    formal = trace.get("formalSpecification", {})
    for path_key, digest_key in (("modulePath", "moduleSha256"), ("configPath", "configSha256")):
        relative = formal.get(path_key)
        expected = formal.get(digest_key)
        if not isinstance(relative, str) or not isinstance(expected, str):
            errors.append(f"formalSpecification lacks {path_key}/{digest_key}")
            continue
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"formal source missing: {relative}")
            continue
        observed = sha256(path)
        if observed != expected:
            errors.append(f"formal source drift: {relative}: expected {expected}, observed {observed}")

    module_path = ROOT / str(formal.get("modulePath", ""))
    if module_path.is_file():
        module = module_path.read_text(encoding="utf-8")
        for name in (formal.get("modelTransition"), formal.get("invariant")):
            if not isinstance(name, str) or f"{name} ==" not in module:
                errors.append(f"formal symbol missing from module: {name!r}")

    invariants = {
        item.get("id"): item
        for item in invariant_manifest.get("invariants", [])
        if isinstance(item, dict)
    }
    for binding in trace.get("runtimeInvariantBindings", []):
        item = invariants.get(binding.get("id"))
        if item is None:
            errors.append(f"Runtime invariant missing: {binding.get('id')}")
            continue
        if item.get("name") != binding.get("name"):
            errors.append(
                f"Runtime invariant name drift: {binding.get('id')}: expected {binding.get('name')!r}, observed {item.get('name')!r}"
            )
        proofs = set(item.get("proof", []))
        for required in binding.get("requiredProofRefs", []):
            if required not in proofs:
                errors.append(f"Runtime invariant {binding.get('id')} lost proof binding {required}")

    for group in ("implementationBindings", "testBindings"):
        for binding in trace.get(group, []):
            path = ROOT / binding["path"]
            errors.extend(require_fragments(path, binding["symbol"], binding.get("requiredFragments", [])))

    non_claims = trace.get("nonClaims", [])
    if not any("not a mechanized refinement proof" in item for item in non_claims):
        errors.append("trace manifest lost explicit refinement non-claim")

    if errors:
        for error in errors:
            print(f"formal trace: {error}", file=sys.stderr)
        return 1
    print("formal trace: PASS (traceability/currentness only; mechanized refinement NOT claimed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
