from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
from decimal import Decimal
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Any

import tomllib

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "docs" / "architecture" / "CURRENT_ARCHITECTURE.md"
DEPLOYED = ROOT / "docs" / "architecture" / "deployed-architecture-r1.json"
PLUGIN = ROOT / "extensions" / "ordivon-control-plane" / "mcp.json"
ROUTES = ROOT / "services" / "gateway" / "src" / "ordivon_gateway" / "routes.py"
GATEWAY_MCP = ROOT / "services" / "gateway" / "src" / "ordivon_gateway" / "mcp_server.py"
GATEWAY_SURFACE_MANIFEST = ROOT / "services" / "gateway" / "mcp-surface.json"
HOST_NORTHBOUND_ACCEPTANCE = ROOT / "docs" / "architecture" / "gateway-swf-northbound-acceptance-20260924.json"
METHOD_ROUTER = ROOT / ".agents" / "skills" / "method-router" / "SKILL.md"
README = ROOT / "README.md"

TEMPO_CONFIG = ROOT / "platform" / "workstation" / "observability" / "tempo.yaml"
VECTOR_CONFIG = ROOT / "platform" / "workstation" / "observability" / "vector.yaml"
GRAFANA_DATASOURCES = ROOT / "platform" / "workstation" / "observability" / "grafana-datasources.yaml"
HEAVY_TARGET = ROOT / "platform" / "workstation" / "systemd" / "ordivon-observability-heavy.target"
TRACE_ACCEPTANCE = ROOT / "docs" / "architecture" / "persistent-trace-backend-acceptance-20260921.json"
TEMPO_QUADLET = ROOT / "platform" / "workstation" / "tempo" / "ordivon-tempo.container"

HISTORICAL = {
    ROOT / "docs" / "architecture" / "ARCHITECTURE_CONVERGENCE_A01R2.md":
        "Historical standing: SUPERSEDED FOR CURRENT DEPLOYMENT STATUS",
    ROOT / "docs" / "architecture" / "ORDIVON_COMPOSITION_ARCHITECTURE_EXECUTION_PLAN_R1.md":
        "Historical standing: EXECUTED / SUPERSEDED FOR CURRENT STATE",
    ROOT / "docs" / "architecture" / "AGENT_PLUGIN_R4_ACCEPTANCE_20260921.md":
        "Historical standing: SUPERSEDED BY C02/D01 FOR CURRENT ENDPOINT TOPOLOGY",
}

EXPECTED_CAPABILITIES = {
    "artifact.runtime",
    "continuity.external",
    "execution.linux",
    "execution.windows",
}

EXPECTED_HOST_NORTHBOUND_TOOLS = {
    'actor.declare',
    'attention.ack',
    'attention.delta',
    'attention.get',
    'host.status',
    'message.post',
    'message.relation.add',
    'message.search',
    'space.create',
    'space.get',
    'space.list',
    'space.participation.set',
    'subscription.follow',
    'subscription.list',
    'subscription.unfollow',
    'topic.create',
    'topic.resume',
    'work.create',
    'work.get',
    'work.list',
    'work.snapshot.commit',
}


class ArchitectureDocsError(ValueError):
    pass


# The existing GIT-01 typed decision relation is shared by the read-only
# evidence union AND the final architecture checker. No second vocabulary.
GIT01_ALLOWED_DISPOSITIONS = frozenset({
        "SKIP_DUPLICATE_CHERRY_PICK", "SKIP_OLDER_PIN", "SKIP_OLDER_SOURCECUT",
        "SKIP_UNCONSUMED_PERMISSION",
        "NO_WHOLE_COMMIT_REPLAY_WITHOUT_PRODUCER_AUTHORITY",
        "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER", "SKIP_CANCELLED_HISTORY_PAIR",
        "SKIP_RETIRED_UNCONSUMED", "SKIP_OLDER_TOOLCHAIN_CHERRY_PICK",
        "SKIP_IDENTICAL_TIP_WITH_NATIVE_CONSUMER",
        "PORT_REQUIRED_OWNER_EFFECT",
})
GIT01_ALLOWED_EVIDENCE_SCOPES = frozenset({
        "NATIVE_CONSUMER_PASS", "EXACT_GIT_BLOBS",
        "SOURCE_PROVIDER_NEWER_NO_NATIVE_NIX_PROOF",
        "LATEST_STABLE_SOURCE_NO_UPGRADE",
        "CURRENT_CONSUMER_ELSEWHERE_NO_OLD_EFFECT",
        "FROZEN_GATEWAY_CONSUMER_ONLY",
        "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN",
        "CURRENT_TOOLCHAIN_SUPERSEDES_OLD_LOCK_AND_NATIVE_TEST_PASS",
        "EXACT_EXECUTABLE_BLOB_WITH_NONWINDOWS_HOLD_ONLY",
        "EXACT_GIT_BLOB_AND_NATIVE_CONSUMER_PASS",
        "EXACT_OWNER_LOCKED_COMPONENTS_NO_LIVE_PROVIDER",
        "SOURCE_ABSENCE_ONLY_NO_NATIVE_CDC",
})

GIT01_SCOPE_DISPOSITION = {
            "SOURCE_PROVIDER_NEWER_NO_NATIVE_NIX_PROOF": "SKIP_OLDER_PIN",
            "SOURCE_ABSENCE_ONLY_NO_NATIVE_CDC": "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER",
            "CURRENT_CONSUMER_ELSEWHERE_NO_OLD_EFFECT": "SKIP_UNCONSUMED_PERMISSION",
            "EXACT_OWNER_LOCKED_COMPONENTS_NO_LIVE_PROVIDER": "SKIP_DUPLICATE_CHERRY_PICK",
            "FROZEN_GATEWAY_CONSUMER_ONLY": "NO_WHOLE_COMMIT_REPLAY_WITHOUT_PRODUCER_AUTHORITY",
}

def _load_json(path: Path, *, source_bytes: bytes | None = None) -> dict[str, Any]:
    """Use unambiguous standard JSON bytes for Owner and evidence registration.

    Python's default last-key-wins and NaN extensions are not a sound source
    identity for a formal claim. Keep this guard at the existing repo boundary.
    """
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ArchitectureDocsError(f"duplicate JSON object key: {key!r} in {path}")
            result[key] = item
        return result

    def finite_constant(value: str) -> None:
        raise ArchitectureDocsError(f"non-finite JSON constant: {value} in {path}")

    def representable_float(value: str) -> float:
        # A JSON exponent is legal syntax but must not silently change a
        # nonzero finite source claim into infinity or zero at the owner seam.
        parsed = float(value)
        if not math.isfinite(parsed) or (
            parsed == 0.0 and not Decimal(value).is_zero()
        ):
            raise ArchitectureDocsError(f"unrepresentable JSON number: {value} in {path}")
        return parsed

    value = json.loads(
        source_bytes.decode("utf-8") if source_bytes is not None
        else path.read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=finite_constant,
        parse_float=representable_float,
    )
    if not isinstance(value, dict):
        raise ArchitectureDocsError(f"{path} root must be an object")
    return value


# Problem LEGO classes are finite source types, not attractive free-form labels.
# This set includes every historical class already admitted by the immutable
# time-scoped censuses plus current refinements. Adding a genuinely new class
# requires an explicit source change and its negative-control tests.
FORMAL_ISSUE_PROBLEM_CLASSES = frozenset({
    "BACKING_STORE_ALLOCATION_AND_RECOVERY_CONSUMER",
    "CI_COVERAGE",
    "CI_EXECUTION",
    "CROSS_OWNER_REFINEMENT_BRIDGE",
    "CROSS_TARGET_EXECUTION_ENVIRONMENT",
    "DATABASE_AUTHORITY_CONVERGENCE",
    "DATABASE_AUTHORITY_PRECONDITION",
    "DEPENDENCY_CONVERGENCE",
    "ENVIRONMENT_CONTRACT",
    "FORMAL_INFORMATION_FLOW",
    "FORMAL_REFINEMENT_GAP",
    "FORMAL_REGISTRATION_SOURCE_PROVENANCE",
    "GATEWAY_SKILLS_ROUTE_DISCOVERY_SEAM",
    "GIT_REMOTE_REFERENCE",
    "GIT_RESIDUE",
    "HOST_DISK_PRESSURE",
    "LEGO_DEFINITION",
    "NETWORK_EGRESS",
    "OWNER_IDENTITY_CONTRACT",
    "OWNER_PLAN_REFINEMENT",
    "PR_CONVERGENCE",
    "RECOVERY_SNAPSHOT_RETENTION_UNPROVEN",
    "SECURITY_COMPOSITION",
    "SKILL_DOMAIN_DISCOVERY",
    "SKILL_PROVENANCE",
    "SOURCE_CONVERGENCE",
    "SOURCE_GRAPH_INTEGRITY",
    "TEST_EVIDENCE",
    "WINDOWS_EXECUTION_CONTEXT_CAPABILITY_DRIFT",
    "WORKSPACE_CONSUMER_CONTINUITY",
    "WORKSPACE_LIFECYCLE",
})

FORMAL_ISSUE_REPRESENTATION_TYPES = frozenset({
    "type", "graph", "constraint", "state-machine", "algebra",
    "equivalence", "declarative", "abstraction", "causal", "compression",
})

# The other registered Owner checker handles typed edges and dependency DAGs.
# This validator checks the independent typed node and slice closure;
# no new registry, executable DSL, scheduler or Owner truth.
# Finite R2.1 relation types already consumed by the natural Owners.
# graphlib, not this vocabulary, owns dependency DAG math.
LEGO_RELATION_KINDS = frozenset({
    "ADAPTATION",
    "AUTHORITY",
    "COMPATIBILITY",
    "COMPOSITION",
    "CONTROL",
    "DATA",
    "DELETION",
    "DEPENDENCY",
    "EFFECT",
    "EVIDENCE",
    "FALSIFICATION",
    "IDENTITY",
    "OBSERVATION",
    "POLICY",
    "REALIZATION",
    "SPECIALIZATION",
    "STATE",
    "STORAGE",
    "TRANSACTION",
    "VERIFICATION",
})

OWNER_LEGO_PLANS = (
    "apps/web/planning/lego-plan-r1.json",
    "meta/next/planning/lego-plan-r1.json",
    "domains/capital/planning/lego-plan-r1.json",
    "packages/composition/planning/lego-plan-r1.json",
    "services/runtime/planning/lego-plan-r1.json",
    "services/host/planning/lego-plan-r1.json",
    "services/harness/planning/lego-plan-r1.json",
    "platform/network/planning/lego-plan-r1.json",
    "platform/skills/planning/lego-plan-r1.json",
    "platform/security/planning/lego-plan-r1.json",
    "domains/game/planning/lego-plan-r1.json",
    "capabilities/media/planning/lego-plan-r1.json",
    "tools/repo/planning/lego-plan-r1.json",
    "services/gateway/planning/lego-plan-r1.json",
    "capabilities/preservation/planning/lego-plan-r1.json",
)

# Other already-consumed Owner versions and named carriers do not share the R1
# node/edge/slice graph schema. Register their physical source declarations,
# not a fabricated universal LEGO schema or duplicate Owner implementation.
OWNER_LEGO_PLAN_PROJECTIONS = {
    "capabilities/artifact/planning/lego-plan-r2.json": 2,
    "services/host/planning/lego-plan-r3.json": 3,
    # The named Windows R2 carrier deliberately retains its original schema v1.
    "services/gateway/planning/lego-plan-windows-carrier-r2.json": 1,
}


def validate_owner_plan_inventory(root: Path) -> None:
    """Close current two-level Owner plan paths without conflating schema versions.

    This is source-layout currentness, not a universal LEGO registry or an R2
    semantics proof. R1 graph laws remain scoped to OWNER_LEGO_PLANS; declaring
    an R2/R3 carrier cannot silently bypass source declaration admission.
    """
    observed = {
        path.relative_to(root).as_posix()
        for path in root.glob("*/*/planning/lego-plan-*.json")
    }
    registered = set(OWNER_LEGO_PLANS) | set(OWNER_LEGO_PLAN_PROJECTIONS)
    if observed != registered:
        raise ArchitectureDocsError(
            "Owner LEGO plan inventory drift: "
            f"unregistered={sorted(observed - registered)}, "
            f"missing={sorted(registered - observed)}"
        )


def validate_host_r3_semantic_alignment(root: Path, projection: dict[str, Any]) -> None:
    """Check one exact Host R3-to-R1 source alignment, not semantic equivalence.

    R3 intentionally uses a different native representation. This validator only
    proves that its declared retained responsibilities are totally source-aligned
    to the exact R1 carrier revision and that every current R1 node remains
    represented. It does not prove behavioral refinement, installed currentness,
    replacement safety, or permission to delete either carrier.
    """
    alignment = projection.get("semanticAlignment")
    if not isinstance(alignment, dict):
        raise ArchitectureDocsError("Host R3 semantic alignment missing")
    source_revision = alignment.get("sourceRevision")
    if not isinstance(source_revision, str) or re.fullmatch(r"[0-9a-f]{40}", source_revision) is None:
        raise ArchitectureDocsError("Host R3 semantic alignment source revision invalid")
    if alignment.get("carrier") != "planning/lego-plan-r1.json":
        raise ArchitectureDocsError("Host R3 semantic alignment carrier drift")
    if not isinstance(alignment.get("scope"), str) or not alignment["scope"].strip():
        raise ArchitectureDocsError("Host R3 semantic alignment scope missing")

    r1 = _load_json(
        _source_bound_file(
            root,
            "services/host/planning/lego-plan-r1.json",
            "Host R1 semantic alignment carrier",
        )
    )
    if projection.get("project", {}).get("id") != r1.get("project", {}).get("id"):
        raise ArchitectureDocsError("Host R3 semantic alignment project identity drift")
    review = r1.get("review")
    if not isinstance(review, dict) or review.get("sourceRevision") != source_revision:
        raise ArchitectureDocsError("Host R3 semantic alignment source revision drift")

    retained = projection.get("retained")
    if not isinstance(retained, list) or not retained:
        raise ArchitectureDocsError("Host R3 retained responsibilities missing")
    retained_ids = [row.get("id") for row in retained if isinstance(row, dict)]
    if (
        len(retained_ids) != len(retained)
        or any(not isinstance(identity, str) or not _canonical_owner_lego_id(identity)
               for identity in retained_ids)
        or len(retained_ids) != len(set(retained_ids))
    ):
        raise ArchitectureDocsError("Host R3 retained identity invalid")

    mapping = alignment.get("mapping")
    if not isinstance(mapping, dict) or set(mapping) != set(retained_ids):
        raise ArchitectureDocsError("Host R3 semantic alignment retained coverage drift")

    r1_nodes = r1.get("nodes")
    if not isinstance(r1_nodes, list) or not r1_nodes:
        raise ArchitectureDocsError("Host R1 semantic alignment nodes missing")
    r1_ids = {row.get("id") for row in r1_nodes if isinstance(row, dict)}
    if len(r1_ids) != len(r1_nodes) or any(not isinstance(x, str) for x in r1_ids):
        raise ArchitectureDocsError("Host R1 semantic alignment node identity invalid")

    observed_targets: set[str] = set()
    for retained_id, targets in mapping.items():
        if (
            not isinstance(targets, list)
            or not targets
            or len(targets) != len(set(targets))
            or any(not isinstance(target, str) or target not in r1_ids for target in targets)
        ):
            raise ArchitectureDocsError(
                f"Host R3 semantic alignment unknown Host R1 node: {retained_id}"
            )
        observed_targets.update(targets)
    if observed_targets != r1_ids:
        raise ArchitectureDocsError("Host R3 semantic alignment R1 coverage drift")

    retired_vocabulary = alignment.get("retiredVocabulary")
    if (
        not isinstance(retired_vocabulary, list)
        or not retired_vocabulary
        or any(not isinstance(value, str) or not value.strip() for value in retired_vocabulary)
    ):
        raise ArchitectureDocsError("Host R3 semantic alignment retired vocabulary missing")


