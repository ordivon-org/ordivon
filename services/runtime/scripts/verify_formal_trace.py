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
    "RuntimeDispatch.NoDetachedLiveAttempt",
    "RuntimeDispatch.HeldOrphanIsFenced",
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
    # Preserve RW9 real result provenance and the independent CEGAR
    # ability to recover a matching observation after foreign evidence.
    "MatchingResultRequiredForTerminal",
    "NoForeignResultIsTerminal",
    "ForeignResultDoesNotDisableMatchingRecovery",
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
    # A Rust char or byte-char literal may contain braces. Only match an
    # actual single-character token; apostrophe-prefixed lifetimes ('a, 'static)
    # are not literals and must not swallow later source tokens.
    char_literal = re.compile(
        r"'(?:\\u\{[0-9A-Fa-f_]+\}|\\x[0-9A-Fa-f]{2}|\\[^\n]|[^'\\\n])'"
    )

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
        elif text[i] == "'" and (character := char_literal.match(text, i)):
            i = character.end()
            hide(start, i)
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


def _attached_rust_attributes(code: str, item_start: int) -> list[str]:
    """Read adjacent Rust attributes, including multiline #[cfg(...)] blocks.

    Work on the comment/string-masked source, never the original raw text.
    This is conservative identity screening, not a replacement for rustc.
    """
    lines = code[:item_start].splitlines()
    cursor = len(lines) - 1
    attrs: list[str] = []
    while cursor >= 0:
        while cursor >= 0 and not lines[cursor].strip():
            cursor -= 1
        if cursor < 0 or not lines[cursor].strip().endswith("]"):
            break
        begin = cursor
        bracket_depth = 0
        while begin >= 0:
            fragment = lines[begin].strip()
            bracket_depth += fragment.count("]") - fragment.count("[")
            if bracket_depth <= 0:
                break
            begin -= 1
        if begin < 0 or bracket_depth != 0:
            break
        attribute = " ".join(line.strip() for line in lines[begin : cursor + 1])
        if not re.fullmatch(r"#\s*\[.*\]", attribute):
            break
        attrs.append(attribute)
        cursor = begin - 1
    return attrs


def _has_unqualified_cfg(attrs: list[str], *, test_context: bool) -> bool:
    for attribute in attrs:
        if not re.match(r"#\s*\[\s*cfg(?:_attr)?\s*\(", attribute):
            continue
        # The built-in test harness selects #[cfg(test)] on test sources.
        if test_context and re.fullmatch(r"#\s*\[\s*cfg\s*\(\s*test\s*\)\s*\]", attribute):
            continue
        # All other cfg claims must have a separately proven active build.
        return True
    return False


def _conditional_rust_ancestor(
    code: str, witness_start: int, *, test_context: bool
) -> bool:
    """Reject a proof hidden inside a cfg-dependent enclosing Rust module.

    Rust source inspection cannot validate arbitrary cfg expressions or macro
    expansions. This check only upgrades an obvious false PASS to a typed
    unknown/rejection; it does not prove an item was compiled.
    """
    for match in re.finditer(r"\bmod\s+[A-Za-z_]\w*\s*\{", code):
        opening = code.find("{", match.start(), match.end())
        if opening >= witness_start:
            continue
        if witness_start >= _matching_brace(code, opening):
            continue
        if _has_unqualified_cfg(
            _attached_rust_attributes(code, match.start()), test_context=test_context
        ):
            return True
    return False



def _inside_macro_rules_definition(code: str, witness_start: int) -> bool:
    """Reject source-only symbols inside macro_rules! bodies.

    Macro token definitions are not Rust items until expanded. A lexical test
    symbol or impl inside an uninvoked macro is not a compiled/registered
    witness. This conservative guard does not claim general macro expansion
    verification; only rustc/native proof can establish generated items.
    """
    pairs = {"{": "}", "(": ")", "[": "]"}
    pattern = r"\bmacro_rules\s*!\s*[A-Za-z_]\w*\s*([{\[(])"
    for match in re.finditer(pattern, code):
        if match.start() >= witness_start:
            break
        opener = match.group(1)
        closing = pairs[opener]
        depth = 0
        for index in range(match.end() - 1, len(code)):
            if code[index] == opener:
                depth += 1
            elif code[index] == closing:
                depth -= 1
                if depth == 0:
                    if witness_start < index:
                        return True
                    break
    return False




