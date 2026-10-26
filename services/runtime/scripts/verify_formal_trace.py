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
    "LocalCancellationNeverDispatched",
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
        if marker in {
            "SPECIFICATION",
            "INVARIANTS",
            "INVARIANT",
            "PROPERTIES",
            "PROPERTY",
            "CONSTANTS",
            "CONSTANT",
            "CHECK_DEADLOCK",
            "CONSTRAINT",
            "SYMMETRY",
            "VIEW",
            "ALIAS",
            "INIT",
            "NEXT",
        }:
            section = {"INVARIANT": "INVARIANTS", "PROPERTY": "PROPERTIES"}.get(marker, marker)
            if marker == "SPECIFICATION":
                specification.append(" ".join(parts[1:]))
            elif section in checked:
                checked[section].update(parts[1:])
        elif section in checked:
            checked[section].update(parts)

    errors = []
    if unreviewed_state_filters:
        errors.append(f"TLC config unreviewed state-space restrictions: {sorted(unreviewed_state_filters)}")
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


# Four existing Runtime trace seams have exactly three compiler-owned tests.
# This is a fixed trace contract, not a LEGO registry or Rust syntax parser.
NATIVE_CONTRACT_WITNESSES = {
    "Registry.dispatchCAS": (
        "crates/ordivon-runtime-core/src/runtime/registry/lifecycle.rs",
        "impl",
        "Registry",
        "mark_dispatch_issued",
        "runtime::registry::native_formal_mark_dispatch_issued_contract",
    ),
    "AttemptLifecycle.singleDispatch": (
        "crates/ordivon-runtime-core/src/runtime/engine/execution.rs",
        "impl",
        "Runtime",
        "ensure_attempt_dispatched",
        "runtime::engine::native_formal_runtime_dispatch_methods_contract",
    ),
    "ExecutionProvider.realize": (
        "crates/ordivon-runtime-core/src/runtime/engine/execution.rs",
        "impl",
        "Runtime",
        "dispatch_attempt",
        "runtime::engine::native_formal_runtime_dispatch_methods_contract",
    ),
    "ExecutionProvider.assumeGuarantee": (
        "crates/ordivon-runtime-core/src/runtime/execution_provider.rs",
        "trait",
        "ExecutionProviderSpi",
        "realize",
        "runtime::execution_provider::local_linux_adapter_tests::native_formal_execution_provider_spi_contract",
    ),
}


def native_contract_expected(binding: dict[str, Any]) -> str:
    """Fail closed if a manifest relabels the actual compiler-bound seam."""
    expected = NATIVE_CONTRACT_WITNESSES.get(binding.get("id"))
    actual = tuple(binding.get(key) for key in ("path", "ownerKind", "owner", "symbol"))
    if expected is None or actual != expected[:4]:
        raise ValueError(f"native Rust contract seam identity drift: {binding.get('id')}")
    return expected[4]


def require_contract_source(
    path: Path,
    owner_kind: str,
    owner: str,
    symbol: str,
) -> list[str]:
    """Preserve exact Git source provenance; rustc checks owner methods/types."""
    errors = require_test_source(path, symbol)
    if owner_kind not in {"impl", "trait"} or not isinstance(owner, str):
        errors.append(f"{path}: invalid contract owner identity")
    return errors


