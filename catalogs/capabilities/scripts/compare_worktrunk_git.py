#!/usr/bin/env python3
"""Bounded Worktrunk-vs-Git read-only inventory differential experiment.

Only a disposable repository is mutated. Never invokes Worktrunk remove/merge/hooks.
Produces a comparison observation, not Runtime replacement authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone


def call(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict:
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=20, check=False)
    return {"code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def git_worktrees(repo: Path, env: dict[str, str]) -> dict[str, str]:
    result = call(["git", "-C", str(repo), "worktree", "list", "--porcelain"], env=env)
    if result["code"] != 0:
        raise RuntimeError(result["stderr"])
    found: dict[str, str] = {}
    path = None
    for line in result["stdout"].splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch ") and path:
            found[line.removeprefix("branch refs/heads/")] = path
    return found


def compare(binary: Path) -> dict:
    if not binary.is_file():
        raise ValueError("exact Worktrunk binary does not exist")
    version = call([str(binary), "--version"])
    if version["code"] != 0 or version["stdout"].strip() != "wt v0.81.0":
        raise ValueError("candidate is not the pinned Worktrunk v0.81.0 executable")
    binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="ordivon-lep-wt-fixture-") as tmp:
        home = Path(tmp)
        repo = home / "main"
        worktree = home / "feature"
        env = {k: v for k, v in os.environ.items()
               if k not in ("GH_TOKEN", "GITHUB_TOKEN", "GH_HOST", "SSH_AUTH_SOCK")}
        env.update({"HOME": str(home), "XDG_CONFIG_HOME": str(home / "config"),
                    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_TERMINAL_PROMPT": "0", "NO_COLOR": "1"})
        positive = []
        negative = []
        for command in (["git", "init", "-q", "-b", "main", str(repo)],
                        ["git", "-C", str(repo), "config", "user.name", "LEP Test"],
                        ["git", "-C", str(repo), "config", "user.email", "lep@invalid.example"]):
            outcome = call(command, env=env)
            if outcome["code"] != 0:
                raise RuntimeError(outcome["stderr"])
        (repo / "README").write_text("evidence fixture\n", encoding="utf-8")
        for cmd in (["git", "-C", str(repo), "add", "README"],
                    ["git", "-C", str(repo), "commit", "-qm", "fixture"],
                    ["git", "-C", str(repo), "worktree", "add", "-qb", "experimental", str(worktree)]):
            o = call(cmd, env=env)
            if o["code"]:
                raise RuntimeError(o["stderr"])
        native = git_worktrees(repo, env)
        wt = call([str(binary), "-C", str(repo), "list", "--format", "json"], env=env)
        if wt["code"]:
            raise RuntimeError(wt["stderr"])
        payload = json.loads(wt["stdout"])
        candidate = {i["branch"]: i["worktree"]["path"] for i in payload["items"]
                     if i.get("worktree")}
        positive.append({"name": "read-only worktree inventory",
                         "passed": candidate == native,
                         "nativeBranches": sorted(native),
                         "candidateBranches": sorted(candidate)})
        (worktree / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")
        removed = call(["git", "-C", str(repo), "worktree", "remove", str(worktree)], env=env)
        wt_dirty = call([str(binary), "-C", str(repo), "list", "--format", "json"], env=env)
        dirty_items = json.loads(wt_dirty["stdout"])["items"] if wt_dirty["code"] == 0 else []
        dirty_signal = any(i.get("branch") == "experimental"
                           and i.get("worktree", {}).get("changes", {}).get("untracked") is True
                           for i in dirty_items)
        negative.append({"name": "dirty worktree cannot be removed by plain Git",
                         "passed": removed["code"] != 0 and worktree.exists(),
                         "nativeRemoveExit": removed["code"]})
        negative.append({"name": "candidate reports dirty state without invoking remove",
                         "passed": wt_dirty["code"] == 0 and dirty_signal})
        (worktree / "dirty.txt").unlink()
        cleanup = call(["git", "-C", str(repo), "worktree", "remove", str(worktree)], env=env)
        after = git_worktrees(repo, env)
        rollback = cleanup["code"] == 0 and set(after) == {"main"} and not worktree.exists()
        all_pass = all(i["passed"] for i in positive + negative) and rollback
        return {"kind": "ordivon.external-lego-comparison-r1", "observedAt": datetime.now(timezone.utc).isoformat(),
                "candidate": "max-sixty/worktrunk", "binaryVersion": "v0.81.0",
                "binarySha256": "sha256:" + binary_sha,
                "sourceBoundary": "disposable local Git fixture; no Runtime production consumer",
                "operator": "worktree inventory (read only)", "positiveControls": positive,
                "negativeControls": negative,
                "rollback": {"passed": rollback, "mechanism": "native git worktree remove after dirty file cleanup"},
                "knownNonParity": ["Worktrunk marks an arbitrary path as branch_mismatch",
                                   "No candidate create/remove/merge lifecycle parity verified",
                                   "Runtime source binding, execution evidence and recovery not tested"],
                "standing": "QUALIFIED_IN_SCOPE" if all_pass else "HOLD",
                "replacementDecision": "KEEP_NATIVE_GIT",
                "productionSwitched": False, "deletedCustomLines": 0,
                "independentConsumerReadback": False}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = compare(a.binary)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"standing": result["standing"], "positive": result["positiveControls"],
                      "negative": result["negativeControls"], "rollback": result["rollback"],
                      "output": str(a.output)}, ensure_ascii=False))
    return 0 if result["standing"] == "QUALIFIED_IN_SCOPE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