def _inside_unexpanded_macro_invocation(code: str, witness_start: int) -> bool:
    """Do not admit Rust item-looking tokens inside a macro call as proof.

    The macro may erase or transform arbitrary token trees. In particular a
    parenthesized/bracketed call has no Rust block braces for the ordinary
    enclosing-scope check to notice. This bounded source guard does not prove
    that tokens outside a call were registered by rustc.
    """
    delimiters = {"(": ")", "[": "]", "{": "}"}
    closing = set(delimiters.values())
    pattern = r"\b[A-Za-z_]\w*!\s*([({\[])"
    for match in re.finditer(pattern, code):
        if match.start() >= witness_start:
            break
        stack: list[str] = []
        for i in range(match.end() - 1, len(code)):
            char = code[i]
            if char in delimiters:
                stack.append(delimiters[char])
            elif char in closing:
                if not stack or stack.pop() != char:
                    break
                if not stack:
                    if witness_start < i:
                        return True
                    break
        else:
            # An unbalanced source-only macro cannot authorize a witness.
            if match.end() - 1 < witness_start:
                return True
    return False



def _test_has_nonmodule_enclosing_scope(code: str, witness_start: int) -> bool:
    """Fail closed for unnameable Rust tests nested in non-module blocks.

    Inline named modules are valid scopes. Source-only screening still cannot
    prove actual rustc test registration or execution.
    """
    scopes: list[int] = []
    for index, char in enumerate(code[:witness_start]):
        if char == "{":
            scopes.append(index)
        elif char == "}" and scopes:
            scopes.pop()
    for opening in scopes:
        prefix = code[max(0, opening - 240) : opening]
        if not re.search(r"\bmod\s+[A-Za-z_]\w*\s*$", prefix):
            return True
    return False


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


def _external_rust_module_errors(path: Path, *, test_context: bool) -> list[str]:
    """Require a qualified direct Rust module declaration for a proof file.

    An external module's #[cfg] belongs to its parent file, not the file that
    contains the proving fn/impl. This is a fail-closed lexical gate for the
    named direct module; it does not establish whole-crate feature activation.
    """
    if path.name == "mod.rs":
        module_name = path.parent.name
        directory = path.parent.parent
    else:
        module_name = path.stem
        directory = path.parent
    candidates = [directory / "mod.rs", directory.parent / f"{directory.name}.rs"]
    if directory.name == "src":
        candidates.extend((directory / "lib.rs", directory / "main.rs"))
    parents = [candidate for candidate in candidates if candidate != path and candidate.is_file()]
    if not parents:
        # Standalone Rust test fixtures have no surrounding crate declaration.
        return []
    if len(parents) != 1:
        return [f"{path.relative_to(ROOT)} has ambiguous external module parents"]
    parent = parents[0]
    identity_error = _runtime_source_identity_error(parent)
    if identity_error:
        return [identity_error]
    try:
        raw = parent.read_text(encoding="utf-8")
        code = _rust_code_only(raw)
        declarations = [
            match.start()
            for match in re.finditer(rf"\bmod\s+{re.escape(module_name)}\s*;", code)
        ]
        # Rust include!("engine/execution.rs") is an owner-local source
        # composition edge, not a separate mod declaration. Bind the literal
        # file name to this exact source, never an arbitrary include! symbol.
        for match in re.finditer(r"\binclude!\s*\(", code):
            literal = re.match(r'\s*"([^"\n]+)"\s*\)\s*;', raw[match.end():])
            if literal and parent.parent / literal.group(1) == path:
                declarations.append(match.start())
        if len(declarations) != 1:
            return [
                f"{path.relative_to(ROOT)} has {len(declarations)} exact external module/include declarations"
            ]
        attributes = _attached_rust_attributes(code, declarations[0])
        if _has_unqualified_cfg(attributes, test_context=test_context):
            return [f"{path.relative_to(ROOT)} has conditional external module/include declaration"]
        if any(re.match(r"#\s*\[\s*path\s*=", attr) for attr in attributes):
            return [f"{path.relative_to(ROOT)} has redirected external module path"]
        if _conditional_rust_ancestor(code, declarations[0], test_context=test_context):
            return [f"{path.relative_to(ROOT)} has conditional external ancestor module"]
    except (OSError, UnicodeError, ValueError) as error:
        return [f"{path.relative_to(ROOT)} has unreadable external module parent: {error}"]
    return []


