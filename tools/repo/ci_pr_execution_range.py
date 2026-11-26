"""Bind pull-request selection to the immutable tested merge cut.

This qualifies native range identities and composes existing selector plans.
It is not a proof or artifact reuse decision.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from affected_owners import _source_git_env, changed_paths


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), *args],
        env=_source_git_env(), stderr=subprocess.PIPE, text=True, timeout=30,
    ).strip()


def _commit(repo: Path, value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value) or not value.strip("0"):
        raise ValueError("PR execution requires exact nonzero Git identities")
    if _git(repo, "rev-parse", "--verify", "--end-of-options", value + "^{commit}") != value:
        raise ValueError("PR execution coordinate is not a native commit")
    return value


def qualify(repo: Path, event_base: str, event_head: str, execution_cut: str) -> tuple[str, str]:
    """Return the actual first-parent range with immutable event identities."""
    repo = repo.resolve()
    if Path(_git(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise ValueError("PR execution requires repository root")
    if _git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("PR execution requires complete Git ancestry")
    base, head, cut = (_commit(repo, x) for x in (event_base, event_head, execution_cut))
    if _git(repo, "rev-parse", "HEAD") != cut or cut == head:
        raise ValueError("PR execution checkout mismatch")
    headers = _git(repo, "cat-file", "-p", cut).split("\n\n", 1)[0]
    parents = [line[7:] for line in headers.splitlines() if line.startswith("parent ")]
    if len(parents) != 2 or parents[1] != head:
        raise ValueError("PR execution requires ordered native merge parents")
    parent = _commit(repo, parents[0])
    # Unique original merge base is required before using the event delta.
    if len(_git(repo, "merge-base", "--all", base, head).splitlines()) != 1:
        raise ValueError("PR event merge base is ambiguous")
    if _git(repo, "merge-base", base, parent) != base:
        raise ValueError("PR execution base diverges from original event base")
    return parent, cut


def build_union(repo: Path, event_base: str, event_head: str, execution_cut: str) -> dict:
    """Compose two native plans under the currently qualified control inputs.

    Old/new uv path graph selection belongs to the existing plan producer.
    A change to the known cross-cutting selector contract across the base
    advance retains all obligations; we do not pretend to reconstruct an
    arbitrary historical Owner graph or dynamic test dependency.
    """
    import affected_owners
    import convergence_plan

    repo = repo.resolve()
    if Path.cwd().resolve() != repo or affected_owners.SOURCE_REPO_ROOT != repo:
        raise ValueError("PR union must use the active selector repository")
    parent, cut = qualify(repo, event_base, event_head, execution_cut)
    event = convergence_plan.build_plan(base=event_base, head=event_head)
    execution = convergence_plan.build_plan(base=parent, head=cut)
    paths = sorted(set(event["changedPaths"]) | set(execution["changedPaths"]))
    canonical = {o.name: o.queue_task for o in affected_owners.OWNERS}
    # The old/new uv graph is reconstructed by the native plans, but the
    # existing Owner/seam/relocation/Formal contract is the active checkout.
    # Do not project across an unqualified change in that control surface.
    drift = sorted(
        (set(changed_paths(event_base, parent, source_repo_root=repo))
         | set(changed_paths(event_head, cut, source_repo_root=repo)))
        & affected_owners.CROSS_CUTTING_PATHS
    )
    owners = sorted(canonical if drift else
                    set(event["verificationOwners"]) | set(execution["verificationOwners"]))
    tasks = [canonical[name] for name in owners]
    if drift or any("formal:verify" in plan["queueVerifyTasks"] for plan in (event, execution)):
        tasks.append("formal:verify")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.repo-pr-obligation-union",
        "truthRole": "qualified-current-selector-not-historical-proof",
        "eventPlan": event,
        "executionPlan": execution,
        "knownCrossCuttingDrift": drift,
        "selectionBasis": "ALL_ON_CONTROL_DRIFT" if drift else "TWO_NATIVE_RANGE_PLANS",
        "changedPaths": paths,
        "verificationOwners": owners,
        "queueVerifyTasks": tasks,
    }


def validate_union(repo: Path, event_base: str, event_head: str, execution_cut: str,
                   plan: dict, owners: list[str], tasks: list[str]) -> None:
    import convergence_plan

    expected = build_union(repo, event_base, event_head, execution_cut)
    if plan != expected or owners != expected["verificationOwners"] or tasks != expected["queueVerifyTasks"]:
        raise ValueError("PR queue must conserve both exact native range obligations")
    # Reuse native queue admission (including Mise's runnable task validation)
    # rather than introducing another task-language checker.
    for native in (expected["eventPlan"], expected["executionPlan"]):
        convergence_plan.validate_queue_task_selection(
            native["verificationOwners"], native["queueVerifyTasks"], native["changedPaths"],
            base=native["baseRevision"], head=native["headRevision"],
        )
    if expected["knownCrossCuttingDrift"]:
        convergence_plan.validate_queue_task_selection(owners, [t for t in tasks if t != "formal:verify"])


def main() -> int:
    try:
        base, head, cut = sys.argv[1:]
        if os.environ.get("GITHUB_SHA", cut) != cut:
            raise ValueError("provider execution SHA mismatch")
        print(json.dumps(build_union(Path.cwd(), base, head, cut), sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("ERROR: unqualified PR execution range: " + str(exc), file=sys.stderr)
        return 43


if __name__ == "__main__":
    raise SystemExit(main())