def require_test_source(path: Path, symbol: str) -> list[str]:
    """Check source provenance; rustc/libtest owns Rust syntax and test truth."""
    error = _runtime_source_identity_error(path)
    if error:
        return [error]
    if not path.is_file() or path.suffix != ".rs":
        return [f"{path}: missing exact Rust source"]
    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Za-z_]\w*", symbol):
        return [f"{path}: invalid native test symbol"]
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
        claimed = (
            {
                item["symbol"]
                for item in model_claims
                if isinstance(item, dict) and item.get("kind") == "invariant" and isinstance(item.get("symbol"), str)
            }
            if isinstance(model_claims, list)
            else set()
        )
        try:
            errors.extend(check_tlc_config_obligations((ROOT / config).read_text(encoding="utf-8"), claimed))
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
            errors.append(f"formal model binding identity drift: {binding_id!r} cannot bind {symbol!r}")
        expected_kind = "transition" if binding_id == "RuntimeDispatch.Dispatch" else "invariant"
        if kind != expected_kind:
            errors.append(f"formal model binding type drift: {binding_id!r}: expected {expected_kind}, observed {kind}")
        if not re.search(rf"(?m)^\s*{re.escape(symbol)}\s*==", module):
            errors.append(f"formal symbol missing from module: {symbol!r}")

    invariants = {item.get("id"): item for item in invariant_manifest.get("invariants", []) if isinstance(item, dict)}
    conditional_refs = {
        f"{item['path']}::{item['symbol']}"
        for item in trace.get("conditionalAcceptanceTests", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("symbol"), str)
    }
    declared_always_on = {
        f"{test['path']}::{test['symbol']}"
        for test in trace.get("provingTests", [])
        if isinstance(test, dict) and isinstance(test.get("path"), str) and isinstance(test.get("symbol"), str)
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
            if required not in declared_always_on:
                errors.append(f"Runtime invariant {binding.get('id')} lacks declared native proving test")
            if required in conditional_refs:
                errors.append(f"Runtime invariant {binding.get('id')} uses conditional opt-in proof")
            if required not in proofs:
                errors.append(f"Runtime invariant {binding.get('id')} lost proof binding {required}")
                continue
            if "::" not in required:
                errors.append(f"Runtime invariant {binding.get('id')} has malformed proof reference {required!r}")
                continue
            path, symbol = required.split("::", 1)
            errors.extend(require_test_source(ROOT / path, symbol))

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
        errors.extend(require_contract_source(ROOT / relative, owner_kind, owner, symbol))
        try:
            native_contract_expected(binding)
        except ValueError as error:
            errors.append(str(error))

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
        errors.extend(require_contract_source(ROOT / relative, owner_kind, owner, symbol))
        try:
            native_contract_expected(binding)
        except ValueError as error:
            errors.append(str(error))

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
        errors.extend(require_test_source(ROOT / relative, symbol))
        if f"{relative}::{symbol}" in conditional_refs:
            errors.append(f"proving test {binding.get('id')} is conditional opt-in evidence")
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
        errors.extend(require_test_source(ROOT / relative, symbol))

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
_ROOT_BUILD_INPUTS = frozenset(
    {
        "Cargo.toml",
        "Cargo.lock",
        "rust-toolchain",
        "rust-toolchain.toml",
        "mise.toml",
        "mise.lock",
    }
)


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
        if (
            not isinstance(relative, str)
            or not relative
            or (
                Path(relative).is_absolute()
                or any(part in {"", ".", ".."} for part in relative.split("/"))
                or "\\" in relative
            )
        ):
            raise ValueError("non-canonical Runtime source dependency")
        return prefix + relative

    common = {
        owned("formal/RuntimeDispatchR1.trace-r1.json"),
        owned("planning/invariants-r1.json"),
        owned("scripts/verify_formal_trace.py"),
        owned("scripts/tests/test_formal_trace.py"),
        # The formal model evidence is consumed through the pinned TLC runner.
        # These shared checker inputs are distinct from individual Rust witnesses.
        owned("formal/toolchain.lock.json"),
        owned("scripts/tla-formal"),
        owned("scripts/tests/test_tla_formal_external_jar.py"),
        owned(trace["formalSpecification"]["modulePath"]),
        owned(trace["formalSpecification"]["configPath"]),
    }
    for item in invariant_manifest.get("invariants", []):
        if item.get("id") in REQUIRED_RUNTIME_INVARIANT_BINDINGS:
            for ref in item.get("proof", []):
                if isinstance(ref, str) and "::" in ref:
                    common.add(owned(ref.split("::", 1)[0]))

    carriers = {
        item["id"]: owned(item["path"]) for key in ("contractSeams", "supportingContracts") for item in trace[key]
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
        path for path in changed_paths if path in _ROOT_BUILD_INPUTS or path.startswith(".cargo/")
    }
    rows = []
    for witness_id, readset in sorted(readsets.items()):
        hits = sorted(readset & changed_paths)
        # Shared Rust callees are not proved closed by the manifest, and
        # global build inputs can invalidate every witness without local diffs.
        standing = (
            "RECHECK_REQUIRED"
            if hits
            else "UNKNOWN"
            if runtime_changed or crosscutting_assumption_changes
            else "REUSE_CANDIDATE"
        )
        rows.append(
            {
                "id": witness_id,
                "standing": standing,
                "matchedChangedPaths": hits,
                "declaredReadSet": sorted(readset),
            }
        )
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
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout

    actual_head = git("rev-parse", "HEAD").decode().strip()
    if head != actual_head:
        raise ValueError(f"impact HEAD is not checkout HEAD: {head} != {actual_head}")
    # Git status can hide edited tracked files when the index carries
    # assume-unchanged or skip-worktree bits. Such flags defeat a source
    # currentness claim even when --porcelain reports an empty worktree.
    source_scope = ("services/runtime", *sorted(_ROOT_BUILD_INPUTS), ".cargo")
    index_rows = git("ls-files", "-v", "-z", "--", *source_scope)
    if any(not row.startswith(b"H ") for row in index_rows.split(b"\x00") if row):
        raise ValueError("impact Runtime/formal build tracked source has unsafe Git index flags")
    if git("status", "--porcelain", "--untracked-files=normal", "--", *source_scope):
        raise ValueError("impact Runtime/formal build worktree is dirty; Git source is not current checkout")
    for revision in (base, head):
        git("cat-file", "-e", f"{revision}^{{commit}}")
    # This mode measures changes FROM a frozen source cut TO this checkout.
    # Comparing two divergent branch tips incorrectly attributes changes
    # already on the target main branch to the candidate PR; callers needing
    # PR integration impact must compare main against an actual merge tree.
    try:
        git("merge-base", "--is-ancestor", base, head)
    except subprocess.CalledProcessError as error:
        if error.returncode == 1:
            raise ValueError(
                "impact base must be an ancestor of checkout HEAD; "
                "use exact integration merge-tree source cut for divergent PRs"
            ) from error
        raise
    data = git("diff", "--no-renames", "--name-only", "-z", base, head, "--")
    return {path.decode("utf-8") for path in data.split(b"\x00") if path}


def _qualified_native_source_head() -> str:
    """Use the same frozen Git checkout guards as Runtime source impact.

    Cargo must not elevate a clean-looking checkout with hidden index flags,
    dirty root toolchain inputs or untracked Runtime sources into a witness.
    This checks two observations; it does not claim atomic source immutability.
    """
    import subprocess

    repo = ROOT.parents[1]
    try:
        head = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.PIPE,
        ).decode("ascii").strip()
        _git_source_changes(head, head)
    except (subprocess.CalledProcessError, UnicodeError) as error:
        raise ValueError("native witness Git SourceCut is unavailable") from error
    return head


