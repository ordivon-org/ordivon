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


def validate_queue_task_selection(
    selected_owners: list[str],
    requested_tasks: list[str],
    changed_paths: list[str] | tuple[str, ...] = (),
) -> None:
    """Fail closed on the *real* queue consumer's owner and source-task contract.

    The only source-only verification task is the existing formal:verify. It
    is never a fake Owner or a substitute for another Owner's queue gate.
    """
    canonical = {
        owner.name: owner.queue_task for owner in affected_owners.OWNERS
    }
    if len(selected_owners) != len(set(selected_owners)):
        raise ValueError("selected verification owner identities are duplicated")
    if any(owner not in canonical for owner in selected_owners):
        raise ValueError("selected verification owner identity is unknown")
    formal_source_changed = any(
        affected_owners._normalize(path).startswith("tools/formal/")
        for path in changed_paths
    )
    expected = [canonical[owner] for owner in selected_owners]
    if formal_source_changed:
        expected.append("formal:verify")
    if requested_tasks != expected:
        raise ValueError(
            "queue task selection must match canonical owner tasks plus "
            "the scoped Formal-source verification task"
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
    graph = load_dependency_graph(
        owners=owners, path=dependency_path, test_only_consumers=test_only_consumers,
    )
    supplemental = tuple(sorted({
        consumer for consumer, provider in test_only_consumers if provider in direct_names
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
    # Formal proofs live in the existing repository Tool source region, not an
    # invented domain Owner. A changed proof/checker source must still route to
    # the already declared root mise formal:verify consumer task.
    formal_source_changed = any(
        affected_owners._normalize(path).startswith("tools/formal/")
        for path in paths
    )
    formal_tasks = ("formal:verify",) if formal_source_changed else ()
    verify_tasks = (
        *(by_name[name].task for name in verification_names),
        *formal_tasks,
    )
    queue_verify_tasks = (
        *(by_name[name].queue_task for name in verification_names),
        *formal_tasks,
    )
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
        "taskLocalTestConsumers": list(supplemental),
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



def explain_source_impact(
    *,
    source_cut: str,
    changed_paths: Iterable[str],
    base_plan: dict[str, object],
    repo: Path = Path.cwd(),
) -> dict[str, object]:
    """Phase2 narrow bootstrap: exact-Git source candidates -> existing task policy.

    Reuses the canonical ProblemRef, source-cell and Python AST relation projection;
    no second registry, importer execution, proof reuse, or installed-effect claims.
    Potential caller tasks are an *additional conservative suggestion*, not a
    substitute for the mandatory queueVerifyTasks in the original plan.
    """
    import exhaustive_coverage as source  # Existing native Repo LEGO

    paths = tuple(affected_owners._normalize(path) for path in changed_paths)
    if len(paths) > 32:
        raise ValueError("bootstrap source impact requires at most 32 changed paths")
    if list(paths) != base_plan.get("changedPaths"):
        raise ValueError("bootstrap source impact requires identical plan source paths")
    try:
        source.exact_commit(repo, source_cut)
    except ValueError as exc:
        raise ValueError("source impact requires an exact available Git SourceCut") from exc
    if base_plan.get("headRevision") is not None and source_cut != base_plan["headRevision"]:
        raise ValueError("bootstrap SourceCut must equal the plan's exact Git head")
    frontier = source.derived_problem_legos(
        source.classification(repo, source_cut), repo=repo
    )
    relations = source.source_problem_relation_projection(
        frontier, source.static_python_import_frontier(repo, source_cut)
    )
    changed = set(paths)
    matched = [
        row for row in relations["staticPythonImportCandidates"]
        if row["providerPath"] in changed
    ]
    if len(matched) > 256:
        raise ValueError("bootstrap impact has more than 256 direct static witnesses")
    consumers = sorted({row["consumerPath"] for row in matched})
    # Preserve real mandatory queue semantics; do not claim an AST candidate
    # proves an additional owner must run or that other owners can be skipped.
    candidate_paths = tuple(sorted(changed | set(consumers)))
    extra_qualification_unknown = False
    try:
        candidate_plan = build_plan(changed_files=candidate_paths)
        candidate_tasks = candidate_plan["queueVerifyTasks"]
    except ValueError:
        # The caller's location is unqualified. Suppressing the new candidate
        # entirely would make a misleading complete-impact claim.
        extra_qualification_unknown = True
        candidate_tasks = base_plan["queueVerifyTasks"]
    base_tasks = base_plan["queueVerifyTasks"]
    return {
        "kind": "ordivon.phase2.source-change-static-impact-and-verifier-hints",
        "sourceCut": frontier["sourceCut"],
        "sourceTree": frontier["sourceTree"],
        "changedPaths": list(paths),
        "changedSourceUnindexedPaths": sorted(changed - set(frontier["sourcePathCellIndex"])),
        "sourceCellRefs": {
            path: frontier["sourcePathCellIndex"].get(path) for path in paths
        },
        "directStaticImportCandidates": matched,
        "directStaticCandidateConsumerPaths": consumers,
        "mandatoryQueueVerifyTasks": base_tasks,
        "candidateVerifyTasks": candidate_tasks,
        "additionalCandidateTasksNotMandatory": [
            task for task in candidate_tasks if task not in base_tasks
        ],
        "candidateTaskQualificationIncomplete": extra_qualification_unknown,
        "taskPolicySourceStanding": "CURRENT_CHECKOUT_POLICY_NOT_PINNED_BY_SOURCECUT",
        "analysisStanding": "STATIC_PYTHON_ONLY",
        "nonPythonCallCoverage": "NOT_ANALYZED",
        "dynamicConsumerClosure": "UNKNOWN",
        "runtimeCallStanding": "UNKNOWN",
        "impactClosureEstablished": False,
        "installedCurrentnessEstablished": False,
        "proofReuseAdmissible": False,
        "deletionAuthorized": False,
        "truthBoundary": (
            "Exact-Git source and Python AST import candidates plus current "
            "repository task-selection policy; no observed runtime invocation, "
            "transitive call graph, formal refinement, safe proof reuse or deployment"
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Project one Git candidate into conservative Ordivon convergence scopes."
    )
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--source-cut", help="exact immutable Git HEAD for source-impact evidence")
    parser.add_argument(
        "--explain-source-impact", action="store_true",
        help="optional Phase2 exact-Git static import and scoped verifier hints",
    )
    parser.add_argument(
        "--format", choices=("json", "tasks", "queue-tasks", "scopes"), default="json"
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        plan = build_plan(base=args.base, head=args.head, changed_files=args.changed_file)
        if args.explain_source_impact:
            if args.format != "json":
                raise ValueError("source-impact explanation requires JSON output")
            source_cut = args.source_cut or plan["headRevision"]
            if source_cut is None:
                raise ValueError("source-impact explanation requires exact --source-cut")
            plan["sourceImpact"] = explain_source_impact(
                source_cut=source_cut,
                changed_paths=plan["changedPaths"],
                base_plan=plan,
            )
        elif args.source_cut:
            raise ValueError("--source-cut requires --explain-source-impact")
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
