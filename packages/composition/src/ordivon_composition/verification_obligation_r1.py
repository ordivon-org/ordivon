#!/usr/bin/env python3
"""Task-local verification-obligation compilation and verifier-binding resolution.

R1 deliberately compiles only existing Cognitive Circuit composition gates. It does not
invent domain properties, discover verifiers, rank providers, execute verification, grant
authority, or establish domain completion. Caller-authored task-local bindings identify the
verifier/provider that will discharge each obligation through the existing Composition Gate
result contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .cognitive_circuit_r1 import (
    CircuitContractError,
    _load_json,
    _load_json_value,
    _validate_schema,
    canonical_digest,
    compile_manifest,
)
from .verification_impact import (
    _cyclic_proof_members as _cyclic_proof_members,
)
from .verification_impact import (
    classify_observed_environment_delta as classify_observed_environment_delta,
)
from .verification_impact import (
    compare_gate_source_scopes as compare_gate_source_scopes,
)
from .verification_impact import (
    select_impacted_obligations as select_impacted_obligations,
)
from .verification_impact import (
    select_source_readset_impacts as select_source_readset_impacts,
)

ROOT = Path(__file__).resolve().parent
OBLIGATION_SET_SCHEMA = ROOT / "schemas" / "verification-obligation-set-v1.schema.json"
BINDING_SET_SCHEMA = ROOT / "schemas" / "verifier-binding-set-v1.schema.json"
RESOLUTION_SCHEMA = ROOT / "schemas" / "verifier-resolution-v1.schema.json"


def _load_task_local_json_list(path: Path) -> list[Any]:
    """Reject ambiguous proof/unknown-ref input before impact selection.

    This reuses the existing Composition JSON admission primitives; caller
    reports remain untrusted and acquire no execution or proof authority.
    """
    value = _load_json_value(path)
    if not isinstance(value, list):
        raise CircuitContractError("task-local proof input must be a JSON array")
    return value


def _immutable_git_manifest(
    repo: Path, commit: str, path: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    """Read a regular Git blob at an exact commit; never consult the mutable checkout.

    This establishes only SOURCE bytes, not authenticated consumer evidence or
    installed/current verifier proof.
    """
    relative = path.as_posix()
    if (
        path.is_absolute()
        or not relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
        or chr(0) in relative
    ):
        raise CircuitContractError(
            "source-bound impact needs an exact Git cut and canonical relative path"
        )

    def git(*argv: str) -> bytes:
        try:
            # Exact SourceCut addresses Git's original objects, not any
            # mutable refs/replace overlay supplied by the local repository.
            return subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(repo), *argv],
                stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise CircuitContractError("Git source cut or regular blob unavailable") from exc

    # Git supports both SHA-1 (40) and SHA-256 (64) storage formats.
    # Ask the repository for the actual object format rather than adopting
    # one hash algorithm as an implicit global LEGO/source-cut type.
    storage_format = git("rev-parse", "--show-object-format=storage").strip()
    if storage_format == b"sha1":
        object_id_width = 40
    elif storage_format == b"sha256":
        object_id_width = 64
    else:
        raise CircuitContractError("unsupported Git repository object format")
    if re.fullmatch(rf"[0-9a-f]{{{object_id_width}}}", commit) is None:
        raise CircuitContractError("source-bound impact needs an exact Git commit object ID")
    if git("cat-file", "-t", commit).strip() != b"commit":
        raise CircuitContractError("Git SourceCut must identify an immutable commit")
    # ls-tree rejects gitlinks, symlinks, missing path, and pathspec ambiguity.
    entries = [
        row
        for row in git("ls-tree", "-z", "--full-tree", commit, "--", relative).split(b"\x00")
        if row
    ]
    if len(entries) != 1 or b"\t" not in entries[0]:
        raise CircuitContractError("exact manifest Git path unavailable")
    meta, name = entries[0].split(b"\t", 1)
    if name.decode("utf-8", "surrogateescape") != relative:
        raise CircuitContractError("manifest pathspec did not identify an exact path")
    mode, kind, blob = meta.split()
    if kind != b"blob" or mode not in (b"100644", b"100755"):
        raise CircuitContractError("manifest must be a regular Git file")
    raw = git("cat-file", "blob", commit + ":" + relative)
    return _load_json(path, source_bytes=raw), {
        "commit": commit,
        "objectFormat": storage_format.decode("ascii"),
        "path": relative,
        "blobId": blob.decode("ascii"),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "truthRole": "git-immutable-source-only-not-proof-reuse",
    }


def _unique_by(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row[key]
        if row_id in result:
            raise CircuitContractError(f"duplicate {label}: {row_id}")
        result[row_id] = row
    return result


def _obligation_from_gate(
    *,
    circuit_ref: dict[str, str],
    gate: dict[str, Any],
) -> dict[str, Any]:
    obligation: dict[str, Any] = {
        "gateId": gate["id"],
        "sourceGateDigest": canonical_digest(gate),
        "circuitRef": dict(circuit_ref),
        "producerStageId": gate["producerStageId"],
        "consumerStageId": gate["consumerStageId"],
        "assumption": gate["assumption"],
        "guarantee": gate["guarantee"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "supportScope": gate["supportScope"],
        "required": gate["required"],
        "requiredStanding": "SATISFIED",
        "resultKind": "ordivon.composition-gate-result",
        "nonClaims": [
            "This obligation is a task-local projection of an existing Composition Gate.",
            "Discharging it establishes only the named support scope, not domain acceptance.",
        ],
    }
    obligation["obligationDigest"] = canonical_digest(obligation)
    return obligation


def compile_verification_obligations(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compile R1 Composition Gates into exact task-local verification obligations."""

    compiled = compile_manifest(manifest)
    circuit_ref = {
        "id": manifest["circuitId"],
        "digest": compiled["manifestDigest"],
    }
    obligations = [
        _obligation_from_gate(circuit_ref=circuit_ref, gate=gate)
        for gate in sorted(manifest["gateRequirements"], key=lambda item: item["id"])
    ]
    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.verification-obligation-set",
        "truthRole": "task-local-non-authoritative-verification-obligation-projection",
        "circuitRef": circuit_ref,
        "obligations": obligations,
        "requiredGateIds": sorted(
            obligation["gateId"] for obligation in obligations if obligation["required"]
        ),
        "nonClaims": [
            "This projection does not discover, select, rank, or execute verifiers.",
            "This projection grants no Tool, credential, workflow, retry, or domain authority.",
            "Verification closure does not establish domain acceptance.",
        ],
    }
    projection["obligationSetDigest"] = canonical_digest(projection)
    _validate_schema(projection, OBLIGATION_SET_SCHEMA, "verification obligation set")
    return projection