def require_owned_method(path: Path, owner_kind: str, owner: str, symbol: str) -> list[str]:
    identity_error = _runtime_source_identity_error(path)
    if identity_error:
        return [identity_error]
    module_errors = _external_rust_module_errors(path, test_context=False)
    if module_errors:
        return module_errors
    try:
        text = path.read_text(encoding="utf-8")
        block = owner_slice(text, owner_kind, owner)
        code = _rust_code_only(text)
        if owner_kind == "trait":
            pattern = re.compile(rf"\btrait\s+{re.escape(owner)}\b[^{{]*{{")
        else:
            pattern = re.compile(
                rf"\bimpl(?:\s*<[^{{>]*>)?\s+{re.escape(owner)}(?:\s*<[^{{>]*>)?\s*{{"
            )
        item = pattern.search(code)
        if item and _inside_macro_rules_definition(code, item.start()):
            return [f"{path.relative_to(ROOT)}::{owner} is inside an unexpanded macro_rules! definition"]
        if item and _inside_unexpanded_macro_invocation(code, item.start()):
            return [f"{path.relative_to(ROOT)}::{owner} is inside an unexpanded macro invocation"]
        if item and (
            _has_unqualified_cfg(
                _attached_rust_attributes(code, item.start()), test_context=False
            )
            or _conditional_rust_ancestor(code, item.start(), test_context=False)
        ):
            return [f"{path.relative_to(ROOT)}::{owner} has conditional ancestor or Owner cfg"]
    except (OSError, UnicodeError, ValueError) as error:
        return [f"{path.relative_to(ROOT)}::{owner}: {error}"]
    # Methods must be direct children of this impl/trait. A nested Rust
    # function is legal source, but it is NOT the declared Owner method.
    # Source masking above removes comments and literals before brace counting.
    opening = block.find("{")
    if opening < 0:
        return [f"{path.relative_to(ROOT)}::{owner} missing owner body"]
    method_pattern = re.compile(rf"\bfn\s+{re.escape(symbol)}\s*\(")
    matches = list(method_pattern.finditer(block, opening + 1))
    if not matches:
        return [f"{path.relative_to(ROOT)}::{owner} missing method symbol {symbol!r}"]
    conditional = False
    macro_only = False
    # The method's source location is not executable proof when an enclosing
    # invocation may erase its Rust tokens before rustc builds the impl.
    masked_block = _rust_code_only(block)
    for match in matches:
        depth = 0
        for char in block[opening : match.start()]:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
        if depth != 1:
            continue
        if (
            _inside_unexpanded_macro_invocation(masked_block, match.start())
            or _inside_macro_rules_definition(masked_block, match.start())
        ):
            macro_only = True
            continue
        # A method compiled out by cfg/cfg_attr cannot witness the physical
        # Runtime seam even when the surrounding impl is always compiled.
        if _has_unqualified_cfg(
            _attached_rust_attributes(block, match.start()), test_context=False
        ):
            conditional = True
            continue
        return []
    if conditional:
        return [f"{path.relative_to(ROOT)}::{owner}::{symbol} is a conditional Owner method"]
    if macro_only:
        return [f"{path.relative_to(ROOT)}::{owner}::{symbol} is inside unexpanded macro tokens"]
    return [f"{path.relative_to(ROOT)}::{owner} missing direct method symbol {symbol!r}"]