def validate_owner_plan_projection_carriers(root: Path) -> None:
    """Validate exact R2/R3 carrier identities without imposing R1 graph laws.

    A registered physical file is not itself valid formal evidence: it must
    contain canonical JSON and a typed Owner/SourceCut envelope. This is not a
    claim that arbitrary R2/R3 semantics or real consumers are verified.
    """
    for relative, version in OWNER_LEGO_PLAN_PROJECTIONS.items():
        projection = _load_json(
            _source_bound_file(root, relative, "registered Owner plan projection")
        )
        if type(projection.get("schemaVersion")) is not int or projection["schemaVersion"] != version:
            raise ArchitectureDocsError(f"Owner plan projection schemaVersion drift: {relative}")
        if projection.get("kind") != "ordivon.project-lego-plan":
            raise ArchitectureDocsError(f"Owner plan projection kind drift: {relative}")
        if not isinstance(projection.get("truthRole"), str) or not projection["truthRole"].strip():
            raise ArchitectureDocsError(f"Owner plan projection truthRole missing: {relative}")
        project = projection.get("project")
        if not isinstance(project, dict) or not isinstance(project.get("id"), str) or not project["id"].strip():
            raise ArchitectureDocsError(f"Owner plan projection identity missing: {relative}")
        if relative == "services/host/planning/lego-plan-r3.json":
            validate_host_r3_semantic_alignment(root, projection)


def _validated_owner_lego_edges(
    edges: Any, vertices: set[str],
) -> list[tuple[str, str, str]]:
    """One total typed relation check; scheduling semantics remain separate."""
    if not isinstance(edges, list):
        raise ArchitectureDocsError("owner LEGO edges must be a list")
    observed: set[tuple[str, str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise ArchitectureDocsError("LEGO edge must be an object")
        kind = edge.get("type")
        if not isinstance(kind, str) or not kind.strip() or kind != kind.strip():
            raise ArchitectureDocsError("LEGO edge requires a type")
        if kind not in LEGO_RELATION_KINDS:
            raise ArchitectureDocsError("unknown LEGO edge type")
        source, target = edge.get("from"), edge.get("to")
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in vertices
            or target not in vertices
        ):
            raise ArchitectureDocsError("unknown LEGO edge endpoint")
        triple = (source, kind, target)
        if triple in observed:
            raise ArchitectureDocsError(f"duplicate LEGO edge: {triple}")
        observed.add(triple)
    return sorted(observed)


def _canonical_owner_lego_id(identity: str) -> bool:
    """One unambiguous machine key, distinct from localized LEGO labels."""
    return re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*", identity) is not None


def _require_exact_schema_one(value: dict[str, Any], label: str) -> None:
    """Schema version is an exact integer, not a Python numeric equality.

    `True == 1` and `1.0 == 1` must not grant admission to old R1
    contracts or historical issue evidence.
    """
    observed = value.get("schemaVersion")
    if type(observed) is not int or observed != 1:
        raise ArchitectureDocsError(f"{label} schemaVersion must be exact integer 1")


def validate_owner_lego_graph(plan: dict[str, Any]) -> None:
    """Check all Owner slices reference typed vertices, including unregistered ones.

    Registered dependency DAGs and typed edges have separate existing laws.
    This does not assert behavioral currentness or execution authority.
    """
    _require_exact_schema_one(plan, "owner LEGO graph")
    if plan.get("kind") != "ordivon.project-lego-plan":
        raise ArchitectureDocsError("owner LEGO graph has unexpected kind")
    if plan.get("truthRole") != "planning-projection-not-project-truth":
        raise ArchitectureDocsError("owner LEGO graph must remain non-authoritative")

    nodes = plan.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ArchitectureDocsError("owner LEGO graph needs nodes")
    identities: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ArchitectureDocsError("LEGO node must be an object")
        identity = node.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise ArchitectureDocsError("LEGO node requires non-empty identity")
        if not _canonical_owner_lego_id(identity):
            raise ArchitectureDocsError("non-canonical LEGO node identity")
        if identity in identities:
            raise ArchitectureDocsError(f"duplicate LEGO node: {identity}")
        if not isinstance(node.get("kind"), str) or not node["kind"].strip():
            raise ArchitectureDocsError(f"LEGO node {identity} requires a type")
        identities.add(identity)

    slices = plan.get("slices", [])
    if not isinstance(slices, list):
        raise ArchitectureDocsError("LEGO slices must be a list")
    slice_ids: set[str] = set()
    for slice_ in slices:
        if not isinstance(slice_, dict):
            raise ArchitectureDocsError("LEGO slice must be an object")
        identity = slice_.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise ArchitectureDocsError("LEGO slice needs non-empty identity")
        if not _canonical_owner_lego_id(identity):
            raise ArchitectureDocsError("non-canonical LEGO slice identity")
        if identity in slice_ids:
            raise ArchitectureDocsError(f"duplicate LEGO slice: {identity}")
        slice_ids.add(identity)
        refs = slice_.get("nodeIds")
        if not isinstance(refs, list) or not refs:
            raise ArchitectureDocsError(f"LEGO slice {identity} needs node references")
        if any(not isinstance(ref, str) or ref not in identities for ref in refs):
            raise ArchitectureDocsError(f"unknown LEGO slice node in {identity}")
        if len(refs) != len(set(refs)):
            raise ArchitectureDocsError(f"duplicate LEGO slice node in {identity}")

    # A blocked slice is a derived claim over the *current* declared
    # prerequisite graph, not a historical reason to keep work blocked.
    # Do not infer completion from released blockers; the slice stays
    # PROPOSED until its own acceptance evidence exists.
    slice_states = {row["id"]: row.get("status") for row in slices}
    # Reuse the stdlib DAG checker; these are planning prerequisites, not
    # executable workflows, and no new scheduler or registry is admitted.
    slice_prerequisites: dict[str, set[str]] = {name: set() for name in slice_states}
    # Finite planning states are types, not descriptive free text. Unknown
    # states must not silently bypass blocker/progress admission.
    lifecycle_states = {
        "PROPOSED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED",
        "COMPLETE", "RETIRED",
    }
    for row in slices:
        state = row.get("status")
        if (
            not isinstance(state, str)
            or (state not in lifecycle_states and not state.startswith("BLOCKED_ON_"))
        ):
            raise ArchitectureDocsError(f"invalid LEGO slice status: {row['id']}")
        if not state.startswith("BLOCKED_ON_"):
            continue
        blockers = row.get("blockers")
        if (
            not isinstance(blockers, list)
            or not blockers
            or any(not isinstance(ref, str) or ref not in slice_states for ref in blockers)
            or len(blockers) != len(set(blockers))
            or state != "BLOCKED_ON_" + "_".join(blockers)
            or any(slice_states[ref] in {"COMPLETE", "RETIRED"} for ref in blockers)
        ):
            raise ArchitectureDocsError(
                f"invalid LEGO blocking prerequisites: {row['id']}"
            )
        slice_prerequisites[row["id"]].update(blockers)
    try:
        TopologicalSorter(slice_prerequisites).prepare()
    except CycleError as error:
        raise ArchitectureDocsError("cyclic LEGO slice blockers") from error

    # Typed relations are structural; OBSERVATION/STATE cycles are allowed.
    _validated_owner_lego_edges(plan.get("edges", []), identities)




# A node's historical evidence prose is NOT a consumer/proof assertion.
# Interpret only syntactically exact file refs against an immutable Git tree
# (or explicitly labelled worktree bytes); all other prose stays unqualified.
def _node_declared_source_anchors(
    root: Path, owner: str, evidence: Any,
    *, git_tree: dict[str, str] | None,
) -> tuple[list[dict[str, str]], list[str]]:
    anchors: list[dict[str, str]] = []
    unresolved: list[str] = []
    if not isinstance(evidence, list):
        return anchors, unresolved
    seen_paths: set[str] = set()
    source_suffixes = (".py", ".rs", ".ts", ".tsx", ".toml", ".json",
                       ".md", ".tla", ".cfg", ".sh", ".rego", ".lock", ".yaml", ".yml")
    for literal in evidence:
        if not isinstance(literal, str):
            continue
        path_text, marker, symbol = literal.partition("::")
        if (not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", path_text)
                or (marker and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol))):
            continue
        # Owner-relative refs are the native planning convention. Fully
        # qualified cross-Owner refs retain their root identity.
        candidates = (
            [path_text] if path_text.startswith(owner + "/")
            else [owner + "/" + path_text, path_text]
        )
        resolved: str | None = None
        identity: str | None = None
        for candidate in candidates:
            if git_tree is not None:
                item = git_tree.get(candidate, "")
                mode, kind, _ = (
                    item.split(":") if item.count(":") == 2 else ("", "", "")
                )
                if kind == "blob" and mode in {"100644", "100755"}:
                    resolved, identity = candidate, item
                    break
            else:
                try:
                    source_path = _source_bound_file(root, candidate, "node declared source")
                except ArchitectureDocsError:
                    continue
                resolved = candidate
                identity = "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest()
                break
        if resolved is None:
            if path_text.endswith(source_suffixes):
                unresolved.append(literal)
            continue
        if resolved in seen_paths:
            # Distinct textual spellings of one file are one source membership.
            continue
        seen_paths.add(resolved)
        anchor: dict[str, str] = {
            "path": resolved,
            "sourceIdentity": identity,
            "qualification": (
                "GIT_BLOB_MEMBERSHIP_ONLY" if git_tree is not None
                else "WORKTREE_FILE_BYTES_ONLY"
            ),
        }
        if marker:
            anchor["declaredSymbolUnverified"] = symbol
        anchors.append(anchor)
    return sorted(anchors, key=lambda row: row["path"]), sorted(set(unresolved))


def project_owner_lego_source_graph(
    root: Path = ROOT, *, source_revision: str | None = None,
) -> dict[str, Any]:
    """Rebuild a *source planning* view; never attest a real LEGO or consumer.

    Owner-local IDs have no cross-owner identity. Preserve source paths,
    source byte digests, relation kinds, and declaration carriers; reuse the
    native structural and source guards rather than inventing a graph store.
    """
    git_tree: dict[str, str] | None = None
    if source_revision is not None:
        import subprocess
        if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
            raise ArchitectureDocsError("sourceRevision must be exact 40-hex Git commit")
        try:
            actual = subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(root), "rev-parse", "--verify", source_revision + "^{commit}"],
                stderr=subprocess.PIPE,
            ).decode("ascii").strip()
            if actual != source_revision:
                raise ArchitectureDocsError("Git commit source identity mismatch")
            # Reuse the existing native Git tree enumeration; no graph database.
            if __package__:
                from .source_history_legos import current_tree
            else:
                from source_history_legos import current_tree
            git_tree = current_tree(root, source_revision)
        except (subprocess.CalledProcessError, UnicodeError) as exc:
            raise ArchitectureDocsError(f"cannot resolve exact Git SourceCut: {exc}") from exc

    # A SourceCut owns its *then-current* registered R1 plans. Reading a
    # pre-registration commit through today's expanded list would falsely
    # demand a plan that did not exist, breaking precisely the LEGO-discovery
    # increment this projector is meant to report. Reuse the immutable Git
    # object already enumerated above, never current worktree registration.
    plan_carriers = OWNER_LEGO_PLANS
    if git_tree is not None:
        import subprocess
        registry_path = "tools/repo/check_architecture_docs.py"
        identity = git_tree.get(registry_path, "")
        mode, kind, oid = (
            identity.split(":") if identity.count(":") == 2 else ("", "", "")
        )
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ArchitectureDocsError("historical LEGO plan registry source missing")
        try:
            registration_source = subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(root),
                 "cat-file", "blob", oid], stderr=subprocess.PIPE,
            )
            historical_tree = ast.parse(registration_source, filename=registry_path)
            declarations = [
                item.value for item in historical_tree.body
                if isinstance(item, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "OWNER_LEGO_PLANS"
                    for target in item.targets
                )
            ]
            if len(declarations) != 1:
                raise ArchitectureDocsError("historical LEGO plan registration ambiguous")
            plan_carriers = ast.literal_eval(declarations[0])
        except (subprocess.CalledProcessError, SyntaxError, ValueError) as exc:
            raise ArchitectureDocsError("cannot qualify historical LEGO plan registration") from exc
        if (
            not isinstance(plan_carriers, tuple) or not plan_carriers
            or len(set(plan_carriers)) != len(plan_carriers)
            or any(
                not isinstance(path, str)
                or re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/planning/lego-plan-r1\.json", path) is None
                for path in plan_carriers
            )
        ):
            raise ArchitectureDocsError("historical LEGO plan registration invalid")

    source_plans: list[dict[str, str]] = []
    source_evidence_carriers: dict[str, dict[str, str]] = {}
    vertices: list[dict[str, Any]] = []
    relation_carriers: dict[tuple[str, str, str], set[str]] = {}
    node_source_relations: list[dict[str, str]] = []
    for relative in plan_carriers:
        if git_tree is None:
            path = _source_bound_file(root, relative, "registered Owner LEGO plan")
            before = path.read_bytes()
        else:
            import subprocess
            path = root / relative
            blob = git_tree.get(relative, "")
            mode, kind, oid = (blob.split(":") if blob.count(":") == 2 else ("", "", ""))
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ArchitectureDocsError(f"Owner plan absent/nonregular in Git SourceCut: {relative}")
            try:
                before = subprocess.check_output(
                    ["git", "--no-replace-objects", "-C", str(root), "cat-file", "blob", oid], stderr=subprocess.PIPE,
                )
            except subprocess.CalledProcessError as exc:
                raise ArchitectureDocsError(f"cannot read Git SourceCut plan: {relative}") from exc
        # Both worktree and immutable Git paths parse exactly the bytes witnessed
        # above: no unbound second read can counterfeit a source-qualified graph.
        plan = _load_json(path, source_bytes=before)
        owner = relative.split("/planning/", 1)[0]
        validate_owner_lego_graph(plan)
        validate_owner_lego_dependencies(plan, owner)
        evidence_paths = validate_owner_lego_source_evidence(
            root, relative, plan, git_tree=git_tree,
        )
        for evidence_path in evidence_paths:
            if git_tree is None:
                current = _source_bound_file(root, evidence_path, "Owner LEGO sourceEvidence")
                carrier = {
                    "path": evidence_path,
                    "worktreeSha256": "sha256:" + hashlib.sha256(current.read_bytes()).hexdigest(),
                }
            else:
                carrier = {"path": evidence_path, "gitBlobIdentity": git_tree[evidence_path]}
            source_evidence_carriers[evidence_path] = carrier
        if git_tree is None and path.read_bytes() != before:
            raise ArchitectureDocsError(f"Owner source changed during projection: {relative}")
        source_plans.append({
            "path": relative,
            "sha256": "sha256:" + hashlib.sha256(before).hexdigest(),
        })
        ids = {node["id"] for node in plan["nodes"]}

        def ref(local_id: str, plan_path: str = relative) -> str:
            return f"{plan_path}#{local_id}"

        for node in plan["nodes"]:
            anchors, unresolved = _node_declared_source_anchors(
                root, owner, node.get("evidence", []), git_tree=git_tree,
            )
            vertices.append({
                "ref": ref(node["id"]),
                "declaredKind": node["kind"],
                "declaredEvidence": node.get("evidence", []),
                "sourceAnchors": anchors,
                "unresolvedSourceEvidence": unresolved,
                # Source-path membership does not establish total readsets,
                # actual consumers, test execution or formal refinement.
                "sourceCoverageStanding": "DECLARED_SOURCE_MEMBERSHIP_PARTIAL",
            })
            for anchor in anchors:
                node_source_relations.append({
                    "from": ref(node["id"]),
                    "type": "EVIDENCE",
                    "toSourcePath": anchor["path"],
                    "sourceIdentity": anchor["sourceIdentity"],
                    "qualification": anchor["qualification"],
                })
            for prerequisite in node["dependencies"]:
                key = (ref(prerequisite), "DEPENDENCY", ref(node["id"]))
                relation_carriers.setdefault(key, set()).add("NODE_DEPENDENCIES")
        for source, kind, target in _validated_owner_lego_edges(plan.get("edges", []), ids):
            key = (ref(source), kind, ref(target))
            relation_carriers.setdefault(key, set()).add("TYPED_EDGE")

    return {
        "kind": "ordivon.owner-lego-planning-source-projection",
        "truthRole": "DERIVED_READ_ONLY_SOURCE_PLANNING_NOT_LEGO_TRUTH",
        "sourceCut": (
            source_revision if source_revision is not None
            else "WORKTREE_BYTES_ONLY_GIT_AND_INSTALLED_UNQUALIFIED"
        ),
        "sourcePlans": source_plans,
        "sourceEvidenceCarriers": [
            source_evidence_carriers[path] for path in sorted(source_evidence_carriers)
        ],
        "vertices": sorted(vertices, key=lambda item: item["ref"]),
        "nodeSourceRelations": sorted(
            node_source_relations,
            key=lambda row: (row["from"], row["toSourcePath"]),
        ),
        "relations": [
            {"from": source, "type": kind, "to": target, "declaredBy": sorted(carriers)}
            for (source, kind, target), carriers in sorted(relation_carriers.items())
        ],
        "excluded": {
            "ownerPlanRevisions": sorted(OWNER_LEGO_PLAN_PROJECTIONS),
            "unverifiedFacets": [
                "ACTUAL_LEGO_IDENTITY", "ACTUAL_CONSUMER", "FORMAL_PROOF",
                "CONFIGURED", "INSTALLED", "EXECUTED", "CURRENTNESS",
                "CROSS_OWNER_RELATION_CLOSURE", "DYNAMIC_DEPENDENCIES",
            ],
        },
    }