def _native_witness_name(witness: dict[str, Any], registered: set[str]) -> str:
    """Require one compiled name at the declared Runtime-core source module."""
    path, symbol = witness["path"], witness["symbol"]
    prefix = "crates/ordivon-runtime-core/src/"
    if not isinstance(path, str) or not path.startswith(prefix) or not path.endswith(".rs"):
        raise ValueError("unsupported native witness path")
    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Za-z_]\w*", symbol):
        raise ValueError("invalid native witness symbol")
    module = path[len(prefix) : -3].replace("/", "::")
    matches = {f"{module}::{symbol}", f"{module}::tests::{symbol}"} & registered
    if len(matches) != 1:
        raise ValueError(f"native test not uniquely registered for {witness['id']}")
    return next(iter(matches))


def _require_native_test_role(
    witness: dict[str, Any],
    registered: set[str],
    ignored: set[str],
    *,
    require_ignored: bool,
) -> str:
    name = _native_witness_name(witness, registered)
    if (name in ignored) != require_ignored:
        raise ValueError(f"native witness {witness['id']} has invalid ignored/always-on evidence role")
    return name


def _require_exact_native_pass(output: str) -> None:
    """Even a successful Cargo exit can mean zero matched Rust tests."""
    reports = [line for line in output.splitlines() if line.startswith("test result:")]
    if len(reports) != 1:
        raise ValueError("native test result missing or ambiguous")
    match = re.fullmatch(
        r"test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; "
        r"\d+ measured; \d+ filtered out; finished in .*",
        reports[0],
    )
    if match is None or tuple(map(int, match.groups())) != (1, 0, 0):
        raise ValueError("native test must execute exactly one PASS and no ignored tests")