def require_test_symbol(path: Path, symbol: str, *, require_ignored: bool = False) -> list[str]:
    identity_error = _runtime_source_identity_error(path)
    if identity_error:
        return [identity_error]
    module_errors = _external_rust_module_errors(path, test_context=True)
    if module_errors:
        return module_errors
    try:
        text = path.read_text(encoding="utf-8")
        code = _rust_code_only(text)
    except (OSError, UnicodeError, ValueError) as error:
        return [f"{path.relative_to(ROOT)}::{symbol}: {error}"]
    match = re.search(rf"(?m)^\s*fn\s+{re.escape(symbol)}\s*\(", code)
    if not match:
        return [f"{path.relative_to(ROOT)} missing proving test symbol {symbol!r}"]
    if _inside_macro_rules_definition(code, match.start()):
        return [f"{path.relative_to(ROOT)}::{symbol} is inside an unexpanded macro_rules! definition"]
    if _inside_unexpanded_macro_invocation(code, match.start()):
        return [f"{path.relative_to(ROOT)}::{symbol} is inside an unexpanded macro invocation"]
    if _test_has_nonmodule_enclosing_scope(code, match.start()):
        return [f"{path.relative_to(ROOT)}::{symbol} has an unnameable non-module test scope"]
    try:
        if _conditional_rust_ancestor(code, match.start(), test_context=True):
            return [f"{path.relative_to(ROOT)}::{symbol} has conditional ancestor module"]
    except ValueError as error:
        return [f"{path.relative_to(ROOT)}::{symbol}: {error}"]
    # Test identity is a proof reference: inspect only attributes attached
    # to this function, including multiline cfg/cfg_attr. Use the same masked
    # source that located the function; source text in literals/comments is
    # not an executable test attribute.
    attributes = _attached_rust_attributes(code, match.start())
    if not any(re.fullmatch(r"#\s*\[\s*test\s*\]", attribute) for attribute in attributes):
        return [f"{path.relative_to(ROOT)}::{symbol} is not marked #[test]"]
    # A source-level #[test] is not always-on evidence if Rust can compile it
    # out or inject #[ignore] through cfg_attr. Never promote such a witness
    # without proof that its conditional branch is active in the Owner CI cut.
    if any(re.fullmatch(r"#\s*\[\s*cfg(?:_attr)?\s*\(.*\)\s*\]", attr) for attr in attributes):
        return [f"{path.relative_to(ROOT)}::{symbol} is conditionally compiled or ignored, not an always-on proving test"]
    # Rust string values were masked above, but a reason-bearing #[ignore]
    # remains an ignore attribute whether its reason is quoted or blanked.
    ignored = any(re.fullmatch(r"#\s*\[\s*ignore(?:\s*=\s*.*)?\s*\]", attr) for attr in attributes)
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


# Build/toolchain inputs outside the Runtime source subtree can invalidate a
# Runtime proof witness just as Runtime-owned Rust input can. This is a bounded
# Git read-set guard, NOT complete build/runtime dependency qualification.
_ROOT_BUILD_INPUTS = frozenset({
    "Cargo.toml", "Cargo.lock", "rust-toolchain", "rust-toolchain.toml",
    "mise.toml", "mise.lock",
})


def project_proving_test_source_impact(
    trace: dict[str, Any],
    invariant_manifest: dict[str, Any],
    changed_paths: set[str],
) -> dict[str, Any]:
    """Rebuild one Runtime-owned Git-source read-set projection, never proof reuse.

    The source read-sets are *declared* by the existing trace manifest, not a
    compiler-discovered consumer closure. A changed unindexed Runtime source is
    UNKNOWN, rather than permission to reuse a test or mechanized proof.
    """
    prefix = "services/runtime/"
    if not isinstance(changed_paths, set) or any(
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
        for path in changed_paths
    ):
        raise ValueError("impact changed paths must be exact normalized Git paths")

    def owned(relative: str) -> str:
        if not isinstance(relative, str) or not relative or (
            Path(relative).is_absolute()
            or any(part in {"", ".", ".."} for part in relative.split("/"))
            or "\\" in relative
        ):
            raise ValueError("non-canonical Runtime source dependency")
        return prefix + relative

    common = {
        owned("formal/RuntimeDispatchR1.trace-r1.json"),
        owned("planning/invariants-r1.json"),
        owned("scripts/verify_formal_trace.py"),
        owned("scripts/tests/test_formal_trace.py"),
        owned(trace["formalSpecification"]["modulePath"]),
        owned(trace["formalSpecification"]["configPath"]),
    }
    for item in invariant_manifest.get("invariants", []):
        if item.get("id") in REQUIRED_RUNTIME_INVARIANT_BINDINGS:
            for ref in item.get("proof", []):
                if isinstance(ref, str) and "::" in ref:
                    common.add(owned(ref.split("::", 1)[0]))

    carriers = {
        item["id"]: owned(item["path"])
        for key in ("contractSeams", "supportingContracts")
        for item in trace[key]
    }
    readsets = {}
    for witness in trace["provingTests"]:
        files = set(common)
        files.add(owned(witness["path"]))
        files.update(carriers[target] for target in witness["proves"] if target in carriers)
        readsets[witness["id"]] = files

    indexed = set().union(common, *readsets.values())
    runtime_changed = {path for path in changed_paths if path.startswith(prefix)}
    unindexed = runtime_changed - indexed
    # Root build/toolchain inputs can invalidate the interpretation of every
    # Runtime source witness even when no Runtime-local path has changed.
    # This is a deliberately bounded cross-cutting assumption guard, NOT a
    # claim that every external dependency has been discovered.
    crosscutting_assumption_changes = {
        path for path in changed_paths
        if path in _ROOT_BUILD_INPUTS or path.startswith(".cargo/")
    }
    rows = []
    for witness_id, readset in sorted(readsets.items()):
        hits = sorted(readset & changed_paths)
        # Shared Rust callees are not proved closed by the manifest, and
        # global build inputs can invalidate every witness without local diffs.
        standing = (
            "RECHECK_REQUIRED" if hits
            else "UNKNOWN" if runtime_changed or crosscutting_assumption_changes
            else "REUSE_CANDIDATE"
        )
        rows.append({
            "id": witness_id,
            "standing": standing,
            "matchedChangedPaths": hits,
            "declaredReadSet": sorted(readset),
        })
    return {
        "kind": "ordivon.runtime-formal-source-impact",
        "truthRole": "non-authoritative-exact-git-source-projection",
        "standingByWitness": rows,
        "unindexedRuntimeChanges": sorted(unindexed),
        "crosscuttingAssumptionChanges": sorted(crosscutting_assumption_changes),
        "changedPaths": sorted(changed_paths),
        "scope": "Runtime tracked Git source plus declared root build/toolchain assumption guards ONLY; no installed/configured/physical/runtime consumer claims",
        "nonClaims": [
            "REUSE_CANDIDATE is not proof PASS, implementation refinement, or installed acceptance.",
            "Declared source readsets are not demonstrated complete Rust build/runtime dependency closures.",
            "A no-hit Runtime source change is UNKNOWN even if its path is indexed by another witness; shared Rust callees are not exhaustively indexed.",
            "Changes outside Runtime are outside this projection's verified dependency scope.",
        ],
    }