def inspect_owner_lego_contract(
    *, source_revision: str, node_ref: str, root: Path = ROOT,
) -> dict[str, Any]:
    """Inspect one declared R2.1 contract at an immutable Git cut.

    Existing Repo plan projection stays the only source; this compact query
    is a read-only *source declaration*, not live consumer or Formal truth.
    """
    import subprocess

    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise ArchitectureDocsError("inspect requires exact 40-hex SourceCut")
    # The native graph validates the historical registered plans, typed edges,
    # and evidence source identities; it must not infer deployed or proof PASS.
    view = project_owner_lego_source_graph(root, source_revision=source_revision)
    nodes = {row["ref"]: row for row in view["vertices"]}
    if node_ref not in nodes:
        raise ArchitectureDocsError("node ref is not registered at this SourceCut")
    plan_path, node_id = node_ref.rsplit("#", 1)
    planned = {row["path"]: row for row in view["sourcePlans"]}
    if plan_path not in planned:
        raise ArchitectureDocsError("node plan is not registered at this SourceCut")
    try:
        source_bytes = subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(root),
             "show", f"{source_revision}:{plan_path}"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise ArchitectureDocsError("node plan Git source cannot be read") from exc
    if "sha256:" + hashlib.sha256(source_bytes).hexdigest() != planned[plan_path]["sha256"]:
        raise ArchitectureDocsError("node plan Git identity differs from validated projection")
    plan = _load_json(root / plan_path, source_bytes=source_bytes)
    candidates = [row for row in plan["nodes"] if row["id"] == node_id]
    if len(candidates) != 1:
        raise ArchitectureDocsError("node declaration is ambiguous")
    node = candidates[0]
    anchors = nodes[node_ref]["sourceAnchors"]
    declared_relations = [
        {"from": edge["from"], "type": edge["type"], "to": edge["to"]}
        for edge in view["relations"]
        if node_ref in (edge["from"], edge["to"])
    ]
    # Preserve absence explicitly, rather than treating an absent optional
    # field or source anchor as a verified empty behavioral contract.
    roles = ("id", "responsibility", "inputs", "outputs",
             "behavioralContract", "acceptance")
    return {
        "kind": "ordivon.owner-lego-source-contract-inspection",
        "truthRole": "SOURCE_PLAN_DECLARATION_ONLY_NOT_RUNTIME_OR_FORMAL_TRUTH",
        "sourceCut": source_revision,
        "ref": node_ref,
        "planIdentity": planned[plan_path],
        "declaredRoles": {key: node.get(key) for key in roles},
        "missingRoles": [key for key in roles if not node.get(key)],
        "declaredKind": node.get("kind"),
        "declaredState": node.get("state"),
        "declaredDependencies": node.get("dependencies", []),
        "declaredConsumerEvidence": node.get("consumerEvidence", []),
        # Owner-local R1 carriers evolved independently. Absence of a field is
        # unknown, not positive evidence that the LEGO has zero consumers.
        # Retain each native claim name; do not pretend an AST/static binding
        # or declared port is an observed production consumer.
        "declaredConsumerClaims": {
            "consumerEvidence": node.get("consumerEvidence"),
            "actualConsumers": node.get("actualConsumers"),
            "consumerBindings": node.get("consumerBindings"),
        },
        "consumerClaimQualification": "SOURCE_PLAN_DECLARATION_ONLY_NOT_VERIFIED_CONSUMPTION",
        "consumerClosureStanding": "UNKNOWN",
        "declaredFormalObligations": node.get("formalObligations", []),
        "sourceAnchors": anchors,
        "unresolvedSourceEvidence": nodes[node_ref]["unresolvedSourceEvidence"],
        "sourceCoverageStanding": nodes[node_ref]["sourceCoverageStanding"],
        "incidentRelations": declared_relations,
        "unverifiedFacets": view["excluded"]["unverifiedFacets"],
        "proofReuseAdmissible": False,
    }



def _project_native_json_schema_source(
    root: Path, source_path: str, source_identity: str | None,
) -> dict[str, Any] | None:
    """Bounded native JSON carrier hint from an immutable Git regular blob.

    This reads only declared metadata, not a verified schema, consumer or
    installed Tool/Plugin. Symlinks and gitlinks are never dereferenced.
    """
    if not source_path.endswith(".json") or not source_identity:
        return None
    mode, kind, oid = (
        source_identity.split(":") if source_identity.count(":") == 2
        else ("", "", "")
    )
    if (
        mode not in {"100644", "100755"} or kind != "blob"
        or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid) is None
    ):
        return None
    import subprocess

    def cat_file(*args: str) -> bytes:
        try:
            return subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(root),
                 "cat-file", *args],
                stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ArchitectureDocsError(
                "native contract Git blob unavailable at immutable SourceCut"
            ) from exc

    length = int(cat_file("-s", oid).strip())
    if length > 65536:
        return None
    try:
        value = json.loads(cat_file("blob", oid))
    except (ValueError, UnicodeError):
        return None
    if not isinstance(value, dict):
        return None
    schema = value.get("$schema")
    if not isinstance(schema, str) or not 0 < len(schema) <= 2048:
        return None

    result: dict[str, Any] = {
        "standing": "NATIVE_JSON_SCHEMA_DECLARATION_ONLY",
        "schemaUri": schema,
        "sourceIdentity": source_identity,
    }
    if isinstance(value.get("name"), str):
        result["declaredPackageName"] = value["name"]
    servers = value.get("mcpServers")
    if isinstance(servers, dict) and len(servers) <= 128 and all(
        isinstance(name, str) for name in servers
    ):
        result["declaredMcpServerKeys"] = sorted(servers)
    return result

def inspect_owner_source_path(
    *, source_revision: str, source_path: str, root: Path = ROOT,
) -> dict[str, Any]:
    """Agent path→owner→declared LEGO lookup; no consumer/proof equivalence."""
    import tomllib
    if (not source_path or source_path.startswith("/") or chr(92) in source_path
            or chr(0) in source_path
            or any(part in {"", ".", ".."} for part in source_path.split("/"))):
        raise ArchitectureDocsError("inspect requires canonical source path")
    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise ArchitectureDocsError("inspect requires exact 40-hex SourceCut")
    if __package__:
        from . import source_history_legos
    else:
        import source_history_legos

    graph = project_owner_lego_source_graph(root, source_revision=source_revision)
    files = source_history_legos.current_tree(root, source_revision)
    owners = source_history_legos.owners(root, source_revision)
    manifest = tomllib.loads(source_history_legos.git(
        root, "--no-replace-objects", "show",
        source_revision + ":tools/repo/owners.toml",
    ))
    registered = {(x["root"], x["name"]): x for x in manifest["owners"]}
    selected = []
    for prefix, name in owners:
        if source_path.startswith(prefix):
            row = registered.get((prefix, name))
            selected.append({
                "name": name,
                "root": prefix,
                "verifyTask": row["verify_task"] if row else "repo:ci",
                "queueVerifyTask": (
                    row.get("queue_verify_task", row["verify_task"]) if row
                    else "repo:ci"
                ),
            })
    anchored = [
        {
            "ref": vertex["ref"],
            "sourceCoverageStanding": vertex["sourceCoverageStanding"],
            "sourceWitness": [
                anchor for anchor in vertex["sourceAnchors"]
                if anchor["path"] == source_path
            ],
        }
        for vertex in graph["vertices"]
        if any(anchor["path"] == source_path for anchor in vertex["sourceAnchors"])
    ]
    identity = files.get(source_path)
    mode, kind = (
        identity.split(":")[:2] if identity and identity.count(":") == 2
        else ("", "")
    )
    if not identity:
        git_entry_standing = "ABSENT_FROM_GIT_CUT"
    elif mode in {"100644", "100755"} and kind == "blob":
        git_entry_standing = "REGULAR_BLOB"
    elif mode == "120000" and kind == "blob":
        git_entry_standing = "SYMLINK_BLOB_NOT_TARGET_CONTENT"
    elif mode == "160000" and kind == "commit":
        git_entry_standing = "GITLINK_NOT_LOCAL_CONTENT"
    else:
        git_entry_standing = "UNKNOWN_NONREGULAR_GIT_ENTRY"

    return {
        "kind": "ordivon.owner-source-path-inspection",
        "truthRole": "IMMUTABLE_GIT_AND_DECLARED_ANCHORS_ONLY",
        "sourceCut": source_revision,
        "path": source_path,
        "sourceIdentity": identity,
        "gitEntryStanding": git_entry_standing,
        "nativeContractCarrier": _project_native_json_schema_source(
            root, source_path, identity
        ),
        "sourceMembershipStanding": (
            "TRACKED_SOURCE" if source_path in files else "ABSENT_AT_SOURCECUT"
        ),
        "ownerPartitions": selected,
        "declaredLegoAnchors": anchored,
        "legoDiscoveryStanding": (
            "DECLARED_ANCHOR_PARTIAL" if anchored else "UNKNOWN_UNINDEXED"
        ),
        "consumerProofStanding": "UNKNOWN",
        "unverifiedFacets": graph["excluded"]["unverifiedFacets"],
        "proofReuseAdmissible": False,
        "nextOperation": (
            "inspect-owner-lego" if anchored else "investigate-source-consumers"
        ),
    }

