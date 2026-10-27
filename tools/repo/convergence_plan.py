#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from collections import deque
from collections.abc import Iterable
from pathlib import Path

import affected_owners

DEPENDENCY_PATH = Path(__file__).with_name("dependency_contracts.toml")


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_dependency_graph(
    owners: tuple[affected_owners.Owner, ...] = affected_owners.OWNERS,
    path: Path = DEPENDENCY_PATH,
    *, test_only_consumers: list[tuple[str, str]] | None = None,
    source_reference_consumers: list[tuple[str, str]] | None = None,
) -> dict[str, set[str]]:
    names = {owner.name for owner in owners}
    graph = {name: set() for name in names}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("dependency contract schema_version must be 1")
    if data.get("truth_role") != "repository-boundary-policy-not-domain-authority":
        raise ValueError("dependency contract truth_role must remain repository-boundary policy")
    seams = data.get("seams", [])
    if not isinstance(seams, list):
        raise ValueError("dependency contract seams must be a list")
    for index, seam in enumerate(seams):
        if not isinstance(seam, dict):
            raise ValueError(f"dependency seam {index} must be a table")
        left = seam.get("from_owner")
        right = seam.get("to_owner")
        if left not in names or right not in names:
            raise ValueError(f"dependency seam {index} references unknown owner: {left!r}->{right!r}")
        if left == right:
            raise ValueError(f"dependency seam {index} must cross owner boundaries")
        # A pinned upstream verifier is a Tool dependency, not a live
        # Runtime/Composition consumer edge. Admit only its exact declared
        # public toolchain source; other kinds retain conservative closure.
        if seam.get("kind") == "PUBLIC_PINNED_FORMAL_TOOLCHAIN":
            # A public mathematical checker is not a business owner edge.
            # Permit only literal known consumer files, never an owner-pair
            # wildcard (which could erase an actual Runtime dependency).
            approved_tool_consumers = {
                (
                    "composition", "runtime", "packages/composition/mise.toml",
                    "../../services/runtime", "services/runtime/formal/README.md",
                ),
                (
                    "harness", "runtime", "services/harness/mise.toml",
                    "../../services/runtime", "services/runtime/formal/README.md",
                ),
            }
            declared = (
                left, right, seam.get("source_glob"),
                seam.get("allowed_fragment"), seam.get("contract_ref"),
            )
            if declared not in approved_tool_consumers:
                raise ValueError("unapproved upstream toolchain-only seam")
            continue
        if seam.get("kind") == "EVIDENCE_SOURCE_REFERENCE":
            # A source citation is a *directed* source-qualification obligation
            # (provider changed -> consumer recheck). Never join the domains
            # into an undirected production/business-dependency component.
            # Admit only the one actually observed current citation.
            declared = (
                left, right, seam.get("source_glob"),
                seam.get("allowed_fragment"), seam.get("contract_ref"),
            )
            admitted = (
                "media", "lego-foundation",
                "capabilities/media/productions/fishing-fable-lego-study-r1/claims.json",
                ".agents/skills/recursive-lego-calculus/SKILL.md",
                ".agents/skills/recursive-lego-calculus/SKILL.md",
            )
            if declared != admitted:
                raise ValueError("unapproved evidence source reference")
            if source_reference_consumers is not None:
                source_reference_consumers.append((left, right))
            continue
        if seam.get("kind") == "TEST_ONLY_SOURCE_CONTRACT":
            # A Composition test reads live Runtime SourceCut bytes to construct
            # an immutable *temporary* fixture. The fixture's later immutability
            # does not erase the native test's current Runtime input dependency.
            # Keep its directed test obligation, not an undirected business edge.
            precise = (
                "composition", "runtime",
                "packages/composition/tests/test_verification_obligation_r1.py",
                "services/runtime/formal/RuntimeDispatchR1.trace-r1.json",
                "services/runtime/formal/RuntimeDispatchR1.trace-r1.json",
            )
            declared = (
                left, right, seam.get("source_glob"),
                seam.get("allowed_fragment"), seam.get("contract_ref"),
            )
            if declared != precise:
                raise ValueError("unapproved test-only source contract")
            if test_only_consumers is not None:
                test_only_consumers.append((left, right))
            continue
        if seam.get("kind") == "READ_ONLY_DOMAIN_PROFILE_CONSUMER":
            # A Gateway route has a directed Research SOURCE-CONFIGURATION
            # dependency. Requalify Gateway when Research changes; Gateway
            # edits alone cannot invalidate the independent Research owner.
            exact = (
                left, right, seam.get("source_glob"),
                seam.get("allowed_fragment"), seam.get("contract_ref"),
            )
            approved = {
                ("gateway", "research",
                 "services/gateway/src/ordivon_gateway/research_routes.py",
                 "meta/research/publication-closure-profile-r2.json",
                 "meta/research/publication-closure-profile-r2.json"),
                ("gateway", "research",
                 "services/gateway/src/ordivon_gateway/research_routes.py",
                 "meta/research/publication/perceptual-conformance-profile-r1.json",
                 "meta/research/publication/perceptual-conformance-profile-r1.json"),
            }
            if exact not in approved:
                raise ValueError("unapproved Research profile source consumer")
            if source_reference_consumers is not None:
                source_reference_consumers.append((left, right))
            continue
        if seam.get("kind") == "TEST_ONLY_DOMAIN_PROFILE_CONSUMER":
            # Artifact reads an R1 Research profile only within native tests.
            # A Research source change should qualify the Artifact test
            # consumer, without treating Artifact edits as Research runtime
            # dependencies or merging both production components.
            if (
                left != "artifact" or right != "research"
                or seam.get("source_glob")
                    != "capabilities/artifact/tests/test_artifact_publication_carrier_r1.py"
                or (
                    seam.get("allowed_fragment"), seam.get("contract_ref")
                ) not in {
                    ("meta/research/venues/fse-2027-research-r1.json",
                     "meta/research/venues/fse-2027-research-r1.json"),
                    ("meta/research/publication-closure-profile-r1.json",
                     "meta/research/publication-closure-profile-r1.json"),
                }
            ):
                raise ValueError("unapproved Research profile test-only seam")
            if test_only_consumers is not None:
                test_only_consumers.append((left, right))
            continue
        graph[left].add(right)
        graph[right].add(left)
    return graph


