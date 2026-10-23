#!/usr/bin/env python3
"""Fail-closed currentness gate from RuntimeDispatchR1 to stable Runtime contract seams.

This gate validates named semantic seams and proving-test identities. It deliberately does not
bind source-code body fragments and is not a Rust↔TLA+ refinement proof.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "formal/RuntimeDispatchR1.trace-r1.json"
INVARIANTS = ROOT / "planning/invariants-r1.json"

REQUIRED_SEAMS = {
    "Registry.dispatchCAS",
    "AttemptLifecycle.singleDispatch",
    "ExecutionProvider.realize",
}
REQUIRED_TESTS = {
    "RuntimeDispatch.concurrentObservers",
    "RuntimeDispatch.ambiguityNoRedrive",
    "ExecutionProvider.guaranteeNegativeControl",
}
REQUIRED_SUPPORTING_CONTRACTS = {
    "ExecutionProvider.assumeGuarantee",
}
REQUIRED_MODEL_BINDINGS = {
    "RuntimeDispatch.Dispatch",
    "RuntimeDispatch.AtMostOnceDispatchPerAttempt",
    "RuntimeDispatch.AmbiguityRequiresReconciliation",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matching_brace(text: str, opening: int) -> int:
    depth = 0
    for index in range(opening, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("owner block has no matching closing brace")


def owner_slice(text: str, owner_kind: str, owner: str) -> str:
    if owner_kind == "trait":
        pattern = re.compile(rf"\btrait\s+{re.escape(owner)}\b[^{{]*{{")
    elif owner_kind == "impl":
        pattern = re.compile(
            rf"\bimpl(?:\s*<[^{{>]*>)?\s+{re.escape(owner)}(?:\s*<[^{{>]*>)?\s*{{"
        )
    else:
        raise ValueError(f"unsupported ownerKind: {owner_kind!r}")
    match = pattern.search(text)
    if not match:
        raise ValueError(f"{owner_kind} owner not found: {owner}")
    opening = text.find("{", match.start(), match.end())
    closing = _matching_brace(text, opening)
    return text[match.start() : closing + 1]


def require_owned_method(path: Path, owner_kind: str, owner: str, symbol: str) -> list[str]:
    try:
        block = owner_slice(path.read_text(encoding="utf-8"), owner_kind, owner)
    except (OSError, UnicodeError, ValueError) as error:
        return [f"{path.relative_to(ROOT)}::{owner}: {error}"]
    if not re.search(rf"\bfn\s+{re.escape(symbol)}\s*\(", block):
        return [f"{path.relative_to(ROOT)}::{owner} missing method symbol {symbol!r}"]
    return []


def require_test_symbol(path: Path, symbol: str) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [f"{path.relative_to(ROOT)}::{symbol}: {error}"]
    match = re.search(rf"(?m)^\s*fn\s+{re.escape(symbol)}\s*\(", text)
    if not match:
        return [f"{path.relative_to(ROOT)} missing proving test symbol {symbol!r}"]
    prefix = text[max(0, match.start() - 512) : match.start()]
    if not re.search(r"#\s*\[\s*test\s*\]", prefix):
        return [f"{path.relative_to(ROOT)}::{symbol} is not marked #[test]"]
    return []


def _ids(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [item.get("id") for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)]


def validate(trace: dict[str, Any], invariant_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if trace.get("schemaVersion") != 2 or trace.get("kind") != "ordivon.runtime-formal-implementation-trace":
        errors.append("trace manifest identity/schema is invalid")
    if trace.get("truthRole") != "traceability-gate-not-mechanized-refinement-proof":
        errors.append("trace manifest must retain the non-refinement truth boundary")

    # Source-body fragment binding is intentionally retired in schema v2.
    encoded = json.dumps(trace, sort_keys=True)
    if "requiredFragments" in encoded:
        errors.append("schema v2 must not bind source-code body fragments")

    formal = trace.get("formalSpecification", {})
    if not isinstance(formal, dict):
        errors.append("formalSpecification must be an object")
        formal = {}
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

    model_bindings = formal.get("modelBindings", [])
    model_ids = _ids(model_bindings)
    if len(model_ids) != len(set(model_ids)):
        errors.append("formal model binding IDs are not unique")
    if set(model_ids) != REQUIRED_MODEL_BINDINGS:
        errors.append(
            f"formal model binding set drift: expected {sorted(REQUIRED_MODEL_BINDINGS)}, observed {sorted(model_ids)}"
        )
    module_path = ROOT / str(formal.get("modulePath", ""))
    module = module_path.read_text(encoding="utf-8") if module_path.is_file() else ""
    for binding in model_bindings if isinstance(model_bindings, list) else []:
        if not isinstance(binding, dict):
            errors.append("formal model binding must be an object")
            continue
        symbol = binding.get("symbol")
        kind = binding.get("kind")
        if kind not in {"transition", "invariant"} or not isinstance(symbol, str):
            errors.append(f"invalid formal model binding: {binding!r}")
            continue
        if not re.search(rf"(?m)^\s*{re.escape(symbol)}\s*==", module):
            errors.append(f"formal symbol missing from module: {symbol!r}")

    invariants = {
        item.get("id"): item
        for item in invariant_manifest.get("invariants", [])
        if isinstance(item, dict)
    }
    for binding in trace.get("runtimeInvariantBindings", []):
        if not isinstance(binding, dict):
            errors.append("Runtime invariant binding must be an object")
            continue
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

    seams = trace.get("contractSeams", [])
    seam_ids = _ids(seams)
    if len(seam_ids) != len(set(seam_ids)):
        errors.append("contract seam IDs are not unique")
    if set(seam_ids) != REQUIRED_SEAMS:
        errors.append(f"contract seam set drift: expected {sorted(REQUIRED_SEAMS)}, observed {sorted(seam_ids)}")
    for binding in seams if isinstance(seams, list) else []:
        if not isinstance(binding, dict):
            errors.append("contract seam binding must be an object")
            continue
        if binding.get("symbolKind") != "method":
            errors.append(f"unsupported contract symbolKind for {binding.get('id')}: {binding.get('symbolKind')!r}")
            continue
        relative = binding.get("path")
        owner_kind = binding.get("ownerKind")
        owner = binding.get("owner")
        symbol = binding.get("symbol")
        if not all(isinstance(value, str) for value in (relative, owner_kind, owner, symbol)):
            errors.append(f"contract seam {binding.get('id')} has incomplete owner identity")
            continue
        errors.extend(require_owned_method(ROOT / relative, owner_kind, owner, symbol))

    supporting = trace.get("supportingContracts", [])
    supporting_ids = _ids(supporting)
    if len(supporting_ids) != len(set(supporting_ids)):
        errors.append("supporting contract IDs are not unique")
    if set(supporting_ids) != REQUIRED_SUPPORTING_CONTRACTS:
        errors.append(
            f"supporting contract set drift: expected {sorted(REQUIRED_SUPPORTING_CONTRACTS)}, observed {sorted(supporting_ids)}"
        )
    for binding in supporting if isinstance(supporting, list) else []:
        if not isinstance(binding, dict):
            errors.append("supporting contract binding must be an object")
            continue
        relative = binding.get("path")
        owner_kind = binding.get("ownerKind")
        owner = binding.get("owner")
        symbol = binding.get("symbol")
        if binding.get("symbolKind") != "method" or not all(
            isinstance(value, str) for value in (relative, owner_kind, owner, symbol)
        ):
            errors.append(f"supporting contract {binding.get('id')} has incomplete owner identity")
            continue
        errors.extend(require_owned_method(ROOT / relative, owner_kind, owner, symbol))

    tests = trace.get("provingTests", [])
    test_ids = _ids(tests)
    if len(test_ids) != len(set(test_ids)):
        errors.append("proving test IDs are not unique")
    if set(test_ids) != REQUIRED_TESTS:
        errors.append(f"proving test set drift: expected {sorted(REQUIRED_TESTS)}, observed {sorted(test_ids)}")
    known_targets = REQUIRED_SEAMS | REQUIRED_SUPPORTING_CONTRACTS | REQUIRED_MODEL_BINDINGS
    proved: set[str] = set()
    for binding in tests if isinstance(tests, list) else []:
        if not isinstance(binding, dict):
            errors.append("proving test binding must be an object")
            continue
        relative = binding.get("path")
        symbol = binding.get("symbol")
        if not isinstance(relative, str) or not isinstance(symbol, str):
            errors.append(f"proving test {binding.get('id')} has incomplete symbol identity")
            continue
        errors.extend(require_test_symbol(ROOT / relative, symbol))
        targets = binding.get("proves", [])
        if not isinstance(targets, list) or not targets:
            errors.append(f"proving test {binding.get('id')} has no proves bindings")
            continue
        for target in targets:
            if target not in known_targets:
                errors.append(f"proving test {binding.get('id')} references unknown target {target!r}")
            elif isinstance(target, str):
                proved.add(target)

    for seam in REQUIRED_SEAMS:
        if seam not in proved:
            errors.append(f"contract seam lacks proving test binding: {seam}")
    for contract in REQUIRED_SUPPORTING_CONTRACTS:
        if contract not in proved:
            errors.append(f"supporting contract lacks proving test binding: {contract}")
    for model in REQUIRED_MODEL_BINDINGS - {"RuntimeDispatch.Dispatch"}:
        if model not in proved:
            errors.append(f"formal safety property lacks proving test binding: {model}")

    non_claims = trace.get("nonClaims", [])
    if not isinstance(non_claims, list) or not any(
        isinstance(item, str) and "not a mechanized refinement proof" in item for item in non_claims
    ):
        errors.append("trace manifest lost explicit refinement non-claim")

    return errors


def main() -> int:
    try:
        trace = json.loads(TRACE.read_text(encoding="utf-8"))
        invariant_manifest = json.loads(INVARIANTS.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"formal trace: cannot load manifests: {error}", file=sys.stderr)
        return 1

    errors = validate(trace, invariant_manifest)
    if errors:
        for error in errors:
            print(f"formal trace: {error}", file=sys.stderr)
        return 1

    print(
        "formal trace: PASS (stable contract/test currentness only; source fragments retired; mechanized refinement NOT claimed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