def project_owner_lego_source_change(
    *, before_revision: str, after_revision: str, root: Path = ROOT,
) -> dict[str, Any]:
    """Select DECLARED graph/source requalification over two immutable Git cuts.

    A path/edge change is not itself an actual consumer or proof dependency.
    Only DEPENDENCY edges have a declared downstream direction; all other
    relation types are exposed as relation deltas, not invented call edges.
    """
    import subprocess
    # The same Git temporal-order proof required by source_membership_delta.
    # A sibling PR diff is not a before/after graph evolution; calculate the
    # integration merge tree first instead of misattributing target-only edits.
    if __package__:
        from .source_history_legos import require_ancestral_source_cuts
    else:
        from source_history_legos import require_ancestral_source_cuts
    require_ancestral_source_cuts(root, before_revision, after_revision)
    before = project_owner_lego_source_graph(root, source_revision=before_revision)
    after = project_owner_lego_source_graph(root, source_revision=after_revision)
    raw = subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(root), "diff", "--no-renames",
         "--name-only", "-z", before_revision, after_revision, "--"],
        stderr=subprocess.PIPE,
    )
    changed_paths = {path.decode("utf-8") for path in raw.split(b"\x00") if path}
    old_nodes = {row["ref"]: row for row in before["vertices"]}
    new_nodes = {row["ref"]: row for row in after["vertices"]}
    old_edges = {
        (row["from"], row["type"], row["to"], tuple(row["declaredBy"]))
        for row in before["relations"]
    }
    new_edges = {
        (row["from"], row["type"], row["to"], tuple(row["declaredBy"]))
        for row in after["relations"]
    }
    changed_edges = old_edges ^ new_edges
    # All changes to the declared vertex or its exact anchored source blob
    # trigger direct requalification, even if the Git path remains constant.
    direct = {
        ref for ref in set(old_nodes) | set(new_nodes)
        if old_nodes.get(ref) != new_nodes.get(ref)
    }
    direct.update(endpoint for src, _, dst, _ in changed_edges for endpoint in (src, dst))
    direct.update(
        ref for ref, node in new_nodes.items()
        if any(anchor["path"] in changed_paths for anchor in node["sourceAnchors"])
    )
    # A removed ancestor can still affect a surviving downstream consumer.
    # Reuse BOTH historical and target dependency declarations.
    downstream: dict[str, set[str]] = {}
    potential_edges: dict[str, set[str]] = {}
    for src, kind, dst, _ in old_edges | new_edges:
        if kind == "DEPENDENCY":
            downstream.setdefault(src, set()).add(dst)
        else:
            # No formal influence polarity is defined for these typed
            # relations: COMPATIBILITY/IDENTITY can affect either endpoint.
            # Conservatively propagate UNKNOWN in both directions, never
            # fabricate a proof prerequisite or a RECHECK_REQUIRED claim.
            potential_edges.setdefault(src, set()).add(dst)
            potential_edges.setdefault(dst, set()).add(src)
    # Plan metadata, slice acceptance, and behavioral obligations are not
    # all projected into vertex/edge identity. A changed plan is a source
    # contract change: recheck its declared nodes conservatively, without
    # claiming that deployed behavior or proofs have changed.
    plan_paths = {row["path"] for row in before["sourcePlans"] + after["sourcePlans"]}
    changed_plan_paths = changed_paths & plan_paths
    direct.update(
        ref for ref in set(old_nodes) | set(new_nodes)
        if ref.split("#", 1)[0] in changed_plan_paths
    )
    affected = set(direct)
    frontier = list(direct)
    while frontier:
        for dst in downstream.get(frontier.pop(), ()):
            if dst not in affected:
                affected.add(dst)
                frontier.append(dst)
    potential: set[str] = set()
    frontier = list(affected)
    visited = set(frontier)
    while frontier:
        source = frontier.pop()
        for dst in downstream.get(source, set()) | potential_edges.get(source, set()):
            if dst not in visited:
                visited.add(dst)
                frontier.append(dst)
                if dst not in affected:
                    potential.add(dst)

    visible_anchors = {
        anchor["path"] for view in (before, after)
        for node in view["vertices"] for anchor in node["sourceAnchors"]
    }
    unindexed = changed_paths - visible_anchors - plan_paths
    rows = []
    for ref in sorted(new_nodes):
        owner = ref.split("/planning/", 1)[0]
        owner_unindexed = any(path.startswith(owner + "/") for path in unindexed)
        status = (
            "RECHECK_REQUIRED" if ref in affected
            else "UNKNOWN" if owner_unindexed or ref in potential
            else "NO_DECLARED_HIT"
        )
        rows.append({"ref": ref, "sourceImpactStanding": status})
    return {
        "kind": "ordivon.owner-lego-declared-source-change",
        "truthRole": "NON_AUTHORITATIVE_GIT_SOURCE_AND_DECLARED_GRAPH_IMPACT_ONLY",
        "beforeSourceCut": before_revision,
        "afterSourceCut": after_revision,
        "changedGitPaths": sorted(changed_paths),
        "sourcePlanChangedPaths": sorted(changed_plan_paths),
        "changedDeclaredRelationCount": len(changed_edges),
        "directChangedRefs": sorted(direct),
        "potentialRelationInfluenceRefs": sorted(potential),
        "removedRefs": sorted(set(old_nodes) - set(new_nodes)),
        "unindexedChangedPaths": sorted(unindexed),
        "standingByDeclaredNode": rows,
        "proofReuseAdmissible": False,
        "nonClaims": [
            "NO_DECLARED_HIT does not mean the node has no actual or dynamic consumers.",
            "Source anchors establish Git membership, not proof execution or formal refinement.",
            "Changed planning-carrier bytes conservatively recheck their nodes, not necessarily their deployed consumers.",
            "Declared DEPENDENCY edges trigger recheck; other typed relations conservatively propagate bidirectional UNKNOWN until influence polarity is proved.",
            "Unobserved cross-Owner and dynamic consumer paths remain UNKNOWN outside this local projection.",
            "Changed unindexed paths may affect undiscovered consumers; SOURCE selection grants no deletion or runtime authority.",
        ],
    }



