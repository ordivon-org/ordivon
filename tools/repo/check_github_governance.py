#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import tomllib
import yaml
from affected_owners import load_owners

ROOT = Path(__file__).resolve().parents[2]
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
RUNTIME_RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "runtime-release.yml"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
CODEQL_WORKFLOW = ROOT / ".github" / "workflows" / "codeql.yml"

def tracked(pattern: str) -> tuple[str, ...]:
    # Git paths are byte sequences and may contain LF, quotes, or non-UTF-8
    # bytes. Its default human-readable quoting cannot certify file identity.
    # Use Git's native NUL-delimited representation, preserving lossless
    # filesystem byte round-tripping through Python's surrogateescape.
    output = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", pattern],
    )
    return tuple(
        part.decode("utf-8", errors="surrogateescape")
        for part in output.split(b"\0")
        if part
    )

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

def active_rooted_codeowners(source: str) -> dict[str, tuple[str, ...]]:
    """The repository's literal-root CODEOWNERS profile, not string mentions.

    GitHub treats comments as inert and the LAST matching rule as effective.
    The root-governance contract accepts only a default '*' rule first and
    later exact, rooted paths with assigned owners. A new wildcard/pattern
    grammar requires a source-bound owner test, not a guessed parser.
    """
    explicit: dict[str, tuple[str, ...]] = {}
    for lineno, line in enumerate(source.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        pattern = fields[0]
        owners = tuple(field for field in fields[1:] if not field.startswith("#"))
        if not owners or any(
            not (
                owner.startswith("@")
                and len(owner) > 1
                or "@" in owner
                and not owner.startswith("@")
            )
            for owner in owners
        ):
            raise AssertionError(f"CODEOWNERS line {lineno} has no valid owner")
        if pattern == "*":
            if explicit:
                raise AssertionError(
                    "CODEOWNERS catch-all after explicit roots overrides them"
                )
            continue
        if (
            not pattern.startswith("/")
            or any(token in pattern for token in "*?[]!\\")
            or any(
                segment in (".", "..", "") for segment in pattern.strip("/").split("/")
            )
            or pattern in explicit
        ):
            raise AssertionError(
                f"CODEOWNERS unsupported, ambiguous or duplicate root rule: {pattern}"
            )
        # A later broad root may override ownership of an earlier narrower
        # root. This existing contract forbids ambiguous explicit overlaps;
        # it does not attempt to reimplement GitHub's complete glob engine.
        if any(
            pattern.startswith(existing) or existing.startswith(pattern)
            for existing in explicit
            if existing.endswith("/")
        ):
            raise AssertionError(
                f"CODEOWNERS overlapping explicit root rule: {pattern}"
            )
        explicit[pattern] = owners
    return explicit


def validate_monorepo_codeql(source: str) -> None:
    """Ensure all three source languages get a real root-loaded CodeQL workflow."""
    workflow = yaml.safe_load(source)
    if not isinstance(workflow, dict):
        raise AssertionError("CodeQL workflow is not a YAML mapping")
    triggers = workflow.get("on", workflow.get(True))
    if not isinstance(triggers, dict):
        raise AssertionError("CodeQL is missing event triggers")
    for event in ("pull_request", "merge_group", "push", "workflow_dispatch", "schedule"):
        if event not in triggers:
            raise AssertionError(f"CodeQL missing active {event} event")
    if workflow.get("permissions", {}).get("security-events") != "write":
        raise AssertionError("CodeQL cannot upload security results")
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict) or set(jobs) != {"analyze"}:
        raise AssertionError("CodeQL requires exactly one bounded analysis job")
    job = jobs["analyze"]
    matrix = job.get("strategy", {}).get("matrix", {})
    languages = matrix.get("language")
    if not isinstance(languages, list) or set(languages) != {
        "python", "javascript-typescript", "rust"
    } or len(languages) != 3:
        raise AssertionError("CodeQL matrix lost a supported Monorepo language")
    steps = job.get("steps")
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        raise AssertionError("CodeQL missing valid steps")
    action_sha = "1c5b675653bb5c22dbe9b12b556ec555138e09fd"
    expected = {
        f"github/codeql-action/init@{action_sha}",
        f"github/codeql-action/analyze@{action_sha}",
    }
    actual = {
        step.get("uses")
        for step in steps
        if str(step.get("uses", "")).startswith("github/codeql-action/")
    }
    if actual != expected:
        raise AssertionError("CodeQL init/analyze SHA actions missing or drifting")
    init = next(step for step in steps if step.get("uses", "").endswith("/init@" + action_sha))
    analyze = next(step for step in steps if step.get("uses", "").endswith("/analyze@" + action_sha))
    matrix_value = "$" + "{{ matrix.language }}"
    if init.get("with", {}).get("languages") != matrix_value:
        raise AssertionError("CodeQL does not bind each matrix language")
    if init.get("with", {}).get("build-mode") != "none":
        raise AssertionError("CodeQL Rust extraction cannot be qualified as no-build")
    if analyze.get("with", {}).get("category") != "/language:" + matrix_value:
        raise AssertionError("CodeQL language and result category are not bound")