def validate_obligation_set(value: dict[str, Any]) -> None:
    _validate_schema(value, OBLIGATION_SET_SCHEMA, "verification obligation set")
    obligations = _unique_by(value["obligations"], "gateId", "verification obligation gateId")

    expected_required = sorted(
        obligation["gateId"] for obligation in obligations.values() if obligation["required"]
    )
    if value["requiredGateIds"] != expected_required:
        raise CircuitContractError("verification obligation requiredGateIds mismatch")

    for obligation in obligations.values():
        if obligation["circuitRef"] != value["circuitRef"]:
            raise CircuitContractError(
                f"verification obligation circuitRef mismatch: {obligation['gateId']}"
            )
        embedded = obligation["obligationDigest"]
        base = dict(obligation)
        del base["obligationDigest"]
        if canonical_digest(base) != embedded:
            raise CircuitContractError(
                f"verification obligation digest mismatch: {obligation['gateId']}"
            )

    set_digest = value["obligationSetDigest"]
    base_set = dict(value)
    del base_set["obligationSetDigest"]
    if canonical_digest(base_set) != set_digest:
        raise CircuitContractError("verification obligation set digest mismatch")


def resolve_verifier_bindings(
    obligation_set: dict[str, Any],
    binding_set: dict[str, Any],
) -> dict[str, Any]:
    """Validate exact caller-authored verifier bindings against one obligation set.

    "Resolve" here means deterministic binding validation only. This function performs no
    registry lookup, provider discovery, availability probe, ranking, or verifier execution.
    """

    validate_obligation_set(obligation_set)
    _validate_schema(binding_set, BINDING_SET_SCHEMA, "verifier binding set")

    if binding_set["circuitRef"] != obligation_set["circuitRef"]:
        raise CircuitContractError("verifier binding set circuitRef mismatch")
    if binding_set["obligationSetDigest"] != obligation_set["obligationSetDigest"]:
        raise CircuitContractError("verifier binding set targets a stale/different obligation set")

    obligations = _unique_by(
        obligation_set["obligations"],
        "gateId",
        "verification obligation gateId",
    )
    bindings = _unique_by(binding_set["bindings"], "gateId", "verifier binding gateId")

    unknown = sorted(set(bindings) - set(obligations))
    if unknown:
        raise CircuitContractError(f"verifier bindings reference unknown obligations: {unknown}")

    resolved: list[dict[str, Any]] = []
    for gate_id in sorted(bindings):
        binding = bindings[gate_id]
        obligation = obligations[gate_id]
        if binding["obligationDigest"] != obligation["obligationDigest"]:
            raise CircuitContractError(f"verifier binding obligation digest mismatch: {gate_id}")
        if binding["verifierOwnerId"] != obligation["verifierOwnerId"]:
            raise CircuitContractError(f"verifier binding owner mismatch: {gate_id}")
        if binding["supportScope"] != obligation["supportScope"]:
            raise CircuitContractError(f"verifier binding support scope mismatch: {gate_id}")

        resolved.append(
            {
                "gateId": gate_id,
                "obligationDigest": obligation["obligationDigest"],
                "verifierOwnerId": binding["verifierOwnerId"],
                "verifierRef": dict(binding["verifierRef"]),
                "verifierClass": binding["verifierClass"],
                "nativeSpecificationRef": (
                    None
                    if binding["nativeSpecificationRef"] is None
                    else dict(binding["nativeSpecificationRef"])
                ),
                "supportScope": binding["supportScope"],
            }
        )

    missing_required = sorted(
        gate_id
        for gate_id, obligation in obligations.items()
        if obligation["required"] and gate_id not in bindings
    )
    unbound_optional = sorted(
        gate_id
        for gate_id, obligation in obligations.items()
        if not obligation["required"] and gate_id not in bindings
    )
    # An empty set of required gates cannot witness any verified cross-owner
    # contract. Binding completeness is an evidence claim, not vacuous truth.
    required_ids = {gate_id for gate_id, item in obligations.items() if item["required"]}
    mechanical_resolution = bool(required_ids) and not missing_required
    standing = "VERIFIER_BINDINGS_RESOLVED" if mechanical_resolution else "VERIFIER_BINDINGS_OPEN"

    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.verifier-resolution",
        "truthRole": "task-local-non-authoritative-verifier-binding-projection",
        "circuitRef": dict(obligation_set["circuitRef"]),
        "obligationSetDigest": obligation_set["obligationSetDigest"],
        "bindingSetDigest": canonical_digest(binding_set),
        "standing": standing,
        "resolvedBindings": resolved,
        "missingRequiredGateIds": missing_required,
        "unboundOptionalGateIds": unbound_optional,
        "mechanicalResolution": mechanical_resolution,
        "executionAuthorityGranted": False,
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "Resolution means only that every required task-local obligation has an exact "
            "caller-authored verifier binding whose owner, obligation digest, and support "
            "scope match. It does not prove verifier availability, execute verification, "
            "grant authority, discharge a gate, or establish domain acceptance."
        ),
    }
    projection["resolutionDigest"] = canonical_digest(projection)
    _validate_schema(projection, RESOLUTION_SCHEMA, "verifier resolution")
    return projection


