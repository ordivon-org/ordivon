#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tomllib
from collections import deque
from collections.abc import Iterable
from pathlib import Path

import affected_owners

DEPENDENCY_PATH = Path(__file__).with_name("dependency_contracts.toml")
ROOT_TASKS_PATH = Path(__file__).resolve().parents[2] / "mise.toml"


def _git(*args: str) -> str:
    proc = subprocess.run(
        # Pin SourceCut/tree identity to Git objects, not locally configured
        # replacement refs which could spoof a selected task's provenance.
        ["git", "--no-replace-objects", *args],
        # Preserve the same graft-free immutable Git SourceCut used by the
        # native affected-owner delta selector.
        env={**os.environ, "GIT_GRAFT_FILE": os.devnull},
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
    # The queue consumes the already projected source impact, not merely the
    # producer's asserted Owner list. Otherwise a consistently empty/partial
    # (verificationOwners, queueVerifyTasks) pair would pass and silently
    # skip a real Runtime consumer or a cross-cutting Owner verification.
    #
    # This compares the caller's changedPaths to the existing native
    # dependency/consumer closure. It DOES NOT prove changedPaths matches Git
    # bytes, installed effects, complete dynamic consumers or formal proof.
    if changed_paths:
        impact = build_plan(changed_files=changed_paths)
        if selected_owners != impact["verificationOwners"]:
            raise ValueError(
                "queue source impact must include the exact canonical "
                "changed-source verification consumer closure"
            )
        if requested_tasks != impact["queueVerifyTasks"]:
            raise ValueError(
                "queue source impact must include the exact canonical "
                "changed-source task closure"
            )
    if len(selected_owners) != len(set(selected_owners)):
        raise ValueError("selected verification owner identities are duplicated")
    if any(owner not in canonical for owner in selected_owners):
        raise ValueError("selected verification owner identity is unknown")
    formal_source_changed = affected_owners.requires_core_formal_verification(
        changed_paths
    )
    expected = [canonical[owner] for owner in selected_owners]
    if formal_source_changed:
        expected.append("formal:verify")
    if requested_tasks != expected:
        raise ValueError(
            "queue task selection must match canonical owner tasks plus "
            "the scoped Formal-source verification task"
        )

    # The queue invokes these exact task names through mise run.
    # Name/Owner agreement alone is not a runnable contract: the root task
    # can be removed or renamed independently of the source selector.
    # Validate the current native manifest, without interpreting task
    # shell text as mathematical behavior or running effects.
    if requested_tasks:
        try:
            declared = tomllib.loads(ROOT_TASKS_PATH.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError("selected queue tasks require readable root mise.toml") from exc
        root_tasks = declared.get("tasks")
        if not isinstance(root_tasks, dict):
            raise ValueError("selected queue tasks require a root mise task table")
        for name in requested_tasks:
            task = root_tasks.get(name)
            if isinstance(task, str):
                callable_task = bool(task.strip())
            elif isinstance(task, dict):
                callable_task = bool(task.get("run") or task.get("depends"))
            else:
                callable_task = False
            if not callable_task:
                raise ValueError(f"selected queue task has no root mise runner: {name}")
        # A nonempty TOML value cannot prove the actual runner can parse a
        # command or resolve its task dependencies. Reuse the already installed
        # native mise validator instead of reimplementing its task language.
        # Validation does not execute the task or establish its effects.
        try:
            native = subprocess.run(
                ["mise", "--cd", str(ROOT_TASKS_PATH.parent), "tasks", "validate"],
                capture_output=True, text=True, timeout=30, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("selected queue tasks require native mise task validation") from exc
        if native.returncode != 0:
            raise ValueError("selected queue tasks fail native mise task validation")


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
    formal_source_changed = affected_owners.requires_core_formal_verification(
        paths
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


def explain_source_impacts(
    plan: dict[str, object], *, source_cut: str, repo: Path | None = None,
) -> dict[str, object]:
    """Compose EXISTING SourceCut, ProblemRefs, AST hints and real queue tasks.

    This is a bounded, on-demand agent-facing *read* interface, not a new
    authority, a full call graph or permission to skip/expand verification.
    """
    import exhaustive_coverage as source_tools

    if repo is None:
        repo = Path(__file__).resolve().parents[2]
    declared_head = plan.get("headRevision")
    if declared_head is not None and source_cut != declared_head:
        raise ValueError("SourceCut mismatch with change plan headRevision")
    changed = plan.get("changedPaths")
    if not isinstance(changed, list) or len(changed) > 32:
        raise ValueError("bounded source impact requires at most 32 changed paths")
    paths = [affected_owners._normalize(path) for path in changed]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate changed source path")
    verify_owners = plan.get("verificationOwners")
    queue_tasks = plan.get("queueVerifyTasks")
    if not isinstance(verify_owners, list) or not isinstance(queue_tasks, list):
        raise ValueError("missing verification-owner/task contract")
    validate_queue_task_selection(verify_owners, queue_tasks, paths)
    # Queue allowlisting alone proves each *provided* task is legitimate,
    # not that every affected consumer was selected. Recompute the complete
    # existing native impact plan rather than trusting a caller's subset.
    # The empty set is an actual SourceCut change frontier, not an excuse
    # to omit producer/policy readset qualification. Reuse the same canonical
    # plan at the identical immutable cut instead of rejecting empty input.
    canonical = (
        build_plan(changed_files=paths) if paths
        else build_plan(base=source_cut, head=source_cut)
    )
    for name in (
        "queueClass", "directOwners", "verificationOwners", "verifyTasks",
        "queueVerifyTasks", "scopeIds", "crossCutting",
        "taskLocalTestConsumers", "dependencyStanding",
        "ownerManifestDigest", "dependencyContractDigest",
    ):
        if plan.get(name) != canonical[name]:
            raise ValueError("noncanonical source impact: changed-path verification selection")
    cut = source_tools.exact_commit(repo, source_cut)
    if cut != _git("rev-parse", "HEAD"):
        raise ValueError("SourceCut mismatch with active native verification contract")
    # Queue tasks come from working-tree TOML, while AST hints come from Git.
    # Reject the projection if either native verification policy has drifted
    # from the SAME exact Git cut, rather than mixing unrelated authorities.
    for contract in (
        affected_owners.MANIFEST_PATH,
        DEPENDENCY_PATH,
        repo / "mise.toml",
    ):
        try:
            relative = contract.relative_to(repo).as_posix()
        except ValueError as exc:
            raise ValueError("verification contract outside active Git repository") from exc
        if contract.read_bytes() != source_tools.git(repo, "show", f"{cut}:{relative}"):
            raise ValueError("verification contract differs from exact Git SourceCut")
    # Source evidence and task selection are *executed* by these concrete
    # native Python producers. Bind their on-disk bytes to the same Git cut;
    # checking only policy TOML would permit a mutable implementation to
    # issue statements about a different committed implementation.
    for relative in (
        "tools/repo/convergence_plan.py",
        "tools/repo/affected_owners.py",
        "tools/repo/exhaustive_coverage.py",
    ):
        producer = repo / relative
        if producer.is_symlink() or not producer.is_file():
            raise ValueError("executed producer source is not a regular Git file")
        if producer.read_bytes() != source_tools.git(repo, "show", f"{cut}:{relative}"):
            raise ValueError("executed producer source differs from exact Git SourceCut")
    inventory = source_tools.classification(repo, cut)
    problems = source_tools.derived_problem_legos(inventory, repo=repo)
    imports = source_tools.static_python_import_frontier(repo, cut)
    relations = source_tools.source_problem_relation_projection(problems, imports)
    indexed = {row["path"]: row for row in inventory["sourcePaths"]}
    by_provider: dict[str, list[dict[str, object]]] = {}
    for edge in relations["staticPythonImportCandidates"]:
        by_provider.setdefault(edge["providerPath"], []).append({
            "relation": edge["relation"],
            "consumerPath": edge["consumerPath"],
            "consumerCellRef": edge["consumerCellRef"],
            "consumerProblemRef": edge["consumerProblemRef"],
            "line": edge["line"],
            "syntax": edge["syntax"],
            "runtimeCallStanding": "UNKNOWN",
        })
    issue_by_cell = {
        row["sourceCellRef"]: row["problemRef"]
        for row in problems["problemLegos"]
        if row["kind"] == "RECURSIVE_SOURCE_CELL_ISSUE"
    }
    source_items: list[dict[str, object]] = []
    missing: list[str] = []
    for path in paths:
        item = indexed.get(path)
        if item is None:
            missing.append(path)
        ref = problems["sourcePathCellIndex"].get(path)
        if item is not None and ref is None:
            raise ValueError("exact Git source lacks physical source cell identity")
        source_items.append({
            "path": path,
            "sourceStanding": (
                "EXACT_GIT_SOURCE_PRESENT" if item is not None
                else "NOT_IN_SOURCE_CUT_OR_DELETED"
            ),
            "gitSourceIdentity": item["sourceIdentity"] if item else None,
            "sourceCellRef": ref,
            "sourceProblemRef": issue_by_cell.get(ref),
            "candidateConsumers": by_provider.get(path, []),
            "consumerQualification": "STATIC_PYTHON_IMPORT_HINTS_NOT_RUNTIME_CALLS",
            "installedStanding": "UNKNOWN",
            "formalRefinementStanding": "UNKNOWN",
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.self-bootstrap-source-impact-explanation",
        "sourceCut": cut,
        "sourceTree": inventory["sourceTree"],
        "sourcePathDigest": inventory["sourcePathDigest"],
        "queueClass": plan["queueClass"],
        "directOwners": plan["directOwners"],
        "verificationOwners": verify_owners,
        "queueVerifyTasks": queue_tasks,
        # R2.1 nonvacuity: an empty scoped task set is not a required
        # unexecuted task. It still cannot certify globally absent consumers.
        "verificationStanding": (
            "REQUIRED_NOT_EXECUTED_BY_PROJECTION" if queue_tasks
            else "NO_NATIVE_QUEUE_TASK_SELECTED_IN_SCOPE"
        ),
        "changedSourceInputs": source_items,
        "unindexedChangedPaths": missing,
        "staticPythonCandidateCount": sum(
            len(row["candidateConsumers"]) for row in source_items
        ),
        "nonPythonConsumerStanding": "NOT_ANALYZED",
        "runtimeCallStanding": "UNKNOWN",
        "installedEffectStanding": "UNKNOWN",
        "proofReuseAdmissible": False,
        "impactClosureAdmissible": False,
        "truthBoundary": (
            "Exact Git source and canonical existing verification task selection; "
            "Python AST imports only suggest candidate consumers. No running "
            "invocation, model-to-implementation refinement, installed effect, "
            "or reusable proof is established by this read-only projection."
        ),
    }




def build_qualified_temporal_impact(
    *, base: str, head: str, prefixes: list[str],
) -> dict[str, object]:
    """Compose existing exact Git source delta with canonical verifier policy.

    Only SOURCE/membership truth and TASK_SELECTION are asserted. It is not an
    implementation proof, runtime call graph, installed-effect certification,
    or permission to reuse stale proofs.
    """
    from source_history_legos import compact_source_impact, source_membership_delta
    import exhaustive_coverage as source

    if not prefixes or len(prefixes) > 8 or len(set(prefixes)) != len(prefixes):
        raise ValueError("temporal impact requires 1..8 distinct scoped Git prefixes")
    repo = Path(__file__).resolve().parents[2]
    current = source.exact_commit(repo, _git("rev-parse", "HEAD"))
    if head != current:
        raise ValueError("temporal impact requires exact current HEAD SourceCut")
    # Each selector has a distinct input contract; no caller-provided changed
    # path overrides these immutable Git membership observations.
    slices = []
    changed: set[str] = set()
    for prefix in prefixes:
        delta = source_membership_delta(repo, base, head, prefix)
        slices.append(compact_source_impact(delta))
        changed.update(delta["addedPaths"])
        changed.update(delta["removedPaths"])
        changed.update(delta["changedValuePaths"])
    if len(changed) > 32:
        raise ValueError("temporal impact exceeds bounded canonical source frontier")
    # R2.1 scoped-operator contract: a subset of immutable source changes
    # cannot be mistaken for a complete consumer verification obligation.
    # Reuse the already qualified native no-renames Git delta; this is a
    # bounded two-SourceCut read, NOT a repository-wide LEGO census.
    full_cut_paths = set(affected_owners.changed_paths(base, head))
    if not changed.issubset(full_cut_paths):
        raise ValueError("scoped source delta contradicts canonical exact Git changed paths")
    unseen_paths = sorted(full_cut_paths - changed)
    paths = sorted(changed)
    plan = build_plan(changed_files=paths) if paths else None
    if plan is not None:
        validate_queue_task_selection(
            plan["verificationOwners"], plan["queueVerifyTasks"], paths
        )
        # Important: the trusted canonical producer itself verifies that all
        # executable analysis and policy readsets match this exact source cut.
        explained = explain_source_impacts(plan, source_cut=head, repo=repo)
    else:
        # Zero observed changes are still a consumer of the current selector
        # and task policy. Without this branch, a dirty policy or executable
        # producer could emit a falsely empty complete queue while declaring
        # itself equivalent to the immutable Git SourceCut.
        explained = explain_source_impacts(
            build_plan(base=head, head=head), source_cut=head, repo=repo
        )
    return {
        "kind": "ordivon.phase2.temporal-source-verified-consumer-selection",
        "sourceCuts": {"previous": base, "current": head},
        "observedPrefixes": list(prefixes),
        "sourceSlices": slices,
        "selectedChangedPaths": paths,
        "plan": plan,
        "sourceConsumerEvidence": explained,
        "queueVerifyTasks": (plan["queueVerifyTasks"] if plan else []),
        "verifyTasks": (plan["verifyTasks"] if plan else []),
        "verificationStanding": (
            "SCOPE_INCOMPLETE_NO_COMPLETE_QUEUE_ADMISSION"
            if unseen_paths else "SELECTED_NOT_EXECUTED"
        ),
        "gitDeltaCoverage": {
            "observedChangedPathCount": len(paths),
            "exactChangedPathCount": len(full_cut_paths),
            "unobservedChangedPathCount": len(unseen_paths),
            "unobservedChangedPathWitness": unseen_paths[:8],
            "allTrackedGitChangesObserved": not unseen_paths,
            "standing": (
                "ONLY_NAMED_PREFIXES_UNOBSERVED_SOURCE_CHANGES"
                if unseen_paths else "EXACT_TRACKED_GIT_DELTA_OBSERVED"
            ),
        },
        "proofReuseAdmissible": False,
        "runtimeCallStanding": "UNKNOWN",
        "installedEffectStanding": "UNKNOWN",
        "completeness": "ONLY_DECLARED_PREFIXES_AND_STATIC_PYTHON_CANDIDATES",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Project one Git candidate into conservative Ordivon convergence scopes."
    )
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--impact-prefix", action="append", default=[],
                        help="opt-in immutable two-SourceCut membership frontier; no execution")
    parser.add_argument(
        "--explain-impacts", action="store_true",
        help="compose exact-Git source/ProblemRef and conservative verification tasks",
    )
    parser.add_argument(
        "--source-cut", help="exact 40-hex Git commit for read-only impact evidence"
    )
    parser.add_argument(
        "--format", choices=("json", "tasks", "queue-tasks", "scopes"), default="json"
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.impact_prefix:
            if (args.changed_file or args.explain_impacts or args.source_cut
                    or not args.base or not args.head):
                raise ValueError("temporal impact requires --base/--head and no competing change/explanation flags")
            receipt = build_qualified_temporal_impact(
                base=args.base, head=args.head, prefixes=args.impact_prefix
            )
            # Machine-readable scoped proposals remain available in JSON,
            # but never print a partial task list as the complete queue.
            if args.format != "json" and not receipt["gitDeltaCoverage"]["allTrackedGitChangesObserved"]:
                raise ValueError(
                    "unobserved Git source changes block complete queue task selection"
                )
            if args.format == "json":
                print(json.dumps(receipt, sort_keys=True))
            elif args.format in ("tasks", "queue-tasks"):
                for task in receipt["verifyTasks" if args.format == "tasks" else "queueVerifyTasks"]:
                    print(task)
            else:
                for scope in receipt["plan"]["scopeIds"] if receipt["plan"] else []:
                    print(scope)
            return 0
        plan = build_plan(base=args.base, head=args.head, changed_files=args.changed_file)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.explain_impacts:
        if args.format != "json":
            raise SystemExit("--explain-impacts requires --format json")
        cut = args.source_cut or plan["headRevision"] or _git("rev-parse", "HEAD")
        try:
            evidence = explain_source_impacts(plan, source_cut=cut)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps(evidence, sort_keys=True))
        return 0
    if args.source_cut is not None:
        raise SystemExit("--source-cut requires --explain-impacts")
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
