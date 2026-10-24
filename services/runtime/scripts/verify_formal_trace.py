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
    "RuntimeDispatch.registryDispatchCAS",
    "RuntimeDispatch.ambiguityHeld",
    "ExecutionProvider.guaranteeNegativeControl",
    "RuntimeDispatch.terminalEvidence",
    "RuntimeDispatch.parallelAdmissionUnique",
}
# Root/cgroup-bound Rust tests exist, but #[ignore] means CI does not execute them.
# These are conditional external acceptance witnesses, never active proving tests.
REQUIRED_OPT_IN_TESTS = {
    "RuntimeDispatch.concurrentObservers",
    "RuntimeDispatch.ambiguityNoRedrive",
}
REQUIRED_SUPPORTING_CONTRACTS = {
    "ExecutionProvider.assumeGuarantee",
}
REQUIRED_MODEL_BINDINGS = {
    "RuntimeDispatch.Dispatch",
    "RuntimeDispatch.AtMostOnceDispatchPerAttempt",
    "RuntimeDispatch.AmbiguityRequiresReconciliation",
    "RuntimeDispatch.TerminalEvidenceIsCommitted",
    "RuntimeDispatch.NoCompetingLiveAttempts",
}
REQUIRED_RUNTIME_INVARIANT_BINDINGS = {"I05", "I11"}


# These are the actual existing RuntimeDispatchR1.cfg obligations, not a
# substitute for TLC. Their independent currentness check prevents a
# refreshed hash from laundering a weaker (or entirely vacuous) check.
REQUIRED_TLC_INVARIANTS = {
    "TypeOK",
    "AtMostOnceDispatchPerAttempt",
    "AmbiguityRequiresReconciliation",
    "NoUnusedAttemptWasDispatched",
    "TerminalAttemptWasDispatched",
}
REQUIRED_TLC_PROPERTIES = {"ProgressToFirstDecision"}


def check_tlc_config_obligations(content: str, claimed_invariants: set[str] | None = None) -> list[str]:
    checked: dict[str, set[str]] = {"INVARIANTS": set(), "PROPERTIES": set()}
    specification: list[str] = []
    retry_bound_sets: list[set[str]] = []
    unreviewed_state_filters: set[str] = set()
    section = ""
    for raw in content.splitlines():
        # TLA+ configuration comments start at backslash-star.
        line = raw.split("\\*", 1)[0].strip()
        if not line:
            continue
        attempts = re.fullmatch(r"Attempts\s*=\s*\{([^{}]*)\}", line)
        if attempts:
            members = [member.strip() for member in attempts.group(1).split(",")]
            retry_bound_sets.append(set(members))
            if len(members) != len(set(members)) or any(not member for member in members):
                retry_bound_sets.append(set())
        parts = line.split()
        marker = parts[0]
        if marker in {"CONSTRAINT", "CONSTRAINTS", "ACTION_CONSTRAINT", "SYMMETRY", "VIEW"}:
            unreviewed_state_filters.add(marker)
        if marker in {"SPECIFICATION", "INVARIANTS", "INVARIANT", "PROPERTIES", "PROPERTY",
                      "CONSTANTS", "CONSTANT", "CHECK_DEADLOCK", "CONSTRAINT", "SYMMETRY",
                      "VIEW", "ALIAS", "INIT", "NEXT"}:
            section = {"INVARIANT": "INVARIANTS", "PROPERTY": "PROPERTIES"}.get(marker, marker)
            if marker == "SPECIFICATION":
                specification.append(" ".join(parts[1:]))
            elif section in checked:
                checked[section].update(parts[1:])
        elif section in checked:
            checked[section].update(parts)

    errors = []
    if unreviewed_state_filters:
        errors.append(
            f"TLC config unreviewed state-space restrictions: {sorted(unreviewed_state_filters)}"
        )
    if specification != ["FairSpec"]:
        errors.append(f"TLC config must check FairSpec including fairness, got {specification!r}")
    if len(retry_bound_sets) != 1 or len(retry_bound_sets[0]) < 3:
        errors.append("TLC config must bind at least three distinct Attempts to explore consecutive explicit retries")
    for section, required in (
        ("INVARIANTS", REQUIRED_TLC_INVARIANTS),
        ("PROPERTIES", REQUIRED_TLC_PROPERTIES),
    ):
        expected = required | (claimed_invariants or set()) if section == "INVARIANTS" else required
        missing = expected - checked[section]
        if missing:
            errors.append(f"TLC config missing checked {section}: {sorted(missing)}")
    return errors


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()



