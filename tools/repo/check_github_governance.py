#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

from affected_owners import load_owners

ROOT = Path(__file__).resolve().parents[2]
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"

def tracked(pattern: str) -> tuple[str, ...]:
    output = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", pattern],
        text=True,
    )
    return tuple(line for line in output.splitlines() if line)

def dirs_for_lock(pattern: str, filename: str) -> set[str]:
    result: set[str] = set()
    for path in tracked(pattern):
        p = Path(path)
        if p.name != filename:
            continue
        result.add("/" + p.parent.as_posix())
    return result

def update_for(config: dict, ecosystem: str) -> dict:
    matches = [
        row
        for row in config.get("updates", [])
        if row.get("package-ecosystem") == ecosystem
    ]
    if len(matches) != 1:
        raise AssertionError(f"{ecosystem}: expected exactly one root update entry, got {len(matches)}")
    return matches[0]

def configured_dirs(row: dict) -> set[str]:
    if "directories" in row:
        return set(row["directories"])
    if "directory" in row:
        return {row["directory"]}
    return set()

def main() -> int:
    assert DEPENDABOT.is_file(), "missing root Dependabot config"
    assert WORKFLOW.is_file(), "missing root required workflow"
    assert CODEOWNERS.is_file(), "missing root CODEOWNERS"

    config = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))
    assert config["version"] == 2

    github_actions = update_for(config, "github-actions")
    assert configured_dirs(github_actions) == {"/"}

    expected_uv = dirs_for_lock("**/uv.lock", "uv.lock")
    actual_uv = configured_dirs(update_for(config, "uv"))
    assert actual_uv == expected_uv, f"uv directories drift: expected={sorted(expected_uv)} actual={sorted(actual_uv)}"

    npm_locks: set[str] = set()
    for pattern, name in (
        ("**/pnpm-lock.yaml", "pnpm-lock.yaml"),
        ("**/package-lock.json", "package-lock.json"),
        ("**/npm-shrinkwrap.json", "npm-shrinkwrap.json"),
    ):
        npm_locks |= dirs_for_lock(pattern, name)
    actual_npm = configured_dirs(update_for(config, "npm"))
    assert actual_npm == npm_locks, f"npm directories drift: expected={sorted(npm_locks)} actual={sorted(actual_npm)}"

    expected_cargo = dirs_for_lock("**/Cargo.lock", "Cargo.lock")
    actual_cargo = configured_dirs(update_for(config, "cargo"))
    assert actual_cargo == expected_cargo, f"cargo directories drift: expected={sorted(expected_cargo)} actual={sorted(actual_cargo)}"

    nested = [
        path
        for path in tracked("**/.github/dependabot.yml")
        if path != ".github/dependabot.yml"
    ]
    assert not nested, f"nested Dependabot configs are not active monorepo authority: {nested}"

    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "name: root-verification" in workflow
    assert "paths:" not in workflow

    action_refs = re.findall(r"^\s*-?\s*uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE)
    assert action_refs, "root workflow has no external actions"
    floating = [
        ref
        for ref in action_refs
        if not ref.startswith("./") and re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref) is None
    ]
    assert not floating, f"root workflow contains non-SHA action references: {floating}"
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in workflow
    assert "jdx/mise-action@9e7f7633ff6f6d6048a9418a68d48f288f50eb14" in workflow
    assert "gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e" in workflow

    owners = load_owners()
    codeowners = CODEOWNERS.read_text(encoding="utf-8")
    for owner in owners:
        root = "/" + owner.root
        assert (ROOT / owner.root).is_dir(), f"owner root does not exist: {owner.name}={owner.root}"
        assert root in codeowners, f"missing CODEOWNERS boundary: {root}"

    for root in ("/.github/", "/tools/repo/", "/mise.toml"):
        assert root in codeowners, f"missing repository-mechanics CODEOWNERS boundary: {root}"

    mise = (ROOT / "mise.toml").read_text(encoding="utf-8")
    for owner in owners:
        assert f'[tasks."{owner.task}"]' in mise, (
            f"owner verify task is not exposed by root mise: {owner.name}={owner.task}"
        )

    print(
        "github governance: valid "
        f"(uv={len(expected_uv)}, npm={len(npm_locks)}, cargo={len(expected_cargo)})"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