def project_node_python_import_syntax(
    *, source_revision: str, node_ref: str, target_source: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Trace a declared Python node source through native Git + stdlib AST.

    The result describes possible syntactic importers, not proven runtime
    consumers, dynamic dependencies, or a complete Python import analysis.
    """
    import importlib.util
    import subprocess

    graph = project_owner_lego_source_graph(root, source_revision=source_revision)
    nodes = {row["ref"]: row for row in graph["vertices"]}
    if node_ref not in nodes or "/planning/lego-plan-" not in node_ref:
        raise ArchitectureDocsError("Python import inspection requires registered node ref")
    owner = node_ref.split("/planning/", 1)[0]
    allowed = {a["path"]: a for a in nodes[node_ref]["sourceAnchors"]}
    if target_source not in allowed or not target_source.startswith(owner + "/src/"):
        raise ArchitectureDocsError("Python import target is not node-anchored Owner src")
    if not target_source.endswith(".py"):
        raise ArchitectureDocsError("Python import target must be source Python")
    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise ArchitectureDocsError("Python import SourceCut is not exact Git commit")
    if __package__:
        from .source_history_legos import current_tree
    else:
        from source_history_legos import current_tree

    tree = current_tree(root, source_revision)
    if tree.get(target_source) != allowed[target_source]["sourceIdentity"]:
        raise ArchitectureDocsError("Python import target source identity mismatch")

    prefix = owner + "/src/"
    rel = target_source[len(prefix):]
    target_module = rel[:-3].replace("/", ".")
    target_module = target_module.removesuffix(".__init__")
    if not target_module or "." not in target_module:
        raise ArchitectureDocsError("Python import target package path is unqualified")

    def read_git_source(path: str) -> str:
        identity = tree[path]
        mode, kind, oid = identity.split(":")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ArchitectureDocsError("nonregular Git Python importer")
        return subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(root), "cat-file", "blob", oid],
            stderr=subprocess.PIPE,
        ).decode("utf-8")

    # Finite, task-local static upstream SOURCE overapproximation.
    # This is neither Python's executed import graph nor a complete proof
    # readset: external packages, runtime imports, env and installed versions
    # remain explicitly outside the Git-only evidence boundary.
    local_prefix = owner + "/src/"
    def module_source(module_name: str) -> str | None:
        if not module_name or any(
            not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part)
            for part in module_name.split(".")
        ):
            return None
        stem = local_prefix + module_name.replace(".", "/")
        for candidate in (stem + ".py", stem + "/__init__.py"):
            identity = tree.get(candidate, "")
            if (identity.startswith("100644:blob:")
                    or identity.startswith("100755:blob:")):
                return candidate
        return None

    def source_package(path: str) -> str:
        mod = path[len(local_prefix):-3].replace("/", ".")
        return mod.removesuffix(".__init__") if path.endswith("/__init__.py") else mod.rpartition(".")[0]

    # Python imports execute intermediate package initializers as well.
    source_parts = target_source[len(local_prefix):].split("/")
    init_paths = [
        local_prefix + "/".join(source_parts[:depth]) + "/__init__.py"
        for depth in range(1, len(source_parts))
    ]
    pending = [target_source] + [path for path in init_paths if path in tree]
    visited: set[str] = set()
    upstream_invalid: set[str] = set()
    external_module_assumptions: set[str] = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        if len(visited) > 256:
            raise ArchitectureDocsError("local Python static source readset exceeded bounded 256 files")
        try:
            syntax = ast.parse(read_git_source(path), filename=path)
        except (SyntaxError, UnicodeError):
            upstream_invalid.add(path)
            continue
        package = source_package(path)
        for node in ast.walk(syntax):
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                try:
                    base = (
                        importlib.util.resolve_name("." * node.level + (node.module or ""), package)
                        if node.level else (node.module or "")
                    )
                except ImportError:
                    upstream_invalid.add(path)
                    continue
                imports = [base] + [base + "." + alias.name for alias in node.names]
            else:
                continue
            for imported in imports:
                source = module_source(imported)
                if source:
                    pending.append(source)
                    # Include Python parent package initialization if present.
                    parts = imported.split(".")
                    for count in range(1, len(parts)):
                        parent_source = module_source(".".join(parts[:count]))
                        if parent_source:
                            pending.append(parent_source)
                else:
                    # A from-imported *symbol* of a local module is not
                    # another missing package. For genuinely unresolved
                    # modules retain the external top-level environment cut.
                    ancestor = imported
                    while "." in ancestor and module_source(ancestor) is None:
                        ancestor = ancestor.rpartition(".")[0]
                    if module_source(ancestor) is None:
                        external_module_assumptions.add(imported.split(".", 1)[0])
    upstream_paths = sorted(visited - {target_source})

    try:
        target_ast = ast.parse(read_git_source(target_source), filename=target_source)
    except (SyntaxError, UnicodeError) as exc:
        raise ArchitectureDocsError("Python declared target has invalid source syntax") from exc
    top_level_defined: set[str] = set()
    for statement in target_ast.body:
        if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            top_level_defined.add(statement.name)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    top_level_defined.add(target.id)
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            top_level_defined.add(statement.target.id)

    possible_importers: list[dict[str, Any]] = []
    invalid_syntax: list[str] = []
    scanned = 0
    search_prefixes = (owner + "/src/", owner + "/tests/")
    for path in sorted(tree):
        if not path.endswith(".py") or path == target_source or not path.startswith(search_prefixes):
            continue
        scanned += 1
        try:
            ast_tree = ast.parse(read_git_source(path), filename=path)
        except (SyntaxError, UnicodeError):
            invalid_syntax.append(path)
            continue
        # 'tests' do not always form Python packages, hence relative imports
        # there cannot be safely resolved without more execution context.
        if path.startswith(prefix):
            module = path[len(prefix):-3].replace("/", ".")
            package = (
                module.removesuffix(".__init__")
                if path.endswith("/__init__.py") else module.rpartition(".")[0]
            )
        else:
            package = None
        matches: set[tuple[str, str]] = set()
        for item in ast.walk(ast_tree):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    if alias.name == target_module:
                        matches.add(("IMPORT", alias.name))
            elif isinstance(item, ast.ImportFrom):
                try:
                    if item.level:
                        if package is None:
                            continue
                        base = importlib.util.resolve_name(
                            "." * item.level + (item.module or ""), package
                        )
                    else:
                        base = item.module or ""
                except ImportError:
                    continue
                if base == target_module:
                    for alias in item.names:
                        matches.add(("IMPORT_FROM", alias.name))
                else:
                    for alias in item.names:
                        if base + "." + alias.name == target_module:
                            matches.add(("FROM_PARENT_SUBMODULE", alias.name))
        if matches:
            possible_importers.append({
                "sourcePath": path,
                "gitBlobIdentity": tree[path],
                "importSyntax": [
                    {
                        "kind": k, "name": n,
                        "targetDefinitionStanding": (
                            "SOURCE_TOP_LEVEL_DEFINED" if n in top_level_defined
                            else "MODULE_SOURCE_PRESENT" if k != "IMPORT_FROM"
                            else "UNRESOLVED_OR_REEXPORTED"
                        ),
                    }
                    for k, n in sorted(matches)
                ],
                "qualification": "PYTHON_AST_IMPORT_SYNTAX_ONLY_NOT_EXECUTION",
            })
    return {
        "kind": "ordivon.owner-lego-python-source-import-syntax",
        "truthRole": "DERIVED_SOURCE_CANDIDATE_CONSUMERS_NOT_RUNTIME_CONSUMER_TRUTH",
        "sourceCut": source_revision,
        "declaredNodeRef": node_ref,
        "targetSourcePath": target_source,
        "targetGitBlobIdentity": tree[target_source],
        "targetPythonModule": target_module,
        "upstreamLocalSourceFiles": [
            {"sourcePath": path, "gitBlobIdentity": tree[path]}
            for path in upstream_paths
        ],
        "upstreamStaticReadsetQualification": "PARTIAL_GIT_STATIC_IMPORTS_NOT_EXECUTED_OR_COMPLETE",
        "upstreamInvalidSyntaxPaths": sorted(upstream_invalid),
        "externalImportAssumptions": sorted(external_module_assumptions),
        "candidateImporters": possible_importers,
        "scanBoundary": {
            "sourceRoots": list(search_prefixes),
            "pythonFilesParsedOrAttempted": scanned,
            "invalidSyntaxPaths": invalid_syntax,
            "dynamicImportsResolved": False,
            "externalConsumersCovered": False,
        },
        "nonClaims": [
            "An AST import can be conditional, dead, guarded, unused or shadowed.",
            "Missing static importer is NOT proof of no runtime or cross-Owner consumer.",
            "Only an exact Git blob is source evidence; test execution, implementation refinement and installed currentness require separate receipts.",
        ],
    }



def project_node_python_import_delta(
    *, before_revision: str, after_revision: str,
    node_ref: str, target_source: str, root: Path = ROOT,
) -> dict[str, Any]:
    """Diff one Git-qualified candidate consumer seam, not its runtime truth.

    The same source module can retain all static import syntax while its
    consumer implementation changes. This must never imply proof reuse.
    """
    snapshots: dict[str, dict[str, Any]] = {}
    for label, revision in (("before", before_revision), ("after", after_revision)):
        try:
            snapshots[label] = project_node_python_import_syntax(
                source_revision=revision, node_ref=node_ref,
                target_source=target_source, root=root,
            )
        except ArchitectureDocsError as exc:
            # A deleted/retired/reassigned node or a non-parseable target
            # changes the query boundary: neither "no importers" nor PASS.
            return {
                "kind": "ordivon.owner-lego-python-import-source-delta",
                "beforeSourceCut": before_revision,
                "afterSourceCut": after_revision,
                "declaredNodeRef": node_ref,
                "targetSourcePath": target_source,
                "sourceRelationStanding": "UNKNOWN",
                "unresolvedCut": label,
                "qualificationGap": str(exc),
                "proofReuseAdmissible": False,
            }

    before, after = snapshots["before"], snapshots["after"]
    def index(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {row["sourcePath"]: row for row in snapshot["candidateImporters"]}

    old, new = index(before), index(after)
    def syntax(row: dict[str, Any]) -> set[tuple[str, str, str]]:
        return {
            (entry["kind"], entry["name"], entry["targetDefinitionStanding"])
            for entry in row["importSyntax"]
        }

    candidate_changes: list[dict[str, Any]] = []
    for path in sorted(set(old) | set(new)):
        prior, current = old.get(path), new.get(path)
        prior_syntax = syntax(prior) if prior else set()
        current_syntax = syntax(current) if current else set()
        added = current_syntax - prior_syntax
        removed = prior_syntax - current_syntax
        source_changed = (
            prior is None or current is None
            or prior["gitBlobIdentity"] != current["gitBlobIdentity"]
        )
        if added or removed or source_changed:
            candidate_changes.append({
                "sourcePath": path,
                "sourceChangeStanding": (
                    "STATIC_RELATION_CHANGED" if added or removed
                    else "IMPORTER_BYTES_CHANGED_RELATION_STABLE"
                ),
                "addedImportSyntax": [
                    {"kind": k, "name": n, "targetDefinitionStanding": q}
                    for k, n, q in sorted(added)
                ],
                "removedImportSyntax": [
                    {"kind": k, "name": n, "targetDefinitionStanding": q}
                    for k, n, q in sorted(removed)
                ],
                "beforeGitBlobIdentity": prior["gitBlobIdentity"] if prior else None,
                "afterGitBlobIdentity": current["gitBlobIdentity"] if current else None,
            })

    target_changed = before["targetGitBlobIdentity"] != after["targetGitBlobIdentity"]
    old_upstream = {
        row["sourcePath"]: row["gitBlobIdentity"]
        for row in before["upstreamLocalSourceFiles"]
    }
    new_upstream = {
        row["sourcePath"]: row["gitBlobIdentity"]
        for row in after["upstreamLocalSourceFiles"]
    }
    changed_upstream = [
        {"sourcePath": path, "beforeGitBlobIdentity": old_upstream.get(path),
         "afterGitBlobIdentity": new_upstream.get(path)}
        for path in sorted(set(old_upstream) | set(new_upstream))
        if old_upstream.get(path) != new_upstream.get(path)
    ]
    invalid_syntax_paths = sorted(set(
        before["scanBoundary"]["invalidSyntaxPaths"]
        + after["scanBoundary"]["invalidSyntaxPaths"]
        + before["upstreamInvalidSyntaxPaths"]
        + after["upstreamInvalidSyntaxPaths"]
    ))
    return {
        "kind": "ordivon.owner-lego-python-import-source-delta",
        "truthRole": "TWO_GIT_SOURCE_CUTS_ONLY_NO_CONSUMER_OR_PROOF_AUTHORITY",
        "beforeSourceCut": before_revision,
        "afterSourceCut": after_revision,
        "declaredNodeRef": node_ref,
        "targetSourcePath": target_source,
        "targetBlobChanged": target_changed,
        "beforeCandidateImporterCount": len(old),
        "afterCandidateImporterCount": len(new),
        "changedCandidateImporters": candidate_changes,
        "changedUpstreamLocalSourceFiles": changed_upstream,
        "upstreamReadsetQualification": "PARTIAL_GIT_STATIC_IMPORTS_NOT_EXECUTED_OR_COMPLETE",
        "unchangedCandidateImporterCount": len(set(old) & set(new)) - sum(
            path in old and path in new and old[path] != new[path]
            for path in set(old) & set(new)
        ),
        "invalidSyntaxPaths": invalid_syntax_paths,
        "sourceRelationStanding": (
            "UNKNOWN" if invalid_syntax_paths
            else "RECHECK_REQUIRED" if target_changed or candidate_changes or changed_upstream
            else "NO_DECLARED_SOURCE_RELATION_CHANGE"
        ),
        "proofReuseAdmissible": False,
        "nonClaims": [
            "An unchanged static import is not a behavioral equivalence proof.",
            "An importer may also be called dynamically, re-exported or loaded externally.",
            "Changed importer bytes require consumer requalification even if import syntax is stable.",
            "Source-qualified upstream local static imports are only a partial overapproximation; changed bytes require native contract recheck.",
            "Absence of a changed candidate is not a general proof-cache admission.",
        ],
    }


def validate_deployed_graph(value: dict[str, Any]) -> None:
    _require_exact_schema_one(value, "deployed architecture")
    if value.get("kind") != "ordivon.deployed-architecture":
        raise ArchitectureDocsError("unexpected deployed architecture kind")
    if value.get("status") != "CURRENT_DEPLOYED_BASELINE":
        raise ArchitectureDocsError("deployed architecture must be CURRENT_DEPLOYED_BASELINE")

    northbound = value.get("defaultNorthbound")
    if not isinstance(northbound, dict):
        raise ArchitectureDocsError("defaultNorthbound must be an object")
    if northbound.get("endpoint") != "https://gateway-mcp.ordivon.com/mcp":
        raise ArchitectureDocsError("default northbound must be Gateway MCP")
    if northbound.get("authoritative") is not False:
        raise ArchitectureDocsError("Gateway must remain non-authoritative")
    if northbound.get("directRuntimeHostAreDefault") is not False:
        raise ArchitectureDocsError("direct Runtime/Host must not be default northbound")

    routers = value.get("routers")
    if not isinstance(routers, dict):
        raise ArchitectureDocsError("routers must be an object")
    method = routers.get("methodRouter")
    capability = routers.get("capabilityRouter")
    if not isinstance(method, dict) or not isinstance(capability, dict):
        raise ArchitectureDocsError("both Method Router and Capability Router are required")
    if method.get("kind") != "agent-skill":
        raise ArchitectureDocsError("Method Router must be an Agent Skill")
    if capability.get("kind") != "gateway-static-owner-projection":
        raise ArchitectureDocsError("Capability Router must be a Gateway projection")
    if method.get("path") == capability.get("path"):
        raise ArchitectureDocsError("Method Router and Capability Router must remain distinct")

    capabilities = capability.get("capabilities")
    if not isinstance(capabilities, list) or set(capabilities) != EXPECTED_CAPABILITIES:
        raise ArchitectureDocsError("deployed Gateway capability set drifted")

    retired = value.get("retired")
    if not isinstance(retired, list) or not any(
        isinstance(item, dict)
        and item.get("id") == "agent-service"
        and item.get("standing") == "RETIRED_DO_NOT_RECONSTRUCT"
        for item in retired
    ):
        raise ArchitectureDocsError("retired Agent Service standing is missing")

    observability = value.get("observability")
    if not isinstance(observability, dict):
        raise ArchitectureDocsError("deployed observability projection is missing")
    if observability.get("status") != "deployed-on-demand":
        raise ArchitectureDocsError("trace backend must remain deployed-on-demand")
    ingress = observability.get("ingress")
    backend = observability.get("traceBackend")
    export = observability.get("gatewayExport")
    if not isinstance(ingress, dict) or ingress.get("preserveOtlpTraces") is not True:
        raise ArchitectureDocsError("Vector must preserve OTLP trace envelopes")
    if not isinstance(backend, dict) or backend.get("owner") != "tempo":
        raise ArchitectureDocsError("Tempo must own trace persistence/query semantics")
    if backend.get("queryApi") != "127.0.0.1:3200":
        raise ArchitectureDocsError("Tempo query API must remain loopback")
    if not isinstance(export, dict) or export.get("base") != "OTEL_TRACES_EXPORTER=none":
        raise ArchitectureDocsError("Gateway base trace exporter must remain disabled")
    if export.get("requiredForProductCorrectness") is not False:
        raise ArchitectureDocsError("observability must not become a product correctness dependency")
    if observability.get("defaultPosture") != "cold-inactive":
        raise ArchitectureDocsError("heavy observability must remain cold by default")
    if "always-on-mandatory-trace-backend" not in value.get("notAdmitted", []):
        raise ArchitectureDocsError("always-on mandatory tracing must remain not-admitted")
    if "persistent-queryable-trace-backend" in value.get("notAdmitted", []):
        raise ArchitectureDocsError("persistent trace backend cannot remain not-admitted")

    host_northbound = value.get("hostNorthbound")
    if not isinstance(host_northbound, dict) or host_northbound.get("status") not in {"source-cutover-candidate", "deployed"}:
        raise ArchitectureDocsError("Host northbound seam must be a verified source cutover candidate or deployed")
    if host_northbound.get("semanticOwner") != "host" or host_northbound.get("gatewayAuthority") != "projection-only":
        raise ArchitectureDocsError("Gateway must not absorb Host semantic authority")
    if host_northbound.get("workSnapshotSchemaOwner") != "host":
        raise ArchitectureDocsError("Host must remain WorkSnapshot schema owner")
    if set(host_northbound.get("normalTools", [])) != EXPECTED_HOST_NORTHBOUND_TOOLS:
        raise ArchitectureDocsError("normal Host northbound Tool set drifted")
    if host_northbound.get("adminOnlyDirect") != ["host.status"]:
        raise ArchitectureDocsError("Host status/Doctor must remain direct admin/recovery only")
    if host_northbound.get("connectorCatalogOwner") != "mcp-client-connector":
        raise ArchitectureDocsError("connector catalog freshness owner drifted")


def validate_plugin(value: dict[str, Any]) -> None:
    servers = value.get("mcpServers")
    if not isinstance(servers, dict) or set(servers) != {"ordivon-gateway"}:
        raise ArchitectureDocsError("default Plugin must declare exactly one Gateway MCP server")
    gateway = servers["ordivon-gateway"]
    if not isinstance(gateway, dict) or gateway.get("url") != "https://gateway-mcp.ordivon.com/mcp":
        raise ArchitectureDocsError("default Plugin Gateway endpoint drifted")


def route_capabilities(source: str) -> set[str]:
    return set(re.findall(r'capability="([^"]+)"', source))


def gateway_tools(source: str) -> set[str]:
    return set(re.findall(r'@server\.tool\(name="([^"]+)"\)', source))


def validate_source_tool_surface(
    observed_tools: set[str], manifest: dict[str, Any], *, service: str
) -> set[str]:
    _require_exact_schema_one(manifest, f"{service} source Tool manifest")
    if manifest.get("kind") != "ordivon.mcp-tool-surface":
        raise ArchitectureDocsError(f"{service} source Tool manifest kind drifted")
    if manifest.get("service") != service:
        raise ArchitectureDocsError(f"{service} source Tool manifest service identity drifted")
    tools = manifest.get("tools")
    if not isinstance(tools, list) or not all(isinstance(item, str) and item for item in tools):
        raise ArchitectureDocsError(f"{service} source Tool manifest tools must be strings")
    if len(tools) != len(set(tools)):
        raise ArchitectureDocsError(f"{service} source Tool manifest contains duplicate tools")
    declared_tools = set(tools)
    if observed_tools != declared_tools:
        raise ArchitectureDocsError(
            f"{service} source Tool surface differs from source manifest: {sorted(observed_tools)}"
        )
    return declared_tools


def validate_deployed_source_tool_relation(
    graph: dict[str, Any], source_tools: set[str]
) -> None:
    host_northbound = graph.get("hostNorthbound")
    default_northbound = graph.get("defaultNorthbound")
    if not isinstance(host_northbound, dict) or not isinstance(default_northbound, dict):
        raise ArchitectureDocsError("deployed/source Tool relation requires northbound projections")
    deployed_tools = host_northbound.get("normalTools")
    if not isinstance(deployed_tools, list) or not all(
        isinstance(item, str) and item for item in deployed_tools
    ):
        raise ArchitectureDocsError("deployed Host normalTools must be strings")
    deployed_set = set(deployed_tools)
    if len(deployed_tools) != len(deployed_set):
        raise ArchitectureDocsError("duplicate deployed Host normalTools")
    missing_from_source = deployed_set - source_tools
    if missing_from_source:
        raise ArchitectureDocsError(
            "deployed Host northbound claims tools absent from current Gateway source: "
            f"{sorted(missing_from_source)}"
        )
    declared_count = default_northbound.get("declaredToolCount")
    if type(declared_count) is not int:
        raise ArchitectureDocsError("deployed Gateway declaredToolCount must be an exact integer")
    if declared_count < len(deployed_set):
        raise ArchitectureDocsError("deployed Gateway declaredToolCount undercounts deployed Host tools")
    if declared_count > len(source_tools):
        raise ArchitectureDocsError("deployed Gateway declaredToolCount exceeds current source surface")


def validate_current_document(text: str) -> None:
    required = [
        "Status: **CURRENT DEPLOYED PROJECTION — NON-AUTHORITATIVE**",
        "Method Router ≠ Capability Router",
        "Harness is not currently a routed Gateway owner",
        "historical Ordivon Agent Service is **RETIRED**",
        "OTEL_TRACES_EXPORTER=none",
        "Vector OTLP → Tempo",
        "deployed on demand",
        "cold/inactive by default",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ArchitectureDocsError(f"current architecture document missing: {missing}")
    for forbidden in (
        "planned thin Gateway",
        "Gateway: **BUILD THIN",
        "Method Router: **BUILD AS SKILL",
        "default Agent Plugin still points directly",
    ):
        if forbidden in text:
            raise ArchitectureDocsError(f"stale current-state wording present: {forbidden}")



def _source_bound_file(root: Path, relative_path: str, label: str) -> Path:
    """Require registered architecture input bytes to belong to this SourceCut."""
    relative = Path(relative_path)
    if not relative_path or relative.is_absolute() or ".." in relative.parts:
        raise ArchitectureDocsError(f"invalid {label} path")
    expected = root.resolve() / relative
    if not expected.is_file() or expected.resolve() != expected:
        raise ArchitectureDocsError(f"{label} escapes SourceCut")
    return expected



def validate_owner_lego_source_evidence(
    root: Path, relative: str, plan: dict[str, Any],
    *, git_tree: dict[str, str] | None = None,
) -> set[str]:
    """Bind an Owner's declared project evidence to existing SourceCut files.

    This checks only project.sourceEvidence, which is explicitly a file list.
    Node.evidence also contains historical textual observations; treating all
    of those as paths would create a false authority and false failures.
    """
    owner, delimiter, _ = relative.partition("/planning/")
    if not delimiter:
        raise ArchitectureDocsError("invalid Owner LEGO plan location")
    project = plan.get("project")
    refs = project.get("sourceEvidence") if isinstance(project, dict) else None
    if not isinstance(refs, list) or not refs:
        raise ArchitectureDocsError(f"{owner}: missing Owner LEGO sourceEvidence")
    # Provenance is one SourceCut path, not one human spelling. An Owner may
    # express a path relative to its root or as a complete Owner-prefixed
    # path, but neither may mint a second proof for the same source bytes.
    seen: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str) or not ref or ref != ref.strip():
            raise ArchitectureDocsError(f"{owner}: invalid or duplicate Owner LEGO sourceEvidence")
        segments = ref.split("/")
        if ".." in segments:
            raise ArchitectureDocsError(f"{owner}: invalid Owner LEGO sourceEvidence path")
        if any(segment in {"", "."} for segment in segments):
            raise ArchitectureDocsError(f"{owner}: non-canonical Owner LEGO sourceEvidence path")
        path = ref if ref.startswith(f"{owner}/") else f"{owner}/{ref}"
        if path in seen:
            raise ArchitectureDocsError(f"{owner}: invalid or duplicate Owner LEGO sourceEvidence path")
        seen.add(path)
        if git_tree is None:
            _source_bound_file(root, path, "Owner LEGO sourceEvidence")
        else:
            identity = git_tree.get(path, "")
            mode, kind, _ = (identity.split(":") if identity.count(":") == 2 else ("", "", ""))
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ArchitectureDocsError(f"Owner LEGO sourceEvidence absent/nonregular in Git SourceCut: {path}")
    return seen


def validate_owner_lego_dependencies(
    plan: dict[str, Any], owner: str,
) -> tuple[set[str], tuple[tuple[str, ...], ...]]:
    """Well-founded *declared prerequisites*, not a workflow/execution graph.

    Node.dependencies and typed DEPENDENCY edges are equivalent prerequisite
    syntax in different existing natural-Owner LEGO plans.  DATA, CONTROL,
    EFFECT and OBSERVATION edges are not prerequisite claims.
    """
    _require_exact_schema_one(plan, "owner LEGO prerequisites")
    nodes = plan.get("nodes")
    if not isinstance(nodes, list):
        raise ArchitectureDocsError("owner-local LEGO nodes missing")
    if not nodes:
        raise ArchitectureDocsError(f"{owner}: empty LEGO owner graph")
    graph: dict[str, set[str]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"]:
            raise ArchitectureDocsError("untyped LEGO node identity")
        identity = node["id"]
        if not _canonical_owner_lego_id(identity):
            raise ArchitectureDocsError("non-canonical LEGO node identity")
        if identity in graph:
            raise ArchitectureDocsError("duplicate LEGO node identity")
        depends = node.get("dependencies")
        if not isinstance(depends, list) or any(
            not isinstance(value, str) or not value for value in depends
        ):
            raise ArchitectureDocsError("untyped LEGO dependencies")
        if len(depends) != len(set(depends)):
            raise ArchitectureDocsError("duplicate LEGO dependency")
        graph[identity] = set(depends)
    node_ids = set(graph)
    if any(d not in node_ids for deps in graph.values() for d in deps):
        raise ArchitectureDocsError("unknown LEGO dependency")
    # Reuse the same total typed relation check without altering the
    # existing node/dependency/slice error precedence.
    for source, kind, target in _validated_owner_lego_edges(
        plan.get("edges", []), node_ids,
    ):
        if kind == "DEPENDENCY":
            graph[target].add(source)
    sorter = TopologicalSorter(graph)
    try:
        sorter.prepare()
    except CycleError as error:
        raise ArchitectureDocsError("cyclic LEGO dependencies") from error
    frontiers: list[tuple[str, ...]] = []
    while sorter.is_active():
        ready = tuple(sorted(sorter.get_ready()))
        frontiers.append(ready)
        sorter.done(*ready)
    return node_ids, tuple(frontiers)


def validate_formal_issue_census(
    census: dict[str, Any], plans: dict[str, dict[str, Any]], *, root: Path = ROOT
) -> None:
    """Check LEGO reference integrity, never implementation or domain acceptance."""
    _require_exact_schema_one(census, "formal issue census")
    if census.get("kind") != "ordivon.formal-lego-issue-census-evidence":
        raise ArchitectureDocsError("unexpected issue census kind")
    if census.get("truthRole") != "time-scoped-audit-evidence-not-registry-or-admission":
        raise ArchitectureDocsError("issue census must remain non-authoritative")

    # Preserve the exact Git object-ID boundary on evidence source cuts;
    # this does NOT establish object reachability or consumer acceptance.
    source = census.get("source")
    if not isinstance(source, dict):
        raise ArchitectureDocsError("issue census lacks Git source cut")
    if "protectedGithubMain" not in source:
        raise ArchitectureDocsError("issue census lacks protected Git source revision")
    for role in ("protectedGithubMain", "linuxLocalMain", "mergeBase", "researchLocalMain"):
        if role not in source:  # Incremental evidence may declare a narrower cut.
            continue
        oid = source[role]
        if not isinstance(oid, str) or re.fullmatch(r"[0-9a-f]{40}", oid) is None:
            raise ArchitectureDocsError(f"invalid Git source revision: {role}")

    issues = census.get("issues")
    if not isinstance(issues, list) or not issues:
        raise ArchitectureDocsError("issue census must contain typed issues")
    owner_manifest = tomllib.loads(
        _source_bound_file(root, "tools/repo/owners.toml", "owner manifest").read_text(
            encoding="utf-8"
        )
    )
    known_owners = {row["root"].removesuffix("/") for row in owner_manifest["owners"]}
    known_owners.add("tools/repo")  # Repository mechanics, not a domain owner.
    issue_ids: set[str] = set()
    for issue in issues:
        if not isinstance(issue, dict):
            raise ArchitectureDocsError("issue census entry must be an object")
        issue_id = issue.get("id")
        if not isinstance(issue_id, str) or not issue_id:
            raise ArchitectureDocsError("issue identity required")
        # Use the existing Owner LEGO key grammar for Problem LEGO identities.
        # Unicode confusables and whitespace aliases must not fork one issue.
        if not _canonical_owner_lego_id(issue_id):
            raise ArchitectureDocsError("non-canonical issue identity")
        if issue_id in issue_ids:
            raise ArchitectureDocsError(f"duplicate issue identity: {issue_id}")
        issue_ids.add(issue_id)
        if issue.get("problemClass") == "DATABASE_AUTHORITY_CONVERGENCE":
            recent = issue.get("latestRequalification")
            if recent is not None:
                if not isinstance(recent, dict):
                    raise ArchitectureDocsError(f"database issue {issue_id} needs typed requalification")
                source_cut = recent.get("sourceCut")
                if not isinstance(source_cut, str) or re.fullmatch(r"[0-9a-f]{40}", source_cut) is None:
                    raise ArchitectureDocsError(f"database issue {issue_id} has invalid fresh SourceCut")
                # An observational census never confers data migration/cutover
                # authority, even with passing native tests.  PG writer/reader
                # admission must come from the actual owner effect and receipt.
                if recent.get("cutoverAdmission") != "NOT_ADMITTED":
                    raise ArchitectureDocsError(f"database issue {issue_id} falsely admits PG cutover")
                evidence_paths = recent.get("nativeConsumerEvidence")
                if not isinstance(evidence_paths, list) or not evidence_paths:
                    raise ArchitectureDocsError(f"database issue {issue_id} lacks owner-native source evidence")
                if any(not isinstance(evidence, str) for evidence in evidence_paths):
                    raise ArchitectureDocsError(f"database issue {issue_id} has invalid source evidence")
                if len(set(evidence_paths)) != len(evidence_paths):
                    raise ArchitectureDocsError(f"database issue {issue_id} repeats source evidence")
                for evidence in evidence_paths:
                    _source_bound_file(root, evidence, "database issue owner-native evidence")
        if issue.get("naturalOwner") not in known_owners:
            raise ArchitectureDocsError(f"issue {issue_id} has undeclared naturalOwner")
        for field in ("problemClass", "naturalOwner", "standing", "evidence", "consumers", "formalObligation"):
            if not isinstance(issue.get(field), str) or not issue[field].strip():
                raise ArchitectureDocsError(f"issue {issue_id} lacks {field}")
        if issue["problemClass"] not in FORMAL_ISSUE_PROBLEM_CLASSES:
            raise ArchitectureDocsError(
                f"issue {issue_id} has unknown formal issue problemClass"
            )

    # Time-scoped Problem LEGO readsets supply positive paths, not proof closure.
    if census.get("sourceReadsetContract") is not None:
        if census["sourceReadsetContract"] != "positive-owner-source-observation-r1":
            raise ArchitectureDocsError("unknown problem readset contract")
        cut = source.get("readsetObservationSourceCut")
        if not isinstance(cut, str) or not re.fullmatch(r"[0-9a-f]{40}", cut):
            raise ArchitectureDocsError("problem readset lacks observed SourceCut")
        # Git owns source path membership, not a mutable checkout tree. This
        # validates OBSERVED source addresses, not executable source refinement.
        tree = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(root), "ls-tree",
             "-r", "-z", "--name-only", cut],
            capture_output=True, check=False,
        )
        if tree.returncode != 0:
            raise ArchitectureDocsError("problem evidence SourceCut is not readable")
        observed_paths = set(filter(None, tree.stdout.decode(
            "utf-8", "surrogateescape").split(chr(0))))
        for issue in issues:
            e = issue.get("readsetEvidence")
            fields = {"sourceCut", "sourcePaths", "consumerPaths", "verifierPath",
                      "counterexample", "dependencyClosure", "verificationStanding"}
            if not isinstance(e, dict) or set(e) != fields or e["sourceCut"] != cut:
                raise ArchitectureDocsError("missing typed problem source/readset evidence")
            if (e["dependencyClosure"], e["verificationStanding"]) != ("UNKNOWN", "UNKNOWN"):
                raise ArchitectureDocsError("source inventory cannot establish verification")
            for field in ("sourcePaths", "consumerPaths"):
                paths = e[field]
                if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
                    raise ArchitectureDocsError("missing, duplicate or untyped problem path")
                for path in paths:
                    if not isinstance(path, str):
                        raise ArchitectureDocsError("untyped problem source path")
                    if path not in observed_paths:
                        raise ArchitectureDocsError("problem source path not in observed SourceCut")
                    _source_bound_file(root, path, "problem " + field)
            if not isinstance(e["verifierPath"], str):
                raise ArchitectureDocsError("untyped verifier")
            if e["verifierPath"] not in observed_paths:
                raise ArchitectureDocsError("problem verifier missing from observed SourceCut")
            _source_bound_file(root, e["verifierPath"], "problem verifier")
            negative = e["counterexample"]
            if not isinstance(negative, dict) or set(negative) != {"path", "symbol"}:
                raise ArchitectureDocsError("missing negative control")
            if not isinstance(negative["path"], str) or not isinstance(negative["symbol"], str):
                raise ArchitectureDocsError("untyped negative control")
            if negative["path"] not in observed_paths:
                raise ArchitectureDocsError("counterexample not in observed SourceCut")
            test_source = _source_bound_file(root, negative["path"], "negative control")
            if (not negative["symbol"].startswith("test_")
                or not re.search(r"\bdef\s+" + re.escape(negative["symbol"]) + r"\s*\(",
                                 test_source.read_text(encoding="utf-8"))):
                raise ArchitectureDocsError("negative control not source-addressable")
            if "consumerPartitions" in issue:
                if issue["registration"]["state"] != "UNREGISTERED":
                    raise ArchitectureDocsError("cross-owner PG falsely registered")
                try:
                    from tools.repo.check_sql_dialects import tracked_owner_sqlite_calls
                except ModuleNotFoundError:
                    from check_sql_dialects import tracked_owner_sqlite_calls
                actual = tracked_owner_sqlite_calls(root)
                declared = {}
                seen = set()
                for part in issue["consumerPartitions"]:
                    if not isinstance(part, dict) or set(part) != {"owner","sourcePaths","directCallsites"}:
                        raise ArchitectureDocsError("invalid PG consumer partition")
                    owner, paths = part["owner"], part["sourcePaths"]
                    if not isinstance(owner, str) or owner in seen or not isinstance(paths, list):
                        raise ArchitectureDocsError("duplicate PG owner")
                    seen.add(owner)
                    if not paths or paths != sorted(set(paths)):
                        raise ArchitectureDocsError("invalid PG owner paths")
                    for path in paths:
                        if not isinstance(path, str) or not path.startswith(owner + "/") or path in declared or path not in actual:
                            raise ArchitectureDocsError("PG consumer partition drift")
                        declared[path] = actual[path]
                    if sum(declared[p] for p in paths) != part["directCallsites"]:
                        raise ArchitectureDocsError("PG consumer callsite count drift")
                if declared != actual or sorted(e["consumerPaths"]) != sorted(actual):
                    raise ArchitectureDocsError("PG consumer partitions not exhaustive")

    # The existing GIT-01 list is an evidence projection, not deletion
    # authority. Validate its complete source-bound identity/type relation at
    # the canonical architecture gate, not only in handpicked regression tests.
    # Older selections may predate sourceQualification; preserve their bounded
    # claims rather than inventing missing historical proofs.
    oid_pattern = re.compile(r"[0-9a-f]{40}")
    allowed_dispositions = GIT01_ALLOWED_DISPOSITIONS
    allowed_evidence_scopes = GIT01_ALLOWED_EVIDENCE_SCOPES
    for issue in issues:
        if issue["id"] != "GIT-01":
            continue
        source_cut = issue.get("consumerSourceCut")
        if not isinstance(source_cut, dict) or not oid_pattern.fullmatch(
            str(source_cut.get("localMain", ""))
        ):
            raise ArchitectureDocsError("invalid historical Git local SourceCut")
        selections = issue.get("consumerSelections")
        if not isinstance(selections, list) or not selections:
            raise ArchitectureDocsError("historical Git selections missing")
        identities: set[str] = set()
        cohort_ids: set[str] = set()
        # One finite partial relation: weak or source-only evidence must not
        # be upgraded into a different native-consumer verdict by a merge.
        scope_disposition = GIT01_SCOPE_DISPOSITION
        for entry in selections:
            if not isinstance(entry, dict):
                raise ArchitectureDocsError("historical Git selection must be typed")
            oid = entry.get("localCommit")
            if not isinstance(oid, str) or not oid_pattern.fullmatch(oid):
                raise ArchitectureDocsError("invalid historical Git SHA")
            if oid in identities:
                raise ArchitectureDocsError("duplicate historical Git selection")
            # A non-primary cohort member already has an Owner disposition.
            # Selecting it separately would allow parallel agents to make
            # conflicting decisions about the same immutable Git object.
            if oid in cohort_ids:
                raise ArchitectureDocsError("historical Git cohort member collision")
            identities.add(oid)
            owner = entry.get("owner")
            if not isinstance(owner, str) or (
                owner not in known_owners
                and not (
                    owner == "ROOT_UNOWNED"
                    and entry.get("disposition") == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
                    and entry.get("evidenceScope") == "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN"
                    and isinstance(entry.get("sourceQualification"), dict)
                    and entry["sourceQualification"].get("consumerStanding")
                    == "NO_IN_TREE_CONSUMER_EXTERNAL_UNKNOWN"
                )
            ):
                raise ArchitectureDocsError("undeclared historical Git owner")
            for field in ("consumer", "remoteWitness"):
                if not isinstance(entry.get(field), str) or not entry[field].strip():
                    raise ArchitectureDocsError(f"historical Git selection missing {field}")
            if not isinstance(entry.get("disposition"), str) or entry["disposition"] not in allowed_dispositions:
                raise ArchitectureDocsError("invalid historical Git disposition")
            if not isinstance(entry.get("evidenceScope"), str) or entry["evidenceScope"] not in allowed_evidence_scopes:
                raise ArchitectureDocsError("invalid historical Git evidenceScope")
            expected = scope_disposition.get(entry["evidenceScope"])
            if expected is not None and entry["disposition"] != expected:
                raise ArchitectureDocsError("incompatible historical Git evidence and disposition")
            if "evaluatedRemoteMain" in entry and (
                not isinstance(entry["evaluatedRemoteMain"], str)
                or not oid_pattern.fullmatch(entry["evaluatedRemoteMain"])
            ):
                raise ArchitectureDocsError("invalid historical Git evaluated SourceCut")
            cohort = entry.get("historicalCohort")
            if cohort is not None and (
                not isinstance(cohort, list)
                or not cohort
                or oid not in cohort
                or any(not isinstance(v, str) or not oid_pattern.fullmatch(v) for v in cohort)
                or len(cohort) != len(set(cohort))
                or not cohort_ids.isdisjoint(cohort)
                or not (set(cohort) - {oid}).isdisjoint(identities)
            ):
                raise ArchitectureDocsError("invalid historical Git cohort")
            if cohort is not None:
                cohort_ids.update(cohort)
            source_proof = entry.get("sourceQualification")
            # A port cannot be authorized by a historical blob match.
            if (
                entry["disposition"] == "PORT_REQUIRED_OWNER_EFFECT"
                and (
                    entry["evidenceScope"] != "NATIVE_CONSUMER_PASS"
                    or not isinstance(source_proof, dict)
                    or source_proof.get("branchDeletionAllowed") is not False
                )
            ):
                raise ArchitectureDocsError(
                    "PORT_REQUIRED_OWNER_EFFECT requires native Owner acceptance "
                    "and cannot authorize branch deletion"
                )
            if source_proof is not None:
                if not isinstance(source_proof, dict):
                    raise ArchitectureDocsError("invalid historical Git source qualification")
                if source_proof.get("branchDeletionAllowed") is not False:
                    raise ArchitectureDocsError(
                        "historical Git selection cannot authorize branch deletion"
                    )
                if source_proof.get("localMain") != source_cut["localMain"]:
                    raise ArchitectureDocsError("historical Git selection local SourceCut mismatch")
                remote_oid = source_proof.get("protectedMain")
                if not isinstance(remote_oid, str) or not oid_pattern.fullmatch(remote_oid):
                    raise ArchitectureDocsError("invalid historical Git protected SourceCut")
            # A claim of full-tree direct-child cancellation must be coherent.
            # This validates stated OIDs, not their reachability in the Git DAG.
            if entry["disposition"] == "SKIP_CANCELLED_HISTORY_PAIR":
                revert = entry.get("pairedRevertCommit")
                before = entry.get("beforeTreeOid")
                after = entry.get("afterTreeOid")
                if (
                    not isinstance(revert, str)
                    or oid_pattern.fullmatch(revert) is None
                    or revert == oid
                    or not isinstance(before, str)
                    or oid_pattern.fullmatch(before) is None
                    or not isinstance(after, str)
                    or oid_pattern.fullmatch(after) is None
                    or before != after
                    or source_proof is None
                    or source_proof.get("patchRelation") != "INVERSE_DIRECT_CHILD"
                ):
                    raise ArchitectureDocsError("invalid GIT-01 cancelled pair tree proof")
            if ("branchDeletionAllowed" in entry
                and entry["branchDeletionAllowed"] is not False
            ):
                raise ArchitectureDocsError(
                    "historical Git selection cannot authorize branch deletion"
                )

        # Final-standing claims cannot conflict with an explicitly blocked source.
        blockers = issue.get("consumerBlockedSelections", [])
        if not isinstance(blockers, list):
            raise ArchitectureDocsError("invalid historical Git blocker set")
        blocked: set[str] = set()
        for blocker in blockers:
            if not isinstance(blocker, dict):
                raise ArchitectureDocsError("invalid historical Git blocker")
            commit = blocker.get("localCommit")
            if not isinstance(commit, str) or not oid_pattern.fullmatch(commit):
                raise ArchitectureDocsError("invalid historical Git blocker identity")
            if commit in identities or commit in cohort_ids:
                raise ArchitectureDocsError("historical Git selected and blocked collision")
            if commit in blocked:
                raise ArchitectureDocsError("duplicate historical Git blocker")
            if blocker.get("branchDeletionAllowed") is not False:
                raise ArchitectureDocsError("historical Git blocker cannot authorize branch deletion")
            blocked.add(commit)

    representation_types = FORMAL_ISSUE_REPRESENTATION_TYPES
    for issue in issues:
        rep = issue.get("representation")
        issue_id = issue["id"]
        if not isinstance(rep, dict):
            raise ArchitectureDocsError(f"issue {issue_id} missing representation")
        if not isinstance(rep.get("primary"), str) or rep["primary"] not in representation_types:
            raise ArchitectureDocsError(f"issue {issue_id} unknown primary representation")
        supporting = rep.get("supporting")
        if (
            not isinstance(supporting, list)
            or len(supporting) > 1
            or not all(isinstance(x, str) for x in supporting)
            or len(supporting) != len(set(supporting))
            or any(x not in representation_types or x == rep["primary"] for x in supporting)
        ):
            raise ArchitectureDocsError(f"issue {issue_id} invalid supporting representation")
        skill = rep.get("methodSkill")
        if skill is not None:
            if (
                not isinstance(skill, str)
                or not skill.startswith(".agents/skills/")
                or not skill.endswith("/SKILL.md")
                or ".." in Path(skill).parts
            ):
                raise ArchitectureDocsError(f"issue {issue_id} references unavailable method Skill")
            # The exact source cut supplied to the validator owns its Skills.
            # A same-named Skill in another checkout or via a symlink is not evidence.
            candidate_skill = root / skill
            if (
                not candidate_skill.is_file()
                or not candidate_skill.resolve().is_relative_to(root.resolve())
            ):
                raise ArchitectureDocsError(f"issue {issue_id} references unavailable method Skill")
        for field in ("requiredWitness", "selectionReason"):
            if not isinstance(rep.get(field), str) or not rep[field].strip():
                raise ArchitectureDocsError(f"issue {issue_id} missing {field}")

    registrations = census.get("registrations")
    if not isinstance(registrations, list) or not registrations:
        raise ArchitectureDocsError("issue census needs owner-local LEGO links")
    seen: set[tuple[str, str]] = set()
    for ref in registrations:
        if not isinstance(ref, dict):
            raise ArchitectureDocsError("LEGO registration must be an object")
        plan_path, slice_id = ref.get("ownerPlan"), ref.get("slice")
        if not isinstance(plan_path, str) or not isinstance(slice_id, str) or not slice_id:
            raise ArchitectureDocsError("LEGO registration identity missing")
        # Registration identities are canonical SourceCut paths. Path() would
        # normalize '/./' and '//' and let aliases masquerade as separate
        # Owner/slice LEGO witnesses in a multi-agent issue census.
        if any(segment in {"", ".", ".."} for segment in plan_path.split("/")):
            raise ArchitectureDocsError("non-canonical owner-local LEGO path")
        _source_bound_file(root, plan_path, "owner-local LEGO plan")
        if (plan_path, slice_id) in seen:
            raise ArchitectureDocsError("duplicate owner-local LEGO link")
        seen.add((plan_path, slice_id))
        plan = plans.get(plan_path)
        if not isinstance(plan, dict) or plan.get("truthRole") != "planning-projection-not-project-truth":
            raise ArchitectureDocsError("owner-local LEGO plan must remain non-authoritative")
        node_ids, _ = validate_owner_lego_dependencies(plan, plan_path)
        hits = [s for s in plan.get("slices", []) if isinstance(s, dict) and s.get("id") == slice_id]
        if len(hits) != 1:
            raise ArchitectureDocsError(f"owner-local LEGO slice {slice_id} not unique")
        slice_ = hits[0]
        bound = slice_.get("nodeIds")
        if not isinstance(bound, list) or not bound or not all(isinstance(n, str) and n in node_ids for n in bound):
            raise ArchitectureDocsError(f"unknown LEGO node in {slice_id}")
        clauses = slice_.get("acceptance")
        if not isinstance(clauses, list) or not clauses or not all(isinstance(c, str) and c.strip() for c in clauses):
            raise ArchitectureDocsError(f"LEGO slice {slice_id} needs falsifiable acceptance")
        if slice_.get("status") not in {"PROPOSED", "IMPLEMENTED", "VERIFIED", "RETIRED", "COMPLETE"}:
            raise ArchitectureDocsError(f"LEGO slice {slice_id} has unknown state")


    # Registration is a total, typed relation: every observed issue is either
    # linked to a verified owner-local identity or retains an explicit gap.
    # Neither state asserts runtime behavior has been proved.
    linked_pairs: set[tuple[str, str]] = set()
    for issue in issues:
        issue_id = issue["id"]
        registration = issue.get("registration")
        if not isinstance(registration, dict):
            raise ArchitectureDocsError(f"issue {issue_id} lacks registration disposition")
        state = registration.get("state")
        if state == "UNREGISTERED":
            if not isinstance(registration.get("reason"), str) or not registration["reason"].strip():
                raise ArchitectureDocsError(f"issue {issue_id} lacks unregistered reason")
            if "ownerPlan" in registration or "slice" in registration:
                raise ArchitectureDocsError(f"issue {issue_id} mixes gap and linked registration")
        elif state == "LINKED":
            plan_path = registration.get("ownerPlan")
            slice_id = registration.get("slice")
            if not isinstance(plan_path, str) or not isinstance(slice_id, str):
                raise ArchitectureDocsError(f"issue {issue_id} has invalid owner-local LEGO link")
            pair = (plan_path, slice_id)
            if pair not in seen:
                raise ArchitectureDocsError(f"issue {issue_id} links unknown owner-local LEGO")
            plan_path = pair[0]
            if plan_path.split("/planning/")[0] != issue["naturalOwner"]:
                raise ArchitectureDocsError(f"issue {issue_id} linked outside natural owner")
            linked_pairs.add(pair)
        else:
            raise ArchitectureDocsError(f"issue {issue_id} has unknown registration state")
    if linked_pairs != seen:
        raise ArchitectureDocsError("orphan owner-local LEGO registration")



def project_formal_problem_readsets(census: dict[str, Any], *,
                                    source_cut: str, scope_prefix: str) -> dict[str, Any]:
    """Project positive issue edges into one native directory-scoped Git selector.

    Read edges outside the scoped Git namespace remain UNKNOWN; separate
    queries are required, never automatic proof reuse across directories.
    """
    if (census.get("sourceReadsetContract") != "positive-owner-source-observation-r1"
        or census.get("source", {}).get("readsetObservationSourceCut") != source_cut
        or not isinstance(scope_prefix, str) or not scope_prefix.endswith("/")
        or scope_prefix.startswith("/") or chr(92) in scope_prefix
        or any(part in {"", ".", ".."} for part in scope_prefix[:-1].split("/"))):
        raise ArchitectureDocsError("unqualified problem readset Git scope")
    items = []
    unscoped = {}
    for issue in census["issues"]:
        e = issue["readsetEvidence"]
        if e["sourceCut"] != source_cut:
            raise ArchitectureDocsError("stale issue SourceCut")
        all_paths = sorted(set(e["sourcePaths"] + e["consumerPaths"] +
                               [e["verifierPath"], e["counterexample"]["path"]]))
        paths = [p for p in all_paths if p.startswith(scope_prefix)]
        if not paths:
            continue
        unscoped["problem:" + issue["id"]] = len(all_paths) - len(paths)
        items.append({"id": "problem:" + issue["id"],
                      "sourcePaths": paths, "dependenciesComplete": False})
    return {
        "kind": "ordivon.source-readset-evidence",
        "truthRole": "scoped-positive-problem-edges-not-proof",
        "sourceCut": source_cut, "scopePrefix": scope_prefix, "items": items,
        "unscopedDependencies": unscoped,
        "dependencyQualification": "POSITIVE_GIT_EDGES_OTHER_SCOPES_AND_ENV_UNKNOWN",
        "proofReuseAdmissible": False,
    }


def validate_r21_lego_vocabulary(document: str, *, root: Path = ROOT) -> None:
    """Keep the already accepted six-role LEGO interface distinct from optional math.

    This is a documentation/source-bound gate, not a universal proof schema.
    Consumer paths must name existing Owner-native falsification witnesses.
    """
    canonical = "L = (identity, responsibility, inputs, outputs, contract, acceptance)"
    if document.count(canonical) != 1:
        raise ArchitectureDocsError("R2.1 canonical LEGO contract must be unique")
    if re.search(r"\bL\s*=\s*\(\s*(?:C\s*,\s*I\s*,\s*O\s*,\s*S\s*,|I\s*,\s*O\s*,\s*A\s*,)", document):
        raise ArchitectureDocsError("R2.1 competing LEGO mathematical definition")
    if r"\mathrm{Semantics}(L)" not in document:
        raise ArchitectureDocsError("R2.1 optional semantics must be distinct from LEGO")
    disabled = {
        "unittest.skip", "unittest.skipIf", "unittest.skipUnless",
        "pytest.mark.skip", "pytest.mark.skipif", "pytest.mark.xfail",
    }

    # The architecture prose names these existing tests as Owner consumers.
    # Mere file existence is a false-green: a removed test body would still
    # allow the R2.1 document to claim an executable native witness.
    # AST is the mature Python parser; this proves callable identity only,
    # never test execution, refinement, or domain acceptance.
    for relative, class_name, symbol in (
        ("services/runtime/scripts/tests/test_mcp_e2e_reconciliation.py",
         "ReconciliationContractTests", "test_reconciliation_fails_closed_if_attempt_identity_changes"),
        ("services/host/tests/test_social_work_fabric_postgres.py",
         None, "test_work_snapshot_cas_race_has_one_winner"),
        ("services/harness/tests/test_agent_automation_browserless.py",
         "BrowserlessAutomationServiceTests", "test_birth_replay_does_not_materialize_again"),
        ("platform/network/tests/test_claude_egress_readiness_consumer.py",
         None, "test_real_consumer_readiness_fails_closed_for_upstream_faults"),
    ):
        if relative not in document:
            raise ArchitectureDocsError(f"R2.1 missing current consumer witness: {relative}")
        # Reuse this Repo Owner's existing source-bound path validator: the
        # named witness may not be borrowed from outside the frozen source.
        path = _source_bound_file(root, relative, "R2.1 consumer witness")
        try:
            syntax = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise ArchitectureDocsError(
                f"R2.1 consumer witness invalid Python source: {relative}: {exc}"
            ) from exc
        # Detect source-provable *module-wide* disabling marks, including
        # composite pytestmark and augmented assignments.  A dynamic skipif
        # (e.g. Host's DSN-dependent integration tests) remains conditional
        # evidence rather than a source-proved permanent disable.
        for statement in syntax.body:
            if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    statement.targets if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                if (
                    any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in targets)
                    and any(
                        (
                            isinstance(node, ast.Attribute)
                            and ast.unparse(node) in {"pytest.mark.skip", "pytest.mark.xfail"}
                        ) or (
                            isinstance(node, ast.Call)
                            and ast.unparse(node.func) == "pytest.mark.skipif"
                            and bool(node.args)
                            and isinstance(node.args[0], ast.Constant)
                            and node.args[0].value is True
                        )
                        for node in ast.walk(statement.value)
                    )
                ):
                    raise ArchitectureDocsError(
                        f"R2.1 disabled module consumer witness: {relative}::{symbol}"
                    )
        if class_name is None:
            scope = syntax.body
        else:
            classes = [
                node for node in syntax.body
                if isinstance(node, ast.ClassDef) and node.name == class_name
                and any(
                    isinstance(base, ast.Attribute)
                    and base.attr == "TestCase"
                    for base in node.bases
                )
            ]
            scope = classes[0].body if len(classes) == 1 else ()
        count = sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == symbol
            for node in scope
        )
        if count != 1:
            raise ArchitectureDocsError(
                f"R2.1 consumer witness nonunique or missing callable: "
                f"{relative}::{symbol} (definitions={count})"
            )
        # Source existence and unique names are not execution proofs.
        # Explicit unittest/pytest opt-outs cannot witness an always-on
        # acceptance claim; runtime test execution remains Owner evidence.
        witness = next(
            node for node in scope
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == symbol
        )
        # A file and a named callable are only source-level evidence.  A
        # docstring/pass/ellipsis placeholder cannot even attempt the
        # asserted Owner acceptance witness; do not promote it as runnable.
        effective_body = [
            statement for statement in witness.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
        ]
        if not effective_body or all(
            isinstance(statement, ast.Pass)
            or (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and statement.value.value is Ellipsis
            )
            for statement in effective_body
        ):
            raise ArchitectureDocsError(
                f"R2.1 non-executable consumer witness: {relative}::{symbol}"
            )
        decorators = list(witness.decorator_list)
        if class_name is not None:
            decorators.extend(classes[0].decorator_list)
        if any(
            ast.unparse(item.func if isinstance(item, ast.Call) else item) in disabled
            for item in decorators
        ):
            raise ArchitectureDocsError(
                f"R2.1 disabled consumer witness: {relative}::{symbol}"
            )


def validate_repository(root: Path = ROOT) -> None:
    current = root / CURRENT.relative_to(ROOT)
    deployed = root / DEPLOYED.relative_to(ROOT)
    plugin = root / PLUGIN.relative_to(ROOT)
    routes = root / ROUTES.relative_to(ROOT)
    gateway_mcp = root / GATEWAY_MCP.relative_to(ROOT)
    host_northbound_acceptance = root / HOST_NORTHBOUND_ACCEPTANCE.relative_to(ROOT)
    method_router = root / METHOD_ROUTER.relative_to(ROOT)
    readme = root / README.relative_to(ROOT)

    validate_current_document(current.read_text(encoding="utf-8"))
    validate_r21_lego_vocabulary(
        (root / "docs/architecture/AGENT_CONCEPTS_FORMAL_LEGO_RESEARCH_20261024.md").read_text(
            encoding="utf-8"
        ),
        root=root,
    )
    graph = _load_json(deployed)
    validate_deployed_graph(graph)
    validate_plugin(_load_json(plugin))

    observed = route_capabilities(routes.read_text(encoding="utf-8"))
    if observed != EXPECTED_CAPABILITIES:
        raise ArchitectureDocsError(
            f"Gateway route source differs from deployed graph: {sorted(observed)}"
        )

    observed_tools = gateway_tools(gateway_mcp.read_text(encoding="utf-8"))
    source_tools = validate_source_tool_surface(
        observed_tools,
        _load_json(root / GATEWAY_SURFACE_MANIFEST.relative_to(ROOT)),
        service="ordivon-gateway",
    )
    validate_deployed_source_tool_relation(graph, source_tools)
    host_acceptance = _load_json(host_northbound_acceptance)
    if host_acceptance.get("status") not in {
        "SOURCE_CUTOVER_CANDIDATE_VERIFIED_LIVE_PENDING",
        "LIVE_ACCEPTED_CLIENT_REFRESH_PENDING",
    }:
        raise ArchitectureDocsError("Gateway SWF northbound acceptance status drifted")

    if not method_router.is_file():
        raise ArchitectureDocsError("canonical Method Router Skill is missing")
    if "docs/architecture/CURRENT_ARCHITECTURE.md" not in readme.read_text(encoding="utf-8"):
        raise ArchitectureDocsError("root README must point to canonical current architecture")

    tempo = (root / TEMPO_CONFIG.relative_to(ROOT)).read_text(encoding="utf-8")
    vector = (root / VECTOR_CONFIG.relative_to(ROOT)).read_text(encoding="utf-8")
    datasources = (root / GRAFANA_DATASOURCES.relative_to(ROOT)).read_text(encoding="utf-8")
    target = (root / HEAVY_TARGET.relative_to(ROOT)).read_text(encoding="utf-8")
    quadlet = (root / TEMPO_QUADLET.relative_to(ROOT)).read_text(encoding="utf-8")
    trace_acceptance = _load_json(root / TRACE_ACCEPTANCE.relative_to(ROOT))
    if "http_listen_address: 127.0.0.1" not in tempo or 'endpoint: "127.0.0.1:14318"' not in tempo:
        raise ArchitectureDocsError("Tempo trace endpoints must remain loopback")
    if "backend: local" not in tempo:
        raise ArchitectureDocsError("Tempo local backend contract drifted")
    if "traces: true" not in vector or "otel_traces_tempo:" not in vector:
        raise ArchitectureDocsError("Vector OTLP trace preservation/Tempo sink drifted")
    if "http://127.0.0.1:14318/v1/traces" not in vector:
        raise ArchitectureDocsError("Vector Tempo OTLP sink endpoint drifted")
    if "uid: operations-tempo" not in datasources or "type: tempo" not in datasources:
        raise ArchitectureDocsError("Grafana Tempo datasource drifted")
    if "ordivon-tempo.service" not in target:
        raise ArchitectureDocsError("heavy observability profile lost Tempo")
    if "StopTimeout=60" not in quadlet or "TimeoutStopSec=75" not in quadlet:
        raise ArchitectureDocsError("Tempo graceful cold-stop budget drifted")
    if trace_acceptance.get("status") != "ACCEPTED_DEPLOYED_ON_DEMAND":
        raise ArchitectureDocsError("persistent trace backend lacks accepted live evidence")

    # A new owner-local plan must not silently bypass the existing formal
    # checks simply because no historical issue census or hand-picked test
    # references it. This only covers the declared two-level source layout.
    validate_owner_plan_inventory(root)
    validate_owner_plan_projection_carriers(root)

    # Two independent mature graph obligations apply to every registered Owner,
    # whether or not a time-scoped issue census happens to mention its plan.
    # Only DEPENDENCY is a prerequisite; STATE/OBSERVATION feedback may cycle.
    for relative in OWNER_LEGO_PLANS:
        plan = _load_json(_source_bound_file(root, relative, "registered Owner LEGO plan"))
        validate_owner_lego_graph(plan)
        validate_owner_lego_dependencies(plan, relative.split("/planning/", 1)[0])
        validate_owner_lego_source_evidence(root, relative, plan)

    issue_evidence_dir = root / "docs" / "architecture" / "evidence"
    for census_path in issue_evidence_dir.glob("FORMAL_LEGO_ISSUE_CENSUS_*_R*.json"):
        census = _load_json(
            _source_bound_file(root, str(census_path.relative_to(root)), "formal issue census")
        )
        plans: dict[str, dict[str, Any]] = {}
        for ref in census.get("registrations", []):
            if not isinstance(ref, dict) or not isinstance(ref.get("ownerPlan"), str):
                raise ArchitectureDocsError("invalid owner-local LEGO reference")
            relative = Path(ref["ownerPlan"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ArchitectureDocsError("invalid owner-local LEGO path")
            plans[ref["ownerPlan"]] = _load_json(
                _source_bound_file(root, ref["ownerPlan"], "owner-local LEGO plan")
            )
        validate_formal_issue_census(census, plans, root=root)

    for path, marker in HISTORICAL.items():
        candidate = root / path.relative_to(ROOT)
        if marker not in candidate.read_text(encoding="utf-8"):
            raise ArchitectureDocsError(f"historical architecture file lacks supersession marker: {candidate}")


def _select_agent_source_impact(change: dict[str, Any]) -> dict[str, Any]:
    """Reduce read-only Agent context, never strengthen source or proof standing.

    NO_DECLARED_HIT is omitted from the response solely for transport. It is
    not evidence that code, dynamic consumers, installed services or proof
    assumptions have remained valid. All UNKNOWN and future standing kinds,
    changed/unindexed source paths and scoped proof-reuse flags are retained.
    """
    # This is a transport-only source projection. A forged or future input
    # cannot upgrade UNKNOWN/readset status by injecting a proof PASS.
    if change.get("proofReuseAdmissible") is not False:
        raise ArchitectureDocsError(
            "Agent source projection requires explicit proofReuseAdmissible=false"
        )
    rows = change["standingByDeclaredNode"]
    no_hit = [row for row in rows if row["sourceImpactStanding"] == "NO_DECLARED_HIT"]
    selected = [row for row in rows if row["sourceImpactStanding"] != "NO_DECLARED_HIT"]
    return {
        **change,
        "sourceImpactProjection": "CHANGED_OR_UNKNOWN_ONLY",
        "omittedStanding": "NO_DECLARED_HIT",
        "omittedNoDeclaredHitCount": len(no_hit),
        "standingByDeclaredNode": selected,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-problem-readsets", metavar="CENSUS_PATH",
                        help="source-bound readset projection into existing Composition impact-readsets")
    parser.add_argument("--problem-impact-prefix",
                        help="one canonical Git directory prefix, e.g. tools/repo/")
    parser.add_argument("--project-owner-graphs", action="store_true")
    parser.add_argument("--agent-impact", action="store_true",
                        help="compact changed/UNKNOWN source impact for Agent clients; not a proof reuse gate")
    parser.add_argument("--inspect-owner-lego", help="exact registered plan path#node ID at --source-revision")
    parser.add_argument("--inspect-owner-path", help="exact source path at --source-revision")
    parser.add_argument("--source-revision", help="exact Git commit for immutable graph projection")
    parser.add_argument("--compare-source-revision",
                        help="earlier immutable Git commit to compare against --source-revision")
    parser.add_argument("--inspect-python-node", help="registered node ref")
    parser.add_argument("--python-target-source", help="exact node-anchored Python src file")
    args = parser.parse_args(argv)
    try:
        if args.project_problem_readsets:
            if (not args.source_revision or args.problem_impact_prefix is None
                or args.compare_source_revision or args.agent_impact
                or args.project_owner_graphs or args.inspect_owner_path
                or args.inspect_owner_lego or args.inspect_python_node):
                raise ArchitectureDocsError(
                    "problem projection requires exact --source-revision and --problem-impact-prefix")
            path = _source_bound_file(ROOT, args.project_problem_readsets, "problem census")
            census = _load_json(path)
            plans = {
                row["ownerPlan"]: _load_json(
                    _source_bound_file(ROOT, row["ownerPlan"], "problem owner plan")
                ) for row in census["registrations"]
            }
            validate_formal_issue_census(census, plans)
            projection = project_formal_problem_readsets(
                census, source_cut=args.source_revision,
                scope_prefix=args.problem_impact_prefix,
            )
            print(json.dumps(projection, sort_keys=True))
            return 0
        if args.problem_impact_prefix is not None:
            raise ArchitectureDocsError("problem-impact-prefix requires problem projection")
        if args.agent_impact and not (
            args.project_owner_graphs and args.source_revision
            and args.compare_source_revision and not args.inspect_python_node
            and not args.inspect_owner_lego and not args.inspect_owner_path
        ):
            raise ArchitectureDocsError(
                "--agent-impact requires --project-owner-graphs and exact --source-revision "
                "plus --compare-source-revision, without node inspection"
            )
        if args.source_revision and not (args.project_owner_graphs or args.inspect_python_node or args.inspect_owner_lego or args.inspect_owner_path):
            raise ArchitectureDocsError("--source-revision requires graph or node inspection")
        if sum(bool(x) for x in (args.project_owner_graphs, args.inspect_python_node, args.inspect_owner_lego, args.inspect_owner_path)) > 1:
            raise ArchitectureDocsError("inspection and projection modes are mutually exclusive")
        if args.inspect_owner_lego and (not args.source_revision or args.compare_source_revision or args.python_target_source):
            raise ArchitectureDocsError("Owner LEGO inspection requires one exact SourceCut and no comparison")
        if args.compare_source_revision and not args.source_revision:
            raise ArchitectureDocsError("--compare-source-revision requires --source-revision")
        if bool(args.inspect_python_node) != bool(args.python_target_source):
            raise ArchitectureDocsError("Python inspect requires node and source together")
        if args.inspect_python_node and not args.source_revision:
            raise ArchitectureDocsError("Python inspect requires exact source revision")
        if args.inspect_owner_path:
            if not args.source_revision or args.compare_source_revision or args.python_target_source:
                raise ArchitectureDocsError("Owner path inspection requires one exact SourceCut and no comparison")
            print(json.dumps(inspect_owner_source_path(
                source_revision=args.source_revision,
                source_path=args.inspect_owner_path,
            ), sort_keys=True))
            return 0
        if args.inspect_owner_lego:
            print(json.dumps(inspect_owner_lego_contract(
                source_revision=args.source_revision, node_ref=args.inspect_owner_lego
            ), sort_keys=True))
            return 0
        if args.inspect_python_node:
            value = (
                project_node_python_import_delta(
                    before_revision=args.compare_source_revision,
                    after_revision=args.source_revision,
                    node_ref=args.inspect_python_node,
                    target_source=args.python_target_source,
                ) if args.compare_source_revision else
                project_node_python_import_syntax(
                    source_revision=args.source_revision,
                    node_ref=args.inspect_python_node,
                    target_source=args.python_target_source,
                )
            )
            print(json.dumps(value, sort_keys=True))
            return 0
        if args.project_owner_graphs:
            value = (
                project_owner_lego_source_change(
                    before_revision=args.compare_source_revision,
                    after_revision=args.source_revision,
                ) if args.compare_source_revision else
                project_owner_lego_source_graph(source_revision=args.source_revision)
            )
            if args.agent_impact:
                value = _select_agent_source_impact(value)
            print(json.dumps(value, sort_keys=True))
            return 0
        validate_repository()
    except (OSError, json.JSONDecodeError, ArchitectureDocsError) as exc:
        print(f"architecture documentation drift check failed: {exc}")
        return 2
    print("architecture documentation drift check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