def connected_closure(seeds: Iterable[str], graph: dict[str, set[str]]) -> tuple[str, ...]:
    queue = deque(sorted(set(seeds)))
    seen: set[str] = set(queue)
    while queue:
        node = queue.popleft()
        for neighbor in sorted(graph[node]):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return tuple(sorted(seen))


def component_id(members: Iterable[str]) -> str:
    members = tuple(sorted(set(members)))
    return "owner-component:" + "+".join(members)


def _is_cross_cutting(paths: Iterable[str]) -> bool:
    return any(
        affected_owners._normalize(path) in affected_owners.CROSS_CUTTING_PATHS
        for path in paths
    )


def build_plan(
    *,
    base: str | None = None,
    head: str | None = None,
    changed_files: Iterable[str] = (),
    owners: tuple[affected_owners.Owner, ...] = affected_owners.OWNERS,
    dependency_path: Path = DEPENDENCY_PATH,
) -> dict[str, object]:
    explicit_paths = tuple(path for path in changed_files if path.strip())
    if explicit_paths:
        paths = explicit_paths
        base_revision = None
        head_revision = None
        head_tree = None
    else:
        if not base or not head:
            raise ValueError("base and head are required when changed_files is empty")
        base_revision = _git("rev-parse", f"{base}^{{commit}}")
        head_revision = _git("rev-parse", f"{head}^{{commit}}")
        head_tree = _git("rev-parse", f"{head_revision}^{{tree}}")
        paths = affected_owners.changed_paths(base_revision, head_revision)

    affected_owners.require_registered_execution_paths(paths, owners=owners)
    direct = affected_owners.owners_for_paths(paths, owners=owners)
    direct_names = tuple(owner.name for owner in direct)
    cross_cutting = _is_cross_cutting(paths)
    test_only_consumers: list[tuple[str, str]] = []
    source_reference_consumers: list[tuple[str, str]] = []
    graph = load_dependency_graph(
        owners=owners, path=dependency_path,
        test_only_consumers=test_only_consumers,
        source_reference_consumers=source_reference_consumers,
    )
    supplemental = tuple(sorted({
        consumer for consumer, provider in
        (*test_only_consumers, *source_reference_consumers)
        if provider in direct_names
    }))

    if cross_cutting:
        verification_names = tuple(sorted(owner.name for owner in owners))
        scope_ids = ("owner-component:ALL",)
        queue_class = "CROSS_CUTTING"
    elif direct_names:
        verification_names = tuple(sorted(set(connected_closure(direct_names, graph)) | set(supplemental)))
        scope_ids = tuple(
            sorted(
                {
                    component_id(connected_closure((name,), graph))
                    for name in direct_names
                }
            )
        )
        queue_class = "SCOPED"
    else:
        verification_names = ()
        scope_ids = ()
        queue_class = "REPOSITORY_ONLY"

    by_name = {owner.name: owner for owner in owners}
    verify_tasks = tuple(by_name[name].task for name in verification_names)
    queue_verify_tasks = tuple(by_name[name].queue_task for name in verification_names)
    declared_edges = sorted(
        {
            tuple(sorted((left, right)))
            for left, neighbors in graph.items()
            for right in neighbors
            if left != right
        }
    )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.repo-convergence-plan",
        "truthRole": "repository-convergence-projection-not-merge-or-domain-authority",
        "queueClass": queue_class,
        "baseRevision": base_revision,
        "headRevision": head_revision,
        "headTree": head_tree,
        "changedPaths": list(paths),
        "directOwners": list(direct_names),
        "verificationOwners": list(verification_names),
        "taskLocalTestConsumers": sorted({
            consumer for consumer, provider in test_only_consumers
            if provider in direct_names
        }),
        "sourceReferenceConsumers": sorted({
            consumer for consumer, provider in source_reference_consumers
            if provider in direct_names
        }),
        "verifyTasks": list(verify_tasks),
        "queueVerifyTasks": list(queue_verify_tasks),
        "scopeIds": list(scope_ids),
        "crossCutting": cross_cutting,
        "dependencyStanding": "CONSERVATIVE_UNDIRECTED_CLOSURE_OF_DECLARED_OWNER_SEAMS",
        "independenceClaim": "NOT_ESTABLISHED_BY_THIS_PROJECTION",
        "ownerManifestDigest": _digest(affected_owners.MANIFEST_PATH),
        "dependencyContractDigest": _digest(dependency_path),
        "declaredInteractionEdges": [list(edge) for edge in declared_edges],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Project one Git candidate into conservative Ordivon convergence scopes."
    )
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument(
        "--format", choices=("json", "tasks", "queue-tasks", "scopes"), default="json"
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        plan = build_plan(base=args.base, head=args.head, changed_files=args.changed_file)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.format == "tasks":
        for task in plan["verifyTasks"]:
            print(task)
    elif args.format == "queue-tasks":
        for task in plan["queueVerifyTasks"]:
            print(task)
    elif args.format == "scopes":
        for scope in plan["scopeIds"]:
            print(scope)
    else:
        print(json.dumps(plan, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
