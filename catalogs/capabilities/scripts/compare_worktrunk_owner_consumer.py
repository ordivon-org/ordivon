#!/usr/bin/env python3
"""Scope-limited Worktrunk substitution experiment for a real Repo consumer.

Exercise Ordivon's existing tools/repo/exhaustive_coverage.py, not a new
production adapter. Candidate output is injected only through a Python mock in
a throwaway Git fixture. Production Git authority is never replaced.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.repo import exhaustive_coverage as owner

OID = re.compile(r"^[0-9a-f]{40}$")


def run(argv: list[str], env: dict[str, str]) -> str:
    proc = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=25)
    if proc.returncode:
        raise RuntimeError(f"command {argv[0]} exited {proc.returncode}: {proc.stderr[:240]}")
    return proc.stdout


def projected_porcelain(payload: dict, *, native_metadata: bytes) -> bytes:
    """Admit only in a scope Git independently proves has zero prunable entries.

    Worktrunk has no proved equivalent of Git's prunable metadata. This is a
    scoped fail-closed substitution, not a generic Git porcelain converter.
    """
    if any(row.startswith(b"prunable") for row in native_metadata.splitlines()):
        raise ValueError("native Git has prunable metadata Worktrunk cannot prove")
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("candidate has no validated list")
    paths = set()
    blocks = []
    for item in items:
        wt = item.get("worktree")
        if not isinstance(wt, dict):
            continue
        path = wt.get("path")
        if not isinstance(path, str) or not Path(path).is_absolute() or path in paths or "\n" in path:
            raise ValueError("ambiguous, missing or duplicate candidate worktree path")
        paths.add(path)
        head = item.get("head", {}).get("sha")
        if not isinstance(head, str) or not OID.fullmatch(head):
            raise ValueError("missing exact Git worktree HEAD")
        branch = item.get("branch")
        detached = wt.get("detached")
        if detached is True:
            if branch is not None:
                raise ValueError("detached candidate has branch")
            ending = "detached"
        elif isinstance(branch, str) and branch and "\n" not in branch:
            ending = "branch refs/heads/" + branch
        else:
            raise ValueError("candidate lacks an unambiguous branch/detached representation")
        blocks.append(f"worktree {path}\nHEAD {head}\n{ending}\n")
    if not blocks:
        raise ValueError("candidate contains no usable worktrees")
    return ("\n".join(blocks) + "\n").encode()


def qualify(binary: Path) -> dict:
    binary = binary.resolve(strict=True)
    binary_digest = "sha256:" + hashlib.sha256(binary.read_bytes()).hexdigest()
    source_evidence = json.loads((ROOT / "catalogs/capabilities/evidence/worktrunk-candidate-20261106.json").read_text())
    if binary_digest != source_evidence.get("source", {}).get("upstream", {}).get("releaseBinarySha256"):
        raise ValueError("Worktrunk binary digest does not match previously reviewed release")
    binary_version = run([str(binary), "--version"], dict(os.environ)).strip()
    if binary_version != "wt v0.81.0":
        raise ValueError("pinned v0.81.0 Worktrunk required")
    with tempfile.TemporaryDirectory(prefix="lep-consumer-shadow-") as directory:
        home = Path(directory).resolve()
        env = {k: v for k, v in os.environ.items()
               if k not in ("GH_TOKEN", "GITHUB_TOKEN", "GH_HOST", "SSH_AUTH_SOCK")}
        env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / "config"),
                   GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1",
                   GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", NO_COLOR="1")
        primary = home / "primary"
        external = home / "external"
        secondary = home / "external-linked"
        for repo in (primary, external):
            run(["git", "init", "-q", "-b", "main", str(repo)], env)
            run(["git", "-C", str(repo), "config", "user.name", "LEP"], env)
            run(["git", "-C", str(repo), "config", "user.email", "lep@example.invalid"], env)
            (repo / "README").write_text("fixture\n", encoding="utf-8")
            run(["git", "-C", str(repo), "add", "README"], env)
            run(["git", "-C", str(repo), "commit", "-qm", "initial"], env)
        run(["git", "-C", str(external), "worktree", "add", "-qb", "experimental", str(secondary)], env)
        primary_cut = run(["git", "-C", str(primary), "rev-parse", "HEAD"], env).strip()
        external_cut = run(["git", "-C", str(external), "rev-parse", "HEAD"], env).strip()
        query = {"repo": primary, "source": primary_cut,
                 "external_git": [f"sample={external}@{external_cut}"],
                 "non_git_data": [], "git_checkout_observations": True}
        native = owner.independent_scope_frontier(**query)
        original_git = owner.git
        native_porcelain = original_git(external, "worktree", "list", "--porcelain")
        candidate = json.loads(run([str(binary), "-C", str(external), "list", "--format", "json"], env))
        substitute = projected_porcelain(candidate, native_metadata=native_porcelain)
        if substitute != native_porcelain:
            raise AssertionError("candidate porcelain does not match independent native oracle")

        def git_shadow(repo: Path, *args: str) -> bytes:
            if Path(repo) == external and args == ("worktree", "list", "--porcelain"):
                return substitute
            return original_git(repo, *args)

        with patch.object(owner, "git", side_effect=git_shadow):
            shadow = owner.independent_scope_frontier(**query)
        consumer_parity = (shadow == native)
        # Negative 1: a forged path must be detected before consumer admission.
        tampered = json.loads(json.dumps(candidate))
        tampered["items"][0]["worktree"]["path"] += "-forged"
        forged = projected_porcelain(tampered, native_metadata=native_porcelain)
        rejected_forgery = forged != native_porcelain
        # Negative 2: native-only prunable evidence must always block substitution.
        shutil.rmtree(secondary)
        stale_native = original_git(external, "worktree", "list", "--porcelain")
        native_stale = owner.independent_scope_frontier(**query)
        stale_signalled = native_stale["summary"]["prunableWorktreeMetadataRecords"] > 0
        try:
            projected_porcelain(candidate, native_metadata=stale_native)
        except ValueError as error:
            rejected_prunable = "prunable" in str(error)
        else:
            rejected_prunable = False
        # Roll back provider substitution (unpatched owner call), no Git cleanup
        # on live owner. Temp fixture is retired by TemporaryDirectory on exit.
        shutil.rmtree(secondary, ignore_errors=True)
        recovered = owner.independent_scope_frontier(**query)
        rollback = recovered == native_stale
    positive = consumer_parity and substitute == native_porcelain
    negatives = rejected_forgery and stale_signalled and rejected_prunable
    return {
        "kind": "ordivon.external-lego-owner-consumer-shadow-r1",
        "observedAt": datetime.now(timezone.utc).isoformat(),
        "owner": "repository-governance",
        "actualConsumerPath": "tools/repo/exhaustive_coverage.py",
        "candidate": "max-sixty/worktrunk", "candidateVersion": binary_version,
        "candidateBinarySha256": binary_digest,
        "boundary": "independent disposable two-repository Git fixture; actual consumer code under mock-provided read-only Git response",
        "positive": {"nativeVsCandidateConsumerOutputEqual": consumer_parity,
                     "rawGitWorktreePorcelainIdentical": substitute == native_porcelain},
        "negative": {"forgedCandidatePathNotEqualNative": rejected_forgery,
                     "stalePrunableMetadataObservedByGit": stale_signalled,
                     "prunableCandidateBlocked": rejected_prunable},
        "rollback": {"originalConsumerRestoredAfterMock": rollback,
                     "temporaryReposRetired": True, "productionConsumerChanged": False},
        "standing": "QUALIFIED_FOR_DISPOSABLE_READ_ONLY_PROJECTION" if (positive and negatives and rollback) else "HOLD",
        "actualOwnerProductionReadback": False,
        "productionReplacementAuthorized": False,
        "retiredCustomLines": 0,
        "blockingUnknowns": ["No prunable-equivalent native Worktrunk contract",
                             "No Runtime workspace open/close/recovery/SourceCut equivalence",
                             "No actual production code path switched"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    observation = qualify(args.binary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(observation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"standing": observation["standing"], "positive": observation["positive"],
                      "negative": observation["negative"], "rollback": observation["rollback"]}))
    return 0 if observation["standing"] == "QUALIFIED_FOR_DISPOSABLE_READ_ONLY_PROJECTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