def select_manifest_gate_impacts(
    *,
    previous_manifest: dict[str, Any],
    current_manifest: dict[str, Any],
    previous_binding_set: dict[str, Any] | None = None,
    current_binding_set: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare exact task-local manifest property inputs through the existing selector.

    This handles only the two supplied, already-validated manifest JSON values.
    It does not certify source provenance, an Owner query/readset, installed
    currentness, or verifier assumptions outside those manifests. Unchanged
    gate proofs therefore remain UNKNOWN, never proof-reuse qualified.
    """
    previous = compile_verification_obligations(previous_manifest)
    current = compile_verification_obligations(current_manifest)
    if previous_manifest["circuitId"] != current_manifest["circuitId"]:
        raise CircuitContractError("cannot compare different circuit identities")

    # Reuse the existing R2.1 source-scope operator. Its bounded upstream
    # closure already understands producer/consumer stages, incoming edges,
    # method/capability bindings and other premises of the same consumer.
    # Computing another all-non-Gate hash would invalidate unrelated branches.
    scoped = compare_gate_source_scopes(previous_manifest, current_manifest)
    all_current = {item["gateId"] for item in current["obligations"]}
    added = scoped["addedGateIds"]
    removed = scoped["removedGateIds"]

    # Actual global context affects every Gate, including negative membership
    # queries. The scoped comparator separately handles all local source inputs.
    def shared_context(manifest: dict[str, Any]) -> str:
        return canonical_digest(
            {
                key: manifest[key]
                for key in (
                    "schemaVersion",
                    "kind",
                    "circuitId",
                    "objectiveRef",
                    "unresolvedAssumptions",
                    "nonClaims",
                )
            }
        )

    # Negative Gate membership is already part of each bounded consumer's
    # upstreamGates readset in compare_gate_source_scopes. Treating any add/
    # remove as a global change would invalidate independent Gate branches.
    shared_changed = shared_context(previous_manifest) != shared_context(current_manifest)
    local_changed = sorted(set(scoped["changedGateIds"]) | set(added))

    if (previous_binding_set is None) != (current_binding_set is None):
        raise CircuitContractError("both previous and current verifier binding sets are required")

    # These exact binding resolutions validate a caller-authored claim; they do
    # not authenticate a verifier installation, execution or proof. Keep the
    # binding change separate from the Gate's source/contract change.
    binding_pair = previous_binding_set is not None and current_binding_set is not None
    changed_verifier_gates: list[str] = []
    previous_resolution = None
    current_resolution = None
    if binding_pair:
        previous_resolution = resolve_verifier_bindings(previous, previous_binding_set)
        current_resolution = resolve_verifier_bindings(current, current_binding_set)

        # Each binding resolver already checks the exact obligation digest for
        # its own SourceCut. That digest also includes the whole manifest and
        # changes for unrelated Gates: it is NOT a verifier-identity delta.
        # Actual Gate proposition changes are handled by source:gate refs.
        def verifier_identity(row: dict[str, Any]) -> dict[str, Any]:
            return {key: value for key, value in row.items() if key != "obligationDigest"}

        old_bindings = {
            row["gateId"]: verifier_identity(row) for row in previous_resolution["resolvedBindings"]
        }
        new_bindings = {
            row["gateId"]: verifier_identity(row) for row in current_resolution["resolvedBindings"]
        }
        changed_verifier_gates = sorted(
            gate_id
            for gate_id in all_current
            if old_bindings.get(gate_id) != new_bindings.get(gate_id)
        )

    shared_ref = "source:manifest-shared"

    def gate_ref(gate_id: str) -> str:
        return f"source:gate:{gate_id}"

    def verifier_ref(gate_id: str) -> str:
        return f"binding:verifier:{gate_id}"

    authority_refs = [shared_ref] + [gate_ref(key) for key in sorted(all_current)]
    if binding_pair:
        authority_refs.extend(verifier_ref(key) for key in sorted(all_current))
    obligations = [
        {
            "id": f"proof:gate:{gate_id}",
            "dependsOn": [shared_ref, gate_ref(gate_id)]
            + ([verifier_ref(gate_id)] if binding_pair else []),
            # A syntactically complete manifest does NOT account for verifier,
            # installed code, authorization, environment or dynamic consumer reads.
            "dependenciesComplete": False,
        }
        for gate_id in sorted(all_current)
    ]
    changed_refs = [gate_ref(gate_id) for gate_id in local_changed]
    changed_refs.extend(verifier_ref(gate_id) for gate_id in changed_verifier_gates)
    if shared_changed:
        changed_refs.append(shared_ref)
    selection = select_impacted_obligations(
        authority_refs=authority_refs,
        obligations=obligations,
        changed_refs=changed_refs,
    )
    projection = {
        "kind": "ordivon.task-local-manifest-gate-impact",
        "truthRole": "source-manifest-projection-not-proof-admission",
        "previousObligationSetDigest": previous["obligationSetDigest"],
        "currentObligationSetDigest": current["obligationSetDigest"],
        "sharedManifestContextChanged": shared_changed,
        "changedLocalGateIds": local_changed,
        "addedGateIds": added,
        "removedGateIds": removed,
        "selection": selection,
        "proofReuseAdmissible": False,
        "nonClaims": [
            "The manifest objects are caller supplied; source query provenance is not certified.",
            "Shared context covers global manifest premises and Gate membership only.",
            "Gate source deltas reuse existing scoped upstream closure.",
            "An unchanged gate with unresolved verifier/environment deps stays UNKNOWN.",
            "Removed gates need separate actual consumer and proof-retirement qualification.",
        ],
    }
    if binding_pair:
        projection.update(
            {
                "changedVerifierBindingGateIds": changed_verifier_gates,
                "previousVerifierResolutionDigest": previous_resolution["resolutionDigest"],
                "currentVerifierResolutionDigest": current_resolution["resolutionDigest"],
                "verifierBindingComparisonQualification": "CALLER_AUTHORED_BINDINGS_ONLY",
            }
        )
        projection["nonClaims"].append(
            "Verifier/artifact/native specification references are caller-authored; "
            "their digest equality or binding resolution is not a verified runtime readset."
        )
    return projection


def _requalify_git_source_delta(repo: Path, delta: dict[str, Any]) -> dict[str, Any]:
    """Recompute one caller-supplied Git delta through the native source owner."""

    if not isinstance(delta, dict) or delta.get("kind") != "ordivon.git-source-membership-delta":
        raise CircuitContractError("select-impact needs an exact Git source delta")
    if (
        delta.get("gitSourceQueryComplete") is not True
        or delta.get("proofReuseAdmissible") is not False
    ):
        raise CircuitContractError("select-impact cannot promote unqualified Git source evidence")
    try:
        cuts = delta.get("sourceCuts")
        if not isinstance(cuts, dict):
            raise ValueError("sourceCuts must specify immutable Git commits")
        owner_tool = Path(__file__).resolve().parents[4] / "tools/repo/source_history_legos.py"
        if not owner_tool.is_file() or owner_tool.is_symlink():
            raise ValueError("Git owner query entrypoint unavailable")

        def require_qualified_owner_tool() -> None:
            # Exact provenance covers the finite direct local producer readset.
            for relative in (
                "tools/repo/source_history_legos.py",
                "tools/repo/affected_owners.py",
            ):
                producer = owner_tool.parents[2] / relative
                tree_entry = subprocess.run(
                    [
                        "git",
                        "--no-replace-objects",
                        "-C",
                        str(owner_tool.parents[2]),
                        "ls-tree",
                        "-z",
                        "--full-tree",
                        "HEAD",
                        "--",
                        relative,
                    ],
                    capture_output=True,
                    check=False,
                )
                expected = (
                    rb"(100644|100755) blob [0-9a-f]{40,64}\t"
                    + re.escape(relative.encode("utf-8"))
                    + rb"\x00"
                )
                if tree_entry.returncode != 0 or re.fullmatch(expected, tree_entry.stdout) is None:
                    raise CircuitContractError(
                        "native Git query producer Git tree mode is not regular: " + relative
                    )
                committed = subprocess.run(
                    [
                        "git",
                        "--no-replace-objects",
                        "-C",
                        str(owner_tool.parents[2]),
                        "show",
                        "HEAD:" + relative,
                    ],
                    capture_output=True,
                    check=False,
                )
                if (
                    committed.returncode != 0
                    or not producer.is_file()
                    or producer.is_symlink()
                    or committed.stdout != producer.read_bytes()
                ):
                    raise CircuitContractError(
                        "native Git query producer differs from its Git SourceCut: " + relative
                    )

        require_qualified_owner_tool()
        native_query = subprocess.run(
            [
                sys.executable,
                str(owner_tool),
                "--repo",
                str(repo),
                "--left",
                cuts.get("previous"),
                "--right",
                cuts.get("current"),
                "--impact-prefix",
                delta.get("queryPrefix"),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        require_qualified_owner_tool()
        if native_query.returncode != 0:
            raise ValueError("native Git source query failed")
        qualified = json.loads(native_query.stdout)
    except CircuitContractError:
        raise
    except (ValueError, OSError, TypeError) as exc:
        raise CircuitContractError(
            "select-impact requires independently recomputable native Git scope"
        ) from exc
    if qualified != delta:
        raise CircuitContractError(
            "select-impact Git report differs from exact native source delta"
        )
    roots, changes = qualified["authorityRefs"], qualified["changedRefs"]
    if (
        not isinstance(roots, list)
        or not isinstance(changes, list)
        or any(not isinstance(ref, str) for ref in roots + changes)
        or not set(changes).issubset(set(roots))
    ):
        raise CircuitContractError(
            "Git impact changed refs must belong to same scoped authority set"
        )
    return qualified


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile-obligations")
    compile_parser.add_argument("manifest", type=Path)

    resolve_parser = sub.add_parser("resolve-bindings")
    resolve_parser.add_argument("obligation_set", type=Path)
    resolve_parser.add_argument("binding_set", type=Path)

    observed_parser = sub.add_parser("impact-observations")
    observed_parser.add_argument("previous_observations", type=Path)
    observed_parser.add_argument("current_observations", type=Path)
    observed_parser.add_argument("task_local_graph", type=Path)

    impact_parser = sub.add_parser("select-impact")
    impact_parser.add_argument("git_source_delta", type=Path)
    impact_parser.add_argument("obligations", type=Path)
    # A caller-supplied JSON report is not native Git evidence. Verify it
    # against the exact immutable source cuts before using it for scheduling.
    impact_parser.add_argument("--repo", type=Path, required=True)
    impact_parser.add_argument("--unknown-refs", type=Path)

    readset_parser = sub.add_parser("impact-readsets")
    readset_parser.add_argument("git_source_delta", type=Path)
    readset_parser.add_argument("source_readset_evidence", type=Path)
    readset_parser.add_argument("--repo", type=Path, required=True)

    manifest_parser = sub.add_parser("impact-manifests")
    manifest_parser.add_argument("previous_manifest", type=Path)
    manifest_parser.add_argument("current_manifest", type=Path)
    manifest_parser.add_argument("--previous-bindings", type=Path)
    manifest_parser.add_argument("--current-bindings", type=Path)
    manifest_parser.add_argument("--git-repo", type=Path)
    manifest_parser.add_argument("--previous-sourcecut")
    manifest_parser.add_argument("--current-sourcecut")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "compile-obligations":
            result = compile_verification_obligations(_load_json(args.manifest))
        elif args.command == "resolve-bindings":
            result = resolve_verifier_bindings(
                _load_json(args.obligation_set),
                _load_json(args.binding_set),
            )
        elif args.command == "impact-manifests":
            requested = (
                args.git_repo is not None,
                args.previous_sourcecut is not None,
                args.current_sourcecut is not None,
            )
            if any(requested) and not all(requested):
                raise CircuitContractError(
                    "Git source mode requires repository and both exact commits"
                )
            if all(requested):
                before, before_source = _immutable_git_manifest(
                    args.git_repo, args.previous_sourcecut, args.previous_manifest
                )
                after, after_source = _immutable_git_manifest(
                    args.git_repo, args.current_sourcecut, args.current_manifest
                )
            else:
                before, after = (
                    _load_json(args.previous_manifest),
                    _load_json(args.current_manifest),
                )
            result = select_manifest_gate_impacts(
                previous_manifest=before,
                current_manifest=after,
                previous_binding_set=(
                    None if args.previous_bindings is None else _load_json(args.previous_bindings)
                ),
                current_binding_set=(
                    None if args.current_bindings is None else _load_json(args.current_bindings)
                ),
            )
            if all(requested):
                result["gitSourceCuts"] = {"previous": before_source, "current": after_source}
        elif args.command == "impact-observations":
            # Natural owners still own the observations and physical receipts.
            # This is a task-local, non-executing source-to-proof adapter.
            graph = _load_json(args.task_local_graph)
            if not isinstance(graph, dict) or set(graph) != {"authorityRefs", "obligations"}:
                raise CircuitContractError(
                    "impact-observations requires task-local authorityRefs and obligations"
                )
            observed_before = _load_json(args.previous_observations)
            observed_after = _load_json(args.current_observations)
            if set(observed_before) != {"observations"} or set(observed_after) != {"observations"}:
                raise CircuitContractError(
                    "impact-observations requires exact observations envelopes"
                )
            # The graph supplies the *known finite* dependency scope. Missing
            # in both snapshots must not become a false reuse candidate.
            declared_environment_refs = [
                ref
                for ref in graph["authorityRefs"]
                if isinstance(ref, str)
                and ref.partition(":")[0]
                in {
                    "config",
                    "environment",
                    "installed",
                    "authority",
                    "provider",
                    "external",
                    "effect",
                }
            ]
            delta = classify_observed_environment_delta(
                previous=observed_before["observations"],
                current=observed_after["observations"],
                required_refs=declared_environment_refs,
            )
            selected = select_impacted_obligations(
                authority_refs=graph["authorityRefs"],
                obligations=graph["obligations"],
                changed_refs=delta["changedRefs"],
                unknown_refs=delta["unknownRefs"],
            )
            result = {
                "kind": "ordivon.task-local-environment-effect-impact",
                "truthRole": "caller-supplied-observations-not-owner-certified",
                "observationDelta": delta,
                "selection": selected,
                "proofReuseAdmissible": False,
            }
        elif args.command == "select-impact":
            qualified = _requalify_git_source_delta(args.repo, _load_json(args.git_source_delta))
            obligations = _load_task_local_json_list(args.obligations)
            unknown = _load_task_local_json_list(args.unknown_refs) if args.unknown_refs else None
            result = select_impacted_obligations(
                authority_refs=qualified["authorityRefs"],
                obligations=obligations,
                changed_refs=qualified["changedRefs"],
                unknown_refs=unknown,
            )
        elif args.command == "impact-readsets":
            # Repo's path members are Git byte strings, not necessarily UTF-8.
            # Keep all non-path JSON values on the strict Unicode-scalar lane.
            qualified = _requalify_git_source_delta(
                args.repo,
                _load_json(
                    args.git_source_delta,
                    git_byte_path_fields=frozenset(
                        {"addedPaths", "removedPaths", "changedValuePaths"}
                    ),
                ),
            )
            evidence = _load_json(
                args.source_readset_evidence,
                git_byte_path_fields=frozenset({"sourcePaths"}),
            )
            result = select_source_readset_impacts(
                git_source_delta=qualified,
                source_readset_evidence=evidence,
            )
        else:
            raise CircuitContractError(f"unknown verification command: {args.command}")
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"verification obligation R1 failed: {exc}") from exc

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