def _git_source_changes(base: str, head: str) -> set[str]:
    """Derive exact source deltas from Git itself, not caller-authored changed refs."""
    import re as _re
    import subprocess

    if not all(_re.fullmatch(r"[0-9a-f]{40}", x) for x in (base, head)):
        raise ValueError("impact base/head must be exact 40-hex Git commits")
    repo = ROOT.parents[1]
    def git(*args: str) -> bytes:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
    actual_head = git("rev-parse", "HEAD").decode().strip()
    if head != actual_head:
        raise ValueError(f"impact HEAD is not checkout HEAD: {head} != {actual_head}")
    # Git status can hide edited tracked files when the index carries
    # assume-unchanged or skip-worktree bits. Such flags defeat a source
    # currentness claim even when --porcelain reports an empty worktree.
    source_scope = ("services/runtime", *sorted(_ROOT_BUILD_INPUTS), ".cargo")
    index_rows = git("ls-files", "-v", "-z", "--", *source_scope)
    if any(
        not row.startswith(b"H ")
        for row in index_rows.split(b"\x00") if row
    ):
        raise ValueError("impact Runtime/formal build tracked source has unsafe Git index flags")
    if git("status", "--porcelain", "--untracked-files=normal", "--", *source_scope):
        raise ValueError("impact Runtime/formal build worktree is dirty; Git source is not current checkout")
    for revision in (base, head):
        git("cat-file", "-e", f"{revision}^{{commit}}")
    data = git("diff", "--no-renames", "--name-only", "-z", base, head, "--")
    return {path.decode("utf-8") for path in data.split(b"\x00") if path}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--impact-base", help="exact Git source base SHA")
    parser.add_argument("--impact-head", help="exact Git source HEAD SHA")
    # The current Runtime Python contract also calls main() directly in tests.
    args = parser.parse_args([] if argv is None else argv)
    if bool(args.impact_base) != bool(args.impact_head):
        parser.error("--impact-base and --impact-head must be supplied together")
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

    if args.impact_base:
        try:
            delta = _git_source_changes(args.impact_base, args.impact_head)
            projection = project_proving_test_source_impact(trace, invariant_manifest, delta)
        except (OSError, ValueError, __import__("subprocess").CalledProcessError) as error:
            print(f"formal source impact: UNKNOWN ({error})", file=sys.stderr)
            return 1
        projection["baseRevision"] = args.impact_base
        projection["headRevision"] = args.impact_head
        print(json.dumps(projection, sort_keys=True))
        return 0

    print(
        "formal trace: PASS (stable contract/test currentness only; source fragments retired; mechanized refinement NOT claimed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
