"""Private, source-bound Gitleaks triage; not an admission gate or a scanner."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def observe(repo: Path, commit: str) -> tuple[int, dict]:
    """Return only native scan status and narrow locator fields."""
    result = {"commit": commit, "status": "unknown", "findings": []}
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        return 2, result
    try:
        def git(*args: str) -> str:
            return subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(repo), *args],
                stderr=subprocess.DEVNULL, text=True, timeout=15,
            ).strip()

        # Native ignore/config discovery is checkout-dependent. Do not equate
        # a historical object with an unrelated checkout or local policy.
        if (git("rev-parse", "--verify", f"{commit}^{{commit}}") != commit
            or git("rev-parse", "HEAD") != commit
            or Path(git("rev-parse", "--show-toplevel")).resolve() != repo.resolve()
            or git("rev-parse", "--is-shallow-repository") != "false"
            or git("status", "--porcelain", "--untracked-files=all", "--ignored",
                   "--", ".gitleaksignore", ".gitleaks.toml")
            or any(os.environ.get(key) for key in
                   ("GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML"))):
            return 2, result
        with tempfile.TemporaryDirectory(prefix="ordivon-secret-triage-") as temp:
            report = Path(temp) / "report.json"
            scan = subprocess.run(
                ["gitleaks", "git", "--no-banner", "--redact=100",
                 "--timeout", "120", "--exit-code", "17",
                 f"--log-opts={commit}", "--report-format=json",
                 f"--report-path={report}", "."],
                cwd=repo, env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=150, check=False,
            )
            if scan.returncode not in (0, 17):
                return 2, result
            rows = json.loads(report.read_text(encoding="utf-8"))
            if not isinstance(rows, list) or bool(rows) != (scan.returncode == 17):
                return 2, result
            locators = []
            for row in rows:
                rule, file, rev, line = (
                    row["RuleID"], row["File"], row["Commit"], row["StartLine"]
                )
                if (not isinstance(rule, str) or not isinstance(file, str)
                    or not isinstance(rev, str) or
                    not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", rev)
                    or type(line) is not int or line < 1):
                    return 2, result
                locators.append({"rule": rule, "file": file,
                                 "commit": rev, "line": line})
            result.update(status="findings" if locators else "clean",
                          findings=locators)
            return (1 if locators else 0), result
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        return 2, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit", help="Exact full Git commit (not a branch)")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    code, observation = observe(args.repo.resolve(), args.commit)
    print(json.dumps(observation, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