def main() -> int:
    validate_monorepo_codeql(CODEQL_WORKFLOW.read_text(encoding="utf-8"))
    # This verifier uses assertions for its native policy checks. Python -O removes
    # them; fail closed rather than incorrectly certifying an unchecked source tree.
    if not __debug__:
        raise RuntimeError("github governance cannot be verified under optimized Python (-O)")
    assert DEPENDABOT.is_file(), "missing root Dependabot config"
    assert WORKFLOW.is_file(), "missing root required workflow"
    assert RUNTIME_RELEASE_WORKFLOW.is_file(), "missing Runtime tagged-release workflow"
    assert CODEOWNERS.is_file(), "missing root CODEOWNERS"

    config = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))
    assert config["version"] == 2

    github_actions = update_for(config, "github-actions")
    assert configured_dirs(github_actions) == {"/"}

    # Renovate PEP 621 is the single Python manifest + uv.lock update owner.
    # Keep this check against the actual tracked consumers, not a duplicate list.
    expected_uv = dirs_for_lock("**/uv.lock", "uv.lock")
    assert not any(row.get("package-ecosystem") == "uv" for row in config["updates"]), (
        "Dependabot uv duplicates Renovate pep621 ownership"
    )
    renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
    assert "pep621" in renovate.get("enabledManagers", []), (
        "Renovate must own Python PEP 621 manifests"
    )
    assert "mise" in renovate.get("enabledManagers", []), (
        "Renovate must own Mise toolchain version manifests"
    )
    # No duplicate npm/Cargo dependency owner: those are Dependabot's job.
    assert set(renovate.get("enabledManagers", [])) == {"pep621", "mise"}, (
        "Renovate must not duplicate Dependabot npm/Cargo/Nix ownership"
    )
    assert renovate.get("lockFileMaintenance", {}).get("enabled") is True, (
        "Renovate must refresh uv.lock files"
    )
    assert renovate.get("lockFileMaintenance", {}).get("automerge", False) is False, (
        "Renovate uv.lock maintenance must not bypass consumer verification"
    )
    assert renovate.get("automerge", False) is False, (
        "Python dependency upgrades require consumer verification"
    )
    missing = sorted(
        directory for directory in expected_uv
        if not (ROOT / directory.lstrip("/") / "pyproject.toml").is_file()
    )
    assert not missing, f"uv locks without PEP 621 manifests: {missing}"

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
    assert "merge_group:" in workflow
    assert "github.event.merge_group.base_sha" in workflow
    assert "github.event.merge_group.head_sha" in workflow
    assert 'convergence_plan.py --base "$base" --head "$head"' in workflow
    assert '"verificationOwners"' in workflow
    assert '"queueVerifyTasks"' in workflow
    assert "affected_owners.py --base" not in workflow

    workflow_paths = sorted((ROOT / ".github" / "workflows").glob("*.yml")) + sorted(
        (ROOT / ".github" / "workflows").glob("*.yaml")
    )
    action_refs: list[tuple[str, str]] = []
    for workflow_path in workflow_paths:
        text = workflow_path.read_text(encoding="utf-8")
        refs = re.findall(r"^\s*-?\s*uses:\s*([^\s#]+)", text, flags=re.MULTILINE)
        action_refs.extend((workflow_path.name, ref) for ref in refs)
    # Local composite Actions can call external Actions; their transitively
    # consumed code has the same immutable source obligation as workflow steps.
    action_root = ROOT / ".github" / "actions"
    for action_path in sorted((*action_root.rglob("action.yml"), *action_root.rglob("action.yaml"))):
        action = yaml.safe_load(action_path.read_text(encoding="utf-8"))
        assert isinstance(action, dict) and isinstance(action.get("runs"), dict), (
            f"{action_path}: invalid Action metadata"
        )
        runs = action["runs"]
        if runs.get("using") != "composite":
            continue
        steps = runs.get("steps")
        assert isinstance(steps, list), f"{action_path}: composite steps must be a list"
        for step in steps:
            assert isinstance(step, dict), f"{action_path}: composite step must be a mapping"
            if "uses" in step:
                ref = step["uses"]
                assert isinstance(ref, str) and ref.strip(), (
                    f"{action_path}: composite uses must be a nonempty string"
                )
                action_refs.append((str(action_path), ref))
    assert action_refs, "root workflows have no external actions"
    floating = [
        f"{path}:{ref}"
        for path, ref in action_refs
        if not ref.startswith(("./", "$/")) and re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref) is None
    ]
    assert not floating, f"root workflows contain non-SHA action references: {floating}"
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in workflow
    # Exact upstream v5.2.2 commit (verified against the immutable GitHub tag).
    # Keep this review gate: Dependabot must not silently change action code.
    mise_action_pin = "jdx/mise-action@8418fedb1110381a0d3ba51a7a415d7c1b884550"
    assert mise_action_pin in workflow
    assert "gitleaks/gitleaks-action@" not in workflow
    assert "run: mise run repo:secrets:verify" in workflow
    assert "run: tools/repo/check_tracked_secrets.sh" in workflow
    snapshot_scan = (ROOT / "tools/repo/check_tracked_secrets.sh").read_text()
    assert "archive --format=tar" in snapshot_scan
    assert "gitleaks dir --no-banner --redact=100 --timeout 120 ." in snapshot_scan

    runtime_release = RUNTIME_RELEASE_WORKFLOW.read_text(encoding="utf-8")
    assert mise_action_pin in runtime_release
    for required in (
        'runtime-v*',
        'artifact-metadata: write',
        'attestations: write',
        'id-token: write',
        'services/runtime',
        'owner_commit',
        'ordivon-runtime-deploy prepare',
        'sourceOwnerPrefix',
        'actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6',
        'actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9',
    ):
        assert required in runtime_release, f"Runtime release workflow missing contract: {required}"

    # Keep the immutable SHA contract without freezing a historical release.
    # These are two actual SBOM consumers; newer bot versions replace only pins.
    harness_release = ROOT / "services/harness/.github/workflows/release-acceptance.yml"
    for workflow_name, workflow_source in (
        ("Runtime", runtime_release),
        ("Harness", harness_release.read_text(encoding="utf-8")),
    ):
        refs = re.findall(
            r"(?m)^\s*uses:\s*anchore/sbom-action@([0-9a-f]{40})(?=\s|$)",
            workflow_source,
        )
        assert len(refs) == 1, f"{workflow_name} must use one SHA-pinned SBOM action"
    owners = load_owners()
    # GitHub does not load CODEOWNERS files of 3 MB or more, even if every
    # textual rule is valid. Verify source bytes rather than false lexical
    # completeness over a file GitHub would ignore.
    assert CODEOWNERS.stat().st_size < 3_000_000, "CODEOWNERS exceeds GitHub 3 MB limit"
    codeowners = active_rooted_codeowners(CODEOWNERS.read_text(encoding="utf-8"))
    for owner in owners:
        root = "/" + owner.root
        assert (ROOT / owner.root).is_dir(), (
            f"owner root does not exist: {owner.name}={owner.root}"
        )
        assert root in codeowners, f"missing active CODEOWNERS boundary: {root}"

    for root in ("/.github/", "/tools/repo/", "/mise.toml"):
        assert root in codeowners, (
            f"missing active repository-mechanics CODEOWNERS boundary: {root}"
        )

    mise_path = ROOT / "mise.toml"
    mise = mise_path.read_text(encoding="utf-8")
    task_config = tomllib.loads(mise).get("task_config", {})
    assert task_config.get("cascade") is True, "root mise task config must cascade into owner configs"
    assert task_config.get("shell") == "bash -c", "root mise tasks must execute under Bash"
    assert 'gitleaks = "8.30.1"' in mise
    assert '[tasks."repo:secrets:verify"]' in mise
    assert "gitleaks git --no-banner --redact=100 --timeout 120 ." in mise
    assert "gitleaks dir --no-banner --redact=100 --timeout 120 ." in mise
    for owner in owners:
        assert f'[tasks."{owner.task}"]' in mise, (
            f"owner verify task is not exposed by root mise: {owner.name}={owner.task}"
        )
        assert f'[tasks."{owner.queue_task}"]' in mise, (
            f"owner queue task is not exposed by root mise: {owner.name}={owner.queue_task}"
        )

    print(
        "github governance: valid "
        f"(uv={len(expected_uv)}, npm={len(npm_locks)}, cargo={len(expected_cargo)})"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