def _rust_code_only(text: str) -> str:
    """Preserve code positions, but never treat Rust comments/literals as proof.

    Rust block comments can nest. Keep newlines to preserve attribute adjacency
    while hiding everything that rustc treats as comments or string content.
    This is source-identity screening, not a Rust AST or refinement proof.
    """
    masked = list(text)
    n = len(text)

    def hide(start: int, end: int) -> None:
        for pos in range(start, end):
            if masked[pos] != "\n":
                masked[pos] = " "

    i = 0
    while i < n:
        start = i
        if text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end == -1 else end
            hide(start, i)
        elif text.startswith("/*", i):
            i += 2
            depth = 1
            while i < n and depth:
                if text.startswith("/*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated Rust block comment")
            hide(start, i)
        elif (
            (text[i] == "r" or text.startswith("br", i))
            and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"))
        ):
            j = i + (2 if text.startswith("br", i) else 1)
            while j < n and text[j] == "#":
                j += 1
            if j < n and text[j] == '"':
                ending = '"' + text[start + (2 if text.startswith("br", start) else 1) : j]
                end = text.find(ending, j + 1)
                if end == -1:
                    raise ValueError("unterminated Rust raw string")
                i = end + len(ending)
                hide(start, i)
            else:
                i += 1
        elif text[i] == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated Rust string")
            hide(start, min(i, n))
        else:
            i += 1
    return "".join(masked)


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
    code = _rust_code_only(text)
    match = pattern.search(code)
    if not match:
        raise ValueError(f"{owner_kind} owner not found: {owner}")
    opening = code.find("{", match.start(), match.end())
    closing = _matching_brace(code, opening)
    return code[match.start() : closing + 1]


def _runtime_source_identity_error(path: Path) -> str | None:
    """Proof references must name exact Runtime SourceCut bytes, not aliases."""
    # Anchor relative names at the canonical Runtime root. A caller may
    # legitimately mount that root through an outer alias, but a proof
    # reference must never redirect below the Owner root.
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        return f"{path} escapes Runtime source"
    canonical = ROOT.resolve() / relative
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        return f"{path} escapes Runtime source"
    if resolved != canonical:
        return f"{path} is not an exact Runtime source"
    return None


def require_owned_method(path: Path, owner_kind: str, owner: str, symbol: str) -> list[str]:
    identity_error = _runtime_source_identity_error(path)
    if identity_error:
        return [identity_error]
    try:
        block = owner_slice(path.read_text(encoding="utf-8"), owner_kind, owner)
    except (OSError, UnicodeError, ValueError) as error:
        return [f"{path.relative_to(ROOT)}::{owner}: {error}"]
    if not re.search(rf"\bfn\s+{re.escape(symbol)}\s*\(", block):
        return [f"{path.relative_to(ROOT)}::{owner} missing method symbol {symbol!r}"]
    return []


