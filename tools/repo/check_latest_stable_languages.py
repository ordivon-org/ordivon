#!/usr/bin/env python3
"""Enforce official stable language/toolchain currency; never self-approve exceptions."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "tools/repo/latest_stable_languages.json"
OFFICIAL_RELEASE_HOSTS = {
    "python": "www.python.org", "rust": "blog.rust-lang.org",
    "node": "nodejs.org", "godot": "godotengine.org",
    "typescript": "github.com", "opa": "github.com", "uv": "github.com", "uv-build": "github.com",
    "powershell": "github.com", "bash": "ftp.gnu.org", "sqlite": "www.sqlite.org",
    "postgresql": "www.postgresql.org", "osquery": "github.com",
}
OFFICIAL_RELEASE_PREFIXES = {
    "typescript": "/microsoft/TypeScript/releases/",
    "uv": "/astral-sh/uv/releases/", "uv-build": "/astral-sh/uv/releases/",
    "opa": "/open-policy-agent/opa/releases/",
    "powershell": "/PowerShell/PowerShell/releases/",
    "bash": "/gnu/bash/",
    "osquery": "/osquery/osquery/releases/",
}
LANGUAGE_EXTENSIONS = {
    ".py": "python", ".rs": "rust", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".mjs": "javascript", ".gd": "gdscript",
    ".sh": "shell", ".ps1": "powershell", ".rego": "rego", ".sql": "sql",
}


def tracked_paths(root: Path) -> list[str]:
    return subprocess.check_output(["git", "-C", str(root), "ls-files"], text=True).splitlines()


def pin_rows(root: Path, tracked: list[str]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for path in tracked:
        source = root / path
        if not source.is_file():
            continue
        name = source.name
        if name == "mise.toml":
            tools = tomllib.loads(source.read_text(encoding="utf-8")).get("tools", {})
            for language in ("python", "rust", "node", "godot", "opa", "powershell", "uv"):
                pin = tools.get(language)
                if isinstance(pin, dict):
                    pin = pin.get("version")
                if isinstance(pin, str):
                    rows.append((path, language, pin))
        elif name == "pyproject.toml":
            project = tomllib.loads(source.read_text(encoding="utf-8")).get("project", {})
            required = project.get("requires-python")
            if required:
                rows.append((path + "#project.requires-python", "python", str(required)))
            pkg = tomllib.loads(source.read_text(encoding="utf-8"))
            for build in pkg.get("build-system", {}).get("requires", []):
                if isinstance(build, str) and build.startswith("uv_build"):
                    rows.append((path + "#build-system.uv-build", "uv-build", build[len("uv_build"):]))
            required_uv = pkg.get("tool", {}).get("uv", {}).get("required-version")
            if required_uv:
                rows.append((path + "#tool.uv.required-version", "uv", str(required_uv)))
            ruff_target = pkg.get("tool", {}).get("ruff", {}).get("target-version")
            if ruff_target:
                rows.append((path + "#tool.ruff.target-version", "python", str(ruff_target)))
        elif name == ".python-version":
            rows.append((path, "python", source.read_text(encoding="utf-8").strip()))
        elif name == "rust-toolchain.toml":
            toolchain = tomllib.loads(source.read_text(encoding="utf-8"))["toolchain"]
            rows.append((path, "rust", str(toolchain["channel"])))
        elif source.suffix == ".toml":
            # Owner/provider configuration often has an independent interpreter
            # selector which silently survives the project mise version update.
            data = tomllib.loads(source.read_text(encoding="utf-8"))
            def walk(value: object, prefix: str = "") -> None:
                if isinstance(value, dict):
                    for key, item in value.items():
                        dotted = f"{prefix}.{key}" if prefix else key
                        if key in {"python_version", "mcp_python_version", "uv_version"} and isinstance(item, str):
                            tool = "uv" if key == "uv_version" else "python"
                            rows.append((path + "#" + dotted, tool, item))
                        elif isinstance(item, dict):
                            walk(item, dotted)
            walk(data)
        elif name == "package.json":
            package = json.loads(source.read_text(encoding="utf-8"))
            engine = package.get("engines", {}).get("node")
            if engine:
                rows.append((path + "#engines.node", "node", str(engine)))
            # TypeScript is a compiler/runtime contract, not a Node engine.
            ts = package.get("devDependencies", {}).get("typescript") or package.get("dependencies", {}).get("typescript")
            if ts:
                rows.append((path + "#typescript", "typescript", str(ts)))
    return rows


def is_exact_stable(value: str, target: str, *, path: str, language: str) -> bool:
    if value == target:
        return True
    if language == "godot" and value == target + "-stable":
        return True
    if path.endswith("#build-system.uv-build"):
        bits = target.split(".")
        higher = f"{bits[0]}.{int(bits[1])+1}.0"
        return value == f">={target},<{higher}"
    if path.endswith("#tool.uv.required-version"):
        return value == f"=={target}"
    if path.endswith("#tool.ruff.target-version"):
        bits = target.split(".")
        return value == f"py{bits[0]}{bits[1]}"
    if path.endswith("#project.requires-python"):
        # Package metadata is a compatibility range; an owner-local mise/
        # .python-version entry is still required to select exact runtime.
        minor = target.split(".")
        upper = f"{minor[0]}.{int(minor[1])+1}"
        return value in {f"=={target}", f">={target},<{upper}"}
    if path.endswith("#engines.node"):
        major = target.split(".")[0]
        return value in {f">={target} <{int(major)+1}", f">={target}"}
    return False


def bash_source_carriers(root: Path, tracked: list[str]) -> list[str]:
    """Find tracked *.sh AND extensionless executable Bash/POSIX-sh scripts."""
    found: list[str] = []
    for name in tracked:
        path = root / name
        if not path.is_file() or path.is_symlink():
            continue
        if path.suffix == ".sh":
            found.append(name)
            continue
        if path.suffix:
            continue
        try:
            with path.open("rb") as handle:
                shebang = handle.readline(240)
        except OSError:
            continue
        if shebang.startswith(b"#!") and (
            b"bash" in shebang or shebang.rstrip().endswith(b"/sh")
        ):
            found.append(name)
    return found


def bash_gate(root: Path, tracked: list[str], required: str) -> tuple[list[str], str]:
    """No testing an arbitrary pre-existing image as though it were accepted."""
    names = bash_source_carriers(root, tracked)
    if not names:
        return [], "shell scripts: none"
    issues: list[str] = []
    try:
        version = subprocess.run(["bash", "--version"], text=True, capture_output=True, timeout=5, check=True).stdout
        match = re.search(r"GNU bash, version ([0-9.]+)", version)
        observed = match.group(1) if match else "UNKNOWN"
        if observed != required:
            issues.append(f"Bash executable {observed} != official latest stable {required}")
    except (OSError, subprocess.SubprocessError):
        observed = "UNAVAILABLE"
        issues.append("Bash executable unavailable for acceptance")
    for name in names:
        with (root / name).open("rb") as source:
            first = source.readline(240).decode("utf-8", "replace").strip()
        if not (
            first.startswith("#!/bin/bash")
            or first.startswith("#!/usr/bin/env bash")
        ):
            issues.append(f"{name}: interpreter requires separate mapping: {first[:70]}")
            continue
        result = subprocess.run(
            ["bash", "-n", name], cwd=root, text=True, capture_output=True, timeout=8, check=False
        )
        if result.returncode:
            issues.append(f"{name}: bash -n syntax failed: {result.stderr[:140]}")
    try:
        checked = subprocess.run(
            ["shellcheck", "-S", "error", *names],
            cwd=root, text=True, capture_output=True, timeout=60, check=False,
        )
        if checked.returncode:
            issues.append(f"ShellCheck error gate failed: {checked.stdout[:500]} {checked.stderr[:120]}")
    except (OSError, subprocess.SubprocessError):
        issues.append("ShellCheck unavailable or timed out; no compliance claim")
    return issues, f"bash source carriers: {len(names)}; Bash version {observed}; syntax and ShellCheck error-level gated"


def valid_exception(entry: dict, *, today: dt.date) -> tuple[bool, str]:
    required = {
        "path", "language", "currentVersion", "targetVersion", "humanDecisionRef",
        "approvedBy", "approvalPr", "approvedOn", "expiresOn", "reproduction",
        "failureEvidence", "exitCriteria",
    }
    if not isinstance(entry, dict) or not required.issubset(entry):
        return False, "missing mandatory human-approval / reproduction / expiry fields"
    if not all(isinstance(entry[k], str) and entry[k].strip() for k in required):
        return False, "empty exception fields"
    if not entry["humanDecisionRef"].startswith("human-decision:"):
        return False, "missing canonical human-decision"
    if not re.fullmatch(r"https://github\.com/ordivon-org/ordivon/pull/[1-9][0-9]*", entry["approvalPr"]):
        return False, "approval evidence must be an exact repository PR"
    try:
        approved = dt.date.fromisoformat(entry["approvedOn"])
        expires = dt.date.fromisoformat(entry["expiresOn"])
    except ValueError:
        return False, "invalid approval date"
    if approved > today or expires < today or (expires - approved).days > 14:
        return False, "approval not current or exceeds 14-day ceiling"
    # A claimed string alone cannot prove human authorization. Until native
    # Human-decision verification or GitHub review authentication is wired,
    # exception requests are reported but never bypass strict enforcement.
    return False, "human approval requires independently verified authority (no self-certification)"


def check(root: Path, *, today: dt.date) -> tuple[list[str], list[str], dict]:
    baseline = json.loads((root / "tools/repo/latest_stable_languages.json").read_text(encoding="utf-8"))
    issues: list[str] = []
    facts: list[str] = []
    observed = dt.date.fromisoformat(baseline["observedOn"])
    valid_days = baseline["validForDays"]
    if not isinstance(valid_days, int) or not 1 <= valid_days <= 7:
        issues.append("baseline expiry must be within 1-7 days")
    if observed > today or (today - observed).days > valid_days:
        issues.append(f"official stable-version evidence is stale: {observed} (max {valid_days} days)")
    targets = baseline["targets"]
    if not set(("python", "rust", "node", "typescript", "godot", "opa", "powershell", "uv", "uv-build", "bash")).issubset(targets):
        issues.append("language baselines incomplete")
    for language, item in targets.items():
        release = urlparse(item.get("officialRelease", ""))
        if (
            not item.get("version")
            or release.scheme != "https"
            or release.hostname != OFFICIAL_RELEASE_HOSTS.get(language)
            or not release.path.startswith(OFFICIAL_RELEASE_PREFIXES.get(language, "/"))
        ):
            issues.append(f"{language}: no trusted official release evidence")
    tracked = tracked_paths(root)
    rows = pin_rows(root, tracked)
    exceptions = baseline.get("exceptions", [])
    if not isinstance(exceptions, list):
        issues.append("exceptions must be a list")
        exceptions = []
    for exception in exceptions:
        ok, reason = valid_exception(exception, today=today)
        if not ok:
            issues.append(f"UNAPPROVED EXCEPTION {exception.get('path', '?')}: {reason}")
    stale = 0
    for path, language, version in rows:
        official = targets.get(language)
        if not official:
            issues.append(f"{path}: unknown language pin {language}={version}")
            continue
        target = official["version"]
        if not is_exact_stable(version, target, path=path, language=language):
            stale += 1
            issues.append(f"{path}: {language}={version} is not latest stable {target} (no verified exception)")
    # Other real language carriers are not silently certified merely because
    # they have no mise pin: they need a language/engine mapping and proof.
    source_languages = {LANGUAGE_EXTENSIONS.get(Path(p).suffix) for p in tracked}
    if "gdscript" in source_languages and not any(lang == "godot" for _, lang, _ in rows):
        issues.append("domains/game: GDScript code has no accepted Godot engine toolchain pin")
    if "powershell" in source_languages and not any(lang == "powershell" for _, lang, _ in rows):
        issues.append("PowerShell code has no version-pinned toolchain")
    if "rego" in source_languages and not any(lang == "opa" for _, lang, _ in rows):
        issues.append("Rego code has no version-pinned OPA toolchain")
    shell_issues, shell_facts = bash_gate(root, tracked, targets["bash"]["version"])
    issues.extend(shell_issues)
    facts.append(shell_facts)
    if "sql" in source_languages:
        facts.append("SQL dialect acceptance is delegated to the mandatory separate repo:sql:verify gate; not certified by this checker.")
    counts = Counter(LANGUAGE_EXTENSIONS.get(Path(p).suffix, "") for p in tracked)
    counts.pop("", None)
    facts.append("official stable versions: " + ", ".join(f"{k}={v['version']}" for k, v in targets.items()))
    facts.append(f"tracked language pin declarations: {len(rows)}; non-current: {stale}")
    facts.append(f"tracked code files by language: {dict(sorted(counts.items()))}")
    facts.append("Source pin equality is only configuration evidence; native owner + live interpreter/dialect acceptance is separate.")
    return issues, facts, baseline


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true", help="report without claiming compliance")
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    args = parser.parse_args()
    issues, facts, _ = check(ROOT, today=args.today)
    print("\n".join(facts))
    for issue in issues:
        print("NONCOMPLIANT " + issue)
    print(f"latest-stable findings: {len(issues)}; status={'NONCOMPLIANT' if issues else 'PASS'}")
    return 0 if args.audit or not issues else 1


if __name__ == "__main__":
    sys.exit(main())