def qualify_native_witnesses(trace: dict[str, Any]) -> dict[str, Any]:
    """Bind five declared test identities to actual cargo/libtest executions.

    This deliberately establishes only scoped Rust implementation evidence,
    NOT Rust-to-TLA refinement, whole-input closure, or installed release truth.
    """
    import os
    import subprocess

    cargo = [
        "cargo",
        "test",
        "--offline",
        "--locked",
        "-p",
        "ordivon-runtime-core",
        "--no-default-features",
        "--features",
        "transactional-runtime",
        "--lib",
    ]
    pre_execution_head = _qualified_native_source_head()
    env = dict(os.environ)
    env["CARGO_TERM_COLOR"] = "never"
    # Retain Runtime's existing build-cache directory descriptor across the
    # nested Cargo process when Runtime issued a /proc/self/fd target path.
    target = env.get("CARGO_TARGET_DIR", "")
    fds: tuple[int, ...] = ()
    if target.startswith("/proc/self/fd/") and target.rsplit("/", 1)[1].isdigit():
        fd = int(target.rsplit("/", 1)[1])
        os.fstat(fd)
        fds = (fd,)

    def cargo_check(*args: str) -> subprocess.CompletedProcess[str]:
        process = subprocess.run(
            [*cargo, *args],
            cwd=ROOT,
            env=env,
            pass_fds=fds,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if process.returncode:
            raise ValueError(f"native Cargo failed (exit {process.returncode}): {process.stderr[-350:]}")
        return process

    listing = cargo_check("--", "--list")
    ignored_listing = cargo_check("--", "--ignored", "--list")
    registered = {line.removesuffix(": test") for line in listing.stdout.splitlines() if line.endswith(": test")}
    ignored_names = {
        line.removesuffix(": test") for line in ignored_listing.stdout.splitlines() if line.endswith(": test")
    }
    contract_rows = []
    qualified_contract_tests: set[str] = set()
    for binding in [*trace["contractSeams"], *trace["supportingContracts"]]:
        native_name = native_contract_expected(binding)
        if native_name not in registered or native_name in ignored_names:
            raise ValueError(f"compiler-owned contract witness absent/ignored: {native_name}")
        if native_name not in qualified_contract_tests:
            executed = cargo_check(native_name, "--", "--exact")
            _require_exact_native_pass(executed.stdout)
            qualified_contract_tests.add(native_name)
        contract_rows.append(
            {
                "id": binding["id"],
                "nativeName": native_name,
                "standing": "COMPILED_TYPED_WITNESS_PASS",
            }
        )

    witness_rows = []
    for witness in trace["provingTests"]:
        name = _require_native_test_role(
            witness,
            registered,
            ignored_names,
            require_ignored=False,
        )
        result = cargo_check(name, "--", "--exact")
        _require_exact_native_pass(result.stdout)
        witness_rows.append(
            {
                "id": witness["id"],
                "nativeName": name,
                "standing": "EXECUTED_PASS",
            }
        )
    opt_in_rows = []
    for witness in trace["conditionalAcceptanceTests"]:
        name = _require_native_test_role(
            witness,
            registered,
            ignored_names,
            require_ignored=True,
        )
        opt_in_rows.append(
            {
                "id": witness["id"],
                "nativeName": name,
                "standing": "COMPILED_IGNORED_NOT_EXECUTED",
            }
        )

    def provenance(command: list[str]) -> str:
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            pass_fds=fds,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if process.returncode:
            raise ValueError(f"native witness prerequisite failed: {command[0]}")
        return process.stdout.strip()

    source_head = _qualified_native_source_head()
    if source_head != pre_execution_head:
        raise ValueError("native source checkout HEAD changed during Cargo witnesses")
    toolchain = provenance(["rustc", "-vV"])
    cargo_version = provenance(["cargo", "--version"])
    rust_env = {
        key: env.get(key, "")
        for key in (
            "RUSTFLAGS",
            "CARGO_ENCODED_RUSTFLAGS",
            "RUSTDOCFLAGS",
            "CARGO_BUILD_TARGET",
            "RUSTC_WRAPPER",
            "CARGO_HOME",
        )
    }

    return {
        "kind": "ordivon.runtime-native-test-witness",
        "truthRole": "scoped-code-test-evidence-not-formal-refinement",
        "witnesses": witness_rows,
        "conditionalOptInWitnesses": opt_in_rows,
        "typedContractWitnesses": contract_rows,
        "sourceHead": source_head,
        "declaredRustInputsClean": True,
        "sourceQualification": "EXACT_GIT_SOURCE_CUT_PRE_AND_POST_NATIVE_CARGO",
        "sourceSnapshotCompleteness": "PRE_POST_NOT_ATOMIC; EXTERNAL_READSET_UNKNOWN",
        "cargoVersion": cargo_version,
        "rustcVersionVerbose": toolchain,
        "buildEnvironment": rust_env,
        "cargoProfile": {
            "package": "ordivon-runtime-core",
            "feature": "transactional-runtime",
            "noDefaultFeatures": True,
            "lib": True,
            "locked": True,
            "offline": True,
        },
        "proofReuseAdmissible": False,
        "modelToImplementationRefinement": "UNKNOWN",
        "installedCurrentness": "UNKNOWN",
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--native-witnesses", action="store_true")
    parser.add_argument("--impact-base", help="exact Git source base SHA")
    parser.add_argument("--impact-head", help="exact Git source HEAD SHA")
    args = parser.parse_args([] if argv is None else argv)
    if bool(args.impact_base) != bool(args.impact_head):
        parser.error("--impact-base and --impact-head must be supplied together")
    if args.native_witnesses and args.impact_base:
        parser.error("--native-witnesses cannot be combined with --impact-base")
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

    try:
        receipt = qualify_native_witnesses(trace)
    except (OSError, ValueError, __import__("subprocess").TimeoutExpired) as error:
        print(f"formal native witness: UNKNOWN ({error})", file=sys.stderr)
        return 1
    if args.native_witnesses:
        print(json.dumps(receipt, sort_keys=True))
    else:
        print(
            "formal trace: PASS (scoped manifest, Cargo native 5/5 executed "
            "tests, 4/4 typed seams, 2 opt-in ignored; no Rust-to-TLA proof)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
