#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "meta/next/fixtures/career"
CAREER_OPS_VERSION = "1.38.0"
CAREER_OPS_RELEASE_GIT_HEAD = "115bc9873e3d43e23883f3c8f16436617facc62c"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], *, cwd: Path, env: dict[str, str], timeout: int, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if check and cp.returncode != 0:
        raise RuntimeError(
            f"command failed ({cp.returncode}): {cmd!r}\nstdout:\n{cp.stdout}\nstderr:\n{cp.stderr}"
        )
    return cp


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay the narrow provider-native Career qualification used for admission."
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    jd_fixture = FIXTURES / "career-ops-synthetic-jd.md"
    cv_fixture = FIXTURES / "career-ops-synthetic-cv.md"
    env = os.environ.copy()
    env["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"
    env["CI"] = "1"

    with tempfile.TemporaryDirectory(prefix="ordivon-career-provider-replay-") as tmp:
        tmp_path = Path(tmp)
        checkout = tmp_path / "career-ops"
        init = run(
            ["npx", "--yes", f"@santifer/career-ops@{CAREER_OPS_VERSION}", "init", str(checkout)],
            cwd=tmp_path,
            env=env,
            timeout=args.timeout,
        )
        release_head = run(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout,
            env=env,
            timeout=args.timeout,
        ).stdout.strip()
        if release_head != CAREER_OPS_RELEASE_GIT_HEAD:
            raise RuntimeError(
                f"unexpected Career-Ops release head: {release_head} != {CAREER_OPS_RELEASE_GIT_HEAD}"
            )

        shutil.copyfile(jd_fixture, checkout / "synthetic-jd.md")
        shutil.copyfile(cv_fixture, checkout / "cv.md")

        gap_cp = run(
            ["node", "jd-skill-gap.mjs", "synthetic-jd.md"],
            cwd=checkout,
            env=env,
            timeout=args.timeout,
        )
        gap = json.loads(gap_cp.stdout)
        expected_gap = {
            "existing": [],
            "supportedByResume": ["TypeScript", "Rust", "Python", "Go"],
            "gap": ["Spring", "JavaScript", "C++"],
            "lowConfidence": None,
            "partialCoverage": None,
        }
        if gap != expected_gap:
            raise RuntimeError(f"unexpected jd-skill-gap result: {json.dumps(gap, sort_keys=True)}")

        self_test = run(
            ["node", "jd-skill-gap.mjs", "--self-test"],
            cwd=checkout,
            env=env,
            timeout=args.timeout,
        )
        if "115 passed, 0 failed" not in self_test.stdout:
            raise RuntimeError(f"Career-Ops self-test did not reach expected result: {self_test.stdout!r}")

        main_only_probe = run(
            ["node", "keyword-match.mjs", "--url", "https://example.invalid"],
            cwd=checkout,
            env=env,
            timeout=args.timeout,
            check=False,
        )
        probe_text = main_only_probe.stdout + main_only_probe.stderr
        if main_only_probe.returncode == 0 or "Unknown option: --url" not in probe_text:
            raise RuntimeError(
                "stable release unexpectedly accepted the main-only keyword-match --url surface"
            )

        result = {
            "schemaVersion": 1,
            "kind": "ordivon.career.provider-native-replay",
            "observedAtDate": "2026-11-01",
            "provider": "career-ops-hq/career-ops",
            "binding": {
                "npm": "@santifer/career-ops",
                "version": CAREER_OPS_VERSION,
                "releaseGitHead": release_head,
                "packageCliBoundary": "top-level package CLI performs workspace init; qualified diagnostic runs from the initialized stable-release workspace",
                "qualifiedEntrypoint": "node jd-skill-gap.mjs synthetic-jd.md",
            },
            "fixtures": {
                "jobDescription": {
                    "path": str(jd_fixture.relative_to(ROOT)),
                    "sha256": sha256(jd_fixture),
                },
                "syntheticCv": {
                    "path": str(cv_fixture.relative_to(ROOT)),
                    "sha256": sha256(cv_fixture),
                },
            },
            "invocations": {
                "init": f"npx --yes @santifer/career-ops@{CAREER_OPS_VERSION} init <ephemeral>",
                "gap": "node jd-skill-gap.mjs synthetic-jd.md",
                "selfTest": "node jd-skill-gap.mjs --self-test",
                "negativeCurrentnessProbe": "node keyword-match.mjs --url https://example.invalid",
            },
            "observed": {
                "gapResult": gap,
                "selfTestSummary": "115 passed, 0 failed",
                "negativeCurrentnessProbeExitCode": main_only_probe.returncode,
                "negativeCurrentnessProbeObserved": "Unknown option: --url",
            },
            "acceptance": {
                "exactReleaseHead": True,
                "providerNativeDiagnosticReplayed": True,
                "builtInSelfTestPassed": True,
                "mainOnlySurfaceRejectedByStableRelease": True,
                "userDataUsed": False,
                "externalJobBoardQueried": False,
            },
            "truthBoundary": "This replay proves only the pinned stable release's deterministic skill-gap behavior on committed synthetic fixtures and the recorded release/main interface drift. It does not prove employer eligibility, hiring probability, live vacancy state, user-specific Career data, or application submission.",
            "initStdoutTail": init.stdout[-1000:],
        }

    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
