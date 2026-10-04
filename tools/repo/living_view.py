#!/usr/bin/env python3
"""Build a rebuildable Ordivon Living Recursive LEGO view from natural-owner projections.

This compiler owns no Git, Runtime, Host, Gateway, provider, security, or domain truth.
It composes exact source identity, the existing conservative convergence projection, and
caller-supplied owner observations without collapsing those truth layers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import affected_owners
import convergence_plan
import information_census

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION_PATH = ROOT / "docs/architecture/architecture-constitution-r1.json"

OBSERVATION_KIND = "ordivon.living-owner-observation"


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _file_digest(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _current_head(revision: str) -> tuple[str, str]:
    resolved = _git("rev-parse", f"{revision}^{{commit}}")
    head = _git("rev-parse", "HEAD^{commit}")
    if resolved != head:
        raise ValueError(
            "living source view must be built from the exact checked-out HEAD; "
            "checkout the requested revision first"
        )
    return resolved, _git("show", "-s", "--format=%T", resolved)


def _declared_edges(graph: dict[str, set[str]]) -> list[list[str]]:
    return [
        [left, right]
        for left, right in sorted(
            {
                tuple(sorted((left, right)))
                for left, neighbors in graph.items()
                for right in neighbors
                if left != right
            }
        )
    ]


def _components(graph: dict[str, set[str]]) -> list[list[str]]:
    remaining = set(graph)
    result: list[list[str]] = []
    while remaining:
        start = min(remaining)
        component = set(convergence_plan.connected_closure((start,), graph))
        result.append(sorted(component))
        remaining -= component
    return sorted(result, key=lambda row: tuple(row))


def _surface_manifests() -> list[dict[str, object]]:
    raw = _git("ls-files", "--", "*mcp-surface.json")
    paths = [Path(line) for line in raw.splitlines() if line]
    rows: list[dict[str, object]] = []
    for relative in sorted(paths, key=lambda path: path.as_posix()):
        absolute = ROOT / relative
        payload = json.loads(absolute.read_text(encoding="utf-8"))
        tools = payload.get("tools")
        declared_count: int | None
        if isinstance(tools, list):
            declared_count = len(tools)
        else:
            candidate = payload.get("declaredToolCount")
            declared_count = candidate if type(candidate) is int else None
        rows.append(
            {
                "path": relative.as_posix(),
                "digest": _file_digest(absolute),
                "packageVersion": payload.get("packageVersion"),
                "surfaceEpoch": payload.get("surfaceEpoch"),
                "declaredToolCount": declared_count,
            }
        )
    return rows


def build_source_view(revision: str = "HEAD") -> dict[str, object]:
    source_revision, source_tree = _current_head(revision)
    constitution = json.loads(CONSTITUTION_PATH.read_text(encoding="utf-8"))
    owners = tuple(affected_owners.OWNERS)
    graph = convergence_plan.load_dependency_graph(owners=owners)

    owner_rows = [
        {
            "ownerRef": owner.name,
            "root": owner.root,
            "verifyTask": owner.task,
            "queueVerifyTask": owner.queue_task,
        }
        for owner in owners
    ]

    body: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.living-source-view",
        "truthRole": "rebuildable-source-projection-not-live-or-domain-authority",
        "sourceRevision": source_revision,
        "sourceTree": source_tree,
        "architectureConstitution": {
            "path": CONSTITUTION_PATH.relative_to(ROOT).as_posix(),
            "digest": _file_digest(CONSTITUTION_PATH),
            "minimalSemanticKernel": constitution.get("minimalSemanticKernel", []),
            "conditionalKernelExtensions": constitution.get(
                "conditionalKernelExtensions", []
            ),
            "substrateOwners": constitution.get("substrateOwners", {}),
            "laws": constitution.get("laws", []),
        },
        "repositoryOwnerGraph": {
            "truthRole": "repository-mechanics-only-not-domain-authority",
            "ownerManifestDigest": _file_digest(affected_owners.MANIFEST_PATH),
            "dependencyContractDigest": _file_digest(convergence_plan.DEPENDENCY_PATH),
            "owners": owner_rows,
            "declaredInteractionEdges": _declared_edges(graph),
            "conservativeUndirectedComponents": _components(graph),
            "independenceClaim": "NOT_ESTABLISHED_BY_THIS_PROJECTION",
        },
        "sourceSurfaces": _surface_manifests(),
        "informationCoverage": information_census.build_information_summary(
            source_revision
        ),
        "nonClaims": [
            "Repository owner components are not the full Ordivon ontology.",
            "A source manifest does not establish deployed or live state.",
            "A declared dependency edge does not transfer truth ownership.",
            "Absence of a declared edge does not establish semantic independence.",
            "Information coverage is bounded source/reference projection, not semantic completeness or a universal object ontology.",
        ],
    }
    body["viewDigest"] = canonical_digest(body)
    return body


def _path_owner_classification(
    paths: Iterable[str],
) -> tuple[dict[str, list[str]], list[str], list[str]]:
    by_owner: dict[str, list[str]] = {
        owner.name: [] for owner in affected_owners.OWNERS
    }
    cross_cutting: list[str] = []
    unowned: list[str] = []
    for raw in paths:
        path = affected_owners._normalize(raw)
        if path in affected_owners.CROSS_CUTTING_PATHS:
            cross_cutting.append(path)
            continue
        owners = affected_owners.owners_for_paths((path,))
        if owners:
            for owner in owners:
                by_owner[owner.name].append(path)
        else:
            unowned.append(path)
    return (
        {name: sorted(values) for name, values in by_owner.items() if values},
        sorted(cross_cutting),
        sorted(unowned),
    )


def build_delta_view(base: str, head: str = "HEAD") -> dict[str, object]:
    head_revision, _ = _current_head(head)
    plan = convergence_plan.build_plan(base=base, head=head_revision)
    by_owner, cross_cutting_paths, unowned_paths = _path_owner_classification(
        plan["changedPaths"]
    )
    all_owner_refs = [owner.name for owner in affected_owners.OWNERS]

    if plan["crossCutting"]:
        invalidated = all_owner_refs
        preserved: list[str] = []
        standing = "CROSS_CUTTING_SOURCE_REBUILD_ALL"
    else:
        invalidated = list(plan["directOwners"])
        preserved = sorted(set(all_owner_refs) - set(invalidated))
        if invalidated and unowned_paths:
            standing = "SCOPED_SOURCE_REBUILD_WITH_UNCLASSIFIED_PATHS"
        elif invalidated:
            standing = "SCOPED_SOURCE_REBUILD"
        elif unowned_paths:
            standing = "UNCLASSIFIED_REPOSITORY_DELTA"
        else:
            standing = "NO_DELTA"

    body: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.living-delta-view",
        "truthRole": "rebuildable-delta-and-invalidation-projection-not-semantic-authority",
        "baseRevision": plan["baseRevision"],
        "headRevision": plan["headRevision"],
        "headTree": plan["headTree"],
        "changedPaths": plan["changedPaths"],
        "ownerLocalChangedPaths": by_owner,
        "crossCuttingChangedPaths": cross_cutting_paths,
        "unclassifiedChangedPaths": unowned_paths,
        "sourceInvalidation": {
            "ownerRefs": invalidated,
            "preservedOwnerRefs": preserved,
            "standing": standing,
            "minimalityClaim": "NOT_ESTABLISHED_CONSERVATIVE_REPOSITORY_PROJECTION",
        },
        "verificationRequalification": {
            "ownerRefs": plan["verificationOwners"],
            "verifyTasks": plan["verifyTasks"],
            "queueVerifyTasks": plan["queueVerifyTasks"],
            "scopeIds": plan["scopeIds"],
            "dependencyStanding": plan["dependencyStanding"],
        },
        "declaredInteractionEdges": plan["declaredInteractionEdges"],
        "ownerManifestDigest": plan["ownerManifestDigest"],
        "dependencyContractDigest": plan["dependencyContractDigest"],
        "nonClaims": [
            "Unclassified changed paths are not silently attributed to a repository owner.",
            "Verification closure is conservative and does not prove minimal semantic invalidation.",
            "A delta does not establish whether a changed implementation is a regression, successor, or semantic supersession.",
        ],
    }
    body["viewDigest"] = canonical_digest(body)
    return body


def validate_observation(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("owner observation must be a JSON object")
    required = {
        "schemaVersion",
        "kind",
        "subjectRef",
        "ownerRef",
        "observedAt",
        "operation",
        "standing",
        "evidenceRefs",
        "attributes",
    }
    optional = {"sourceRevision", "sourceDigest", "truthBoundary"}
    unknown = set(value) - required - optional
    missing = required - set(value)
    if missing or unknown:
        raise ValueError(
            f"owner observation fields differ: missing={sorted(missing)} unknown={sorted(unknown)}"
        )
    if value["schemaVersion"] != 1 or value["kind"] != OBSERVATION_KIND:
        raise ValueError("unsupported owner observation identity")
    for field in ("subjectRef", "ownerRef", "observedAt", "operation", "standing"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError(f"owner observation {field} must be non-empty text")
    if not isinstance(value["evidenceRefs"], list) or any(
        not isinstance(item, str) or not item for item in value["evidenceRefs"]
    ):
        raise ValueError("owner observation evidenceRefs must be a string array")
    if not isinstance(value["attributes"], dict):
        raise TypeError("owner observation attributes must be an object")
    if (
        "sourceRevision" in value
        and value["sourceRevision"] is not None
        and (
            not isinstance(value["sourceRevision"], str) or not value["sourceRevision"]
        )
    ):
        raise ValueError("owner observation sourceRevision must be text or null")
    if "sourceDigest" in value and value["sourceDigest"] is not None:
        candidate = value["sourceDigest"]
        if (
            not isinstance(candidate, str)
            or len(candidate) != 71
            or not candidate.startswith("sha256:")
        ):
            raise ValueError(
                "owner observation sourceDigest must be sha256:<64 hex> or null"
            )
    return dict(value)


def load_observations(paths: Iterable[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows.extend(validate_observation(item) for item in payload)
        else:
            rows.append(validate_observation(payload))
    return sorted(
        rows,
        key=lambda row: (
            str(row["ownerRef"]),
            str(row["subjectRef"]),
            str(row["observedAt"]),
            canonical_digest(row),
        ),
    )


def build_qualified_view(
    source: dict[str, object],
    *,
    delta: dict[str, object] | None = None,
    observations: Iterable[dict[str, object]] = (),
    required_observation_owners: Iterable[str] = (),
) -> dict[str, object]:
    rows = [validate_observation(row) for row in observations]
    rows = sorted(
        rows,
        key=lambda row: (
            str(row["ownerRef"]),
            str(row["subjectRef"]),
            str(row["observedAt"]),
            canonical_digest(row),
        ),
    )
    observed_owners = {str(row["ownerRef"]) for row in rows}
    required = sorted(set(required_observation_owners))
    currentness = [
        {
            "ownerRef": owner,
            "standing": "OBSERVED" if owner in observed_owners else "UNKNOWN",
        }
        for owner in required
    ]

    source_revision = str(source["sourceRevision"])
    rendered_observations: list[dict[str, object]] = []
    for row in rows:
        observed_source = row.get("sourceRevision")
        if observed_source is None:
            relation = "UNBOUND"
        elif observed_source == source_revision:
            relation = "EXACT_SOURCE_REVISION"
        else:
            relation = "DIFFERENT_SOURCE_REVISION_NO_SEMANTIC_INFERENCE"
        rendered = dict(row)
        rendered["observationDigest"] = canonical_digest(row)
        rendered["sourceBindingRelation"] = relation
        rendered_observations.append(rendered)

    body: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.living-recursive-lego-view",
        "truthRole": "qualified-multi-view-projection-not-natural-owner-authority",
        "sourceView": source,
        "deltaView": delta,
        "ownerObservations": rendered_observations,
        "requiredObservationCurrentness": currentness,
        "unknownRequiredOwners": [
            row["ownerRef"] for row in currentness if row["standing"] == "UNKNOWN"
        ],
        "compositionLaw": (
            "Source, live-owner observations, verification evidence, and domain verdicts "
            "remain separate facets. This projection never lets one facet overwrite another."
        ),
        "nonClaims": [
            "OBSERVED means an owner-qualified observation was supplied, not that the owner is healthy.",
            "UNKNOWN is preserved when a required owner observation is absent.",
            "A different observed source revision is descriptive only; no regression/supersession inference is made.",
            "This view grants no execution, merge, security, workflow, or domain authority.",
        ],
    }
    body["viewDigest"] = canonical_digest(body)
    return body


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an Ordivon Living Recursive LEGO projection for the exact checkout."
    )
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--base")
    parser.add_argument("--observation", action="append", default=[], type=Path)
    parser.add_argument("--require-observation-owner", action="append", default=[])
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        source = build_source_view(args.revision)
        delta = build_delta_view(args.base, args.revision) if args.base else None
        observations = load_observations(args.observation)
        result = build_qualified_view(
            source,
            delta=delta,
            observations=observations,
            required_observation_owners=args.require_observation_owner,
        )
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        raise SystemExit(str(exc)) from exc

    encoded = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