def require_test_symbol(path: Path, symbol: str, *, require_ignored: bool = False) -> list[str]:
    identity_error = _runtime_source_identity_error(path)
    if identity_error:
        return [identity_error]
    try:
        text = path.read_text(encoding="utf-8")
        code = _rust_code_only(text)
    except (OSError, UnicodeError, ValueError) as error:
        return [f"{path.relative_to(ROOT)}::{symbol}: {error}"]
    match = re.search(rf"(?m)^\s*fn\s+{re.escape(symbol)}\s*\(", code)
    if not match:
        return [f"{path.relative_to(ROOT)} missing proving test symbol {symbol!r}"]
    # Test identity is a proof reference: attribute must belong to this function,
    # not merely appear near it on an earlier function (or in a comment).
    attributes = []
    for line in reversed(text[: match.start()].splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#[") and stripped.endswith("]"):
            attributes.append(stripped)
            continue
        break
    if not any(re.fullmatch(r"#\s*\[\s*test\s*\]", attribute) for attribute in attributes):
        return [f"{path.relative_to(ROOT)}::{symbol} is not marked #[test]"]
    # A source-level #[test] is not always-on evidence if Rust can compile it
    # out or inject #[ignore] through cfg_attr. Never promote such a witness
    # without proof that its conditional branch is active in the Owner CI cut.
    if any(re.fullmatch(r"#\s*\[\s*cfg(?:_attr)?\s*\(.*\)\s*\]", attr) for attr in attributes):
        return [f"{path.relative_to(ROOT)}::{symbol} is conditionally compiled or ignored, not an always-on proving test"]
    ignored = any(re.fullmatch(r'#\s*\[\s*ignore(?:\s*=\s*".*")?\s*\]', attribute) for attribute in attributes)
    if ignored and not require_ignored:
        return [f"{path.relative_to(ROOT)}::{symbol} is ignored, not an always-on proving test"]
    if require_ignored and not ignored:
        return [f"{path.relative_to(ROOT)}::{symbol} is not an explicitly ignored opt-in test"]
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
        identity_error = _runtime_source_identity_error(path)
        if identity_error:
            if "escapes Runtime source" in identity_error:
                errors.append(f"formal source escapes Runtime source: {relative}")
            else:
                errors.append(f"formal source {identity_error}: {relative}")
            continue
        if not path.is_file():
            errors.append(f"formal source missing: {relative}")
            continue
        observed = sha256(path)
        if observed != expected:
            errors.append(f"formal source drift: {relative}: expected {expected}, observed {observed}")

    config = formal.get("configPath")
    if isinstance(config, str) and (ROOT / config).is_file():
        model_claims = formal.get("modelBindings", [])
        claimed = {
            item["symbol"] for item in model_claims
            if isinstance(item, dict) and item.get("kind") == "invariant"
            and isinstance(item.get("symbol"), str)
        } if isinstance(model_claims, list) else set()
        try:
            errors.extend(check_tlc_config_obligations(
                (ROOT / config).read_text(encoding="utf-8"), claimed
            ))
        except (OSError, UnicodeError) as error:
            errors.append(f"TLC config unreadable: {error}")

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
        binding_id = binding.get("id")
        # A named formal obligation must denote its exact TLA operator, not
        # merely any operator found in the same checked model.
        if isinstance(binding_id, str) and binding_id != f"RuntimeDispatch.{symbol}":
            errors.append(
                f"formal model binding identity drift: {binding_id!r} cannot bind {symbol!r}"
            )
        expected_kind = "transition" if binding_id == "RuntimeDispatch.Dispatch" else "invariant"
        if kind != expected_kind:
            errors.append(
                f"formal model binding type drift: {binding_id!r}: expected {expected_kind}, observed {kind}"
            )
        if not re.search(rf"(?m)^\s*{re.escape(symbol)}\s*==", module):
            errors.append(f"formal symbol missing from module: {symbol!r}")

    invariants = {
        item.get("id"): item
        for item in invariant_manifest.get("invariants", [])
        if isinstance(item, dict)
    }
    runtime_bindings = trace.get("runtimeInvariantBindings", [])
    runtime_ids = _ids(runtime_bindings)
    if not isinstance(runtime_bindings, list) or len(runtime_ids) != len(set(runtime_ids)):
        errors.append("Runtime invariant binding IDs are invalid or duplicated")
    if set(runtime_ids) != REQUIRED_RUNTIME_INVARIANT_BINDINGS:
        errors.append(
            f"Runtime invariant binding set drift: expected {sorted(REQUIRED_RUNTIME_INVARIANT_BINDINGS)}, "
            f"observed {sorted(set(runtime_ids))}"
        )
    for binding in runtime_bindings if isinstance(runtime_bindings, list) else []:
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
        required_refs = binding.get("requiredProofRefs")
        if (
            not isinstance(required_refs, list)
            or not required_refs
            or any(not isinstance(ref, str) or not ref for ref in required_refs)
        ):
            errors.append(f"Runtime invariant {binding.get('id')} has no required proof references")
            continue
        proofs = set(item.get("proof", []))
        for required in required_refs:
            if required not in proofs:
                errors.append(f"Runtime invariant {binding.get('id')} lost proof binding {required}")
                continue
            if "::" not in required:
                errors.append(f"Runtime invariant {binding.get('id')} has malformed proof reference {required!r}")
                continue
            path, symbol = required.split("::", 1)
            errors.extend(require_test_symbol(ROOT / path, symbol))

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

    # Disjoint evidence roles: existence of a conditional physical test does not
    # count toward always-on implementation witnesses or model refinement.
    conditional = trace.get("conditionalAcceptanceTests", [])
    conditional_ids = _ids(conditional)
    if len(conditional_ids) != len(set(conditional_ids)) or set(conditional_ids) != REQUIRED_OPT_IN_TESTS:
        errors.append("conditional acceptance test set drift")
    for binding in conditional if isinstance(conditional, list) else []:
        if not isinstance(binding, dict):
            errors.append("conditional acceptance binding must be an object")
            continue
        relative = binding.get("path")
        symbol = binding.get("symbol")
        if binding.get("evidenceMode") != "physical-opt-in" or not all(
            isinstance(value, str) for value in (relative, symbol)
        ):
            errors.append(f"conditional acceptance {binding.get('id')} lost opt-in evidence type")
            continue
        errors.extend(require_test_symbol(ROOT / relative, symbol, require_ignored=True))

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
    for source in (TRACE, INVARIANTS):
        error = _runtime_source_identity_error(source)
        if error:
            print(f"formal trace: {error}", file=sys.stderr)
            return 1
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
