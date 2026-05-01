#!/usr/bin/env python3
"""Ordivon Verify — Local Build Artifact Smoke (PV-N8).

Builds wheel/sdist locally, inspects artifact contents for private core
leakage, and reports honestly. Does not upload, publish, or activate anything.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

# ── Files/dirs that must NOT appear in a public Ordivon Verify artifact ─
FORBIDDEN_PATHS = [
    "adapters/",
    "domains/",
    "orchestrator/",
    "capabilities/",
    "intelligence/",
    "apps/",
    "policies/",
    "execution/",
    "infra/",
    "shared/",
    "state/",
    "services/",
    "docs/archive/",
    "docs/governance/",
    "docs/runtime/paper-trades/",
    "docs/runtime/alpaca-",
    "knowledge/",
    "scripts/smoke_",
    "scripts/eval_",
    "scripts/run_",
    "scripts/dev/",
    "scripts/seed_",
    "tests/contracts/",
    "tests/integration/",
    "tests/e2e/",
]

# ── Files/dirs that SHOULD be in the artifact ─
EXPECTED_PATHS = [
    "ordivon_verify/",
    "ordivon_verify/cli.py",
    "ordivon_verify/checks/",
    "src/ordivon_verify/",
]


def build_artifact() -> dict:
    """Build wheel/sdist. Returns result dict."""
    result = {"wheel_built": False, "sdist_built": False, "wheel_path": None, "sdist_path": None}

    proc = subprocess.run(
        ["uv", "build"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        result["build_error"] = proc.stderr[-500:]
        return result

    # Find artifacts
    for f in sorted(DIST.glob("*.whl")):
        result["wheel_built"] = True
        result["wheel_path"] = str(f)
    for f in sorted(DIST.glob("*.tar.gz")):
        result["sdist_built"] = True
        result["sdist_path"] = str(f)

    return result


def inspect_artifact(path: Path) -> list[str]:
    """List all member names in a wheel or sdist. Returns list of names."""
    names: list[str] = []
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
    elif path.suffix == ".gz" and ".tar" in path.suffix:
        with tarfile.open(path, "r:gz") as tf:
            names = tf.getnames()
    return names


def find_forbidden(names: list[str]) -> list[str]:
    """Find member names matching forbidden paths."""
    found = []
    for name in names:
        for forbidden in FORBIDDEN_PATHS:
            if name.startswith(forbidden) or forbidden.rstrip("/") in name:
                found.append(name)
                break
    return found


def find_expected(names: list[str]) -> list[str]:
    """Check which expected paths are present."""
    present = []
    for expected in EXPECTED_PATHS:
        for name in names:
            if expected in name or name.startswith(expected):
                present.append(expected)
                break
    return present


def scan_secrets(names: list[str]) -> list[str]:
    """Quick structural scan for secret-sounding paths in artifact."""
    suspicious = []
    for name in names:
        lower = name.lower()
        if any(kw in lower for kw in ["secret", "api_key", "token", "password", ".env"]):
            suspicious.append(name)
    return suspicious


def main(json_output: bool = False) -> int:
    # Build
    build = build_artifact()

    if not build["wheel_built"] and not build["sdist_built"]:
        if json_output:
            print(json.dumps({"error": "build failed", "detail": build.get("build_error", "")}))
        else:
            print(f"❌ Build failed: {build.get('build_error', 'unknown')}")
        return 1

    # Inspect
    wheel_names: list[str] = []
    sdist_names: list[str] = []
    if build["wheel_path"]:
        wheel_names = inspect_artifact(Path(build["wheel_path"]))
    if build["sdist_path"]:
        sdist_names = inspect_artifact(Path(build["sdist_path"]))

    forbidden_wheel = find_forbidden(wheel_names)
    forbidden_sdist = find_forbidden(sdist_names or [])
    total_forbidden = len(forbidden_wheel) + len(forbidden_sdist)
    has_ordivon = any("ordivon_verify" in n for n in wheel_names)
    blocker = total_forbidden > 0 or not has_ordivon

    if json_output:
        print(
            json.dumps(
                {
                    "wheel_built": build["wheel_built"],
                    "sdist_built": build["sdist_built"],
                    "wheel_path": build.get("wheel_path"),
                    "sdist_path": build.get("sdist_path"),
                    "wheel_members": len(wheel_names),
                    "sdist_members": len(sdist_names),
                    "forbidden_in_wheel": len(forbidden_wheel),
                    "forbidden_in_sdist": len(forbidden_sdist),
                    "ordivon_verify_present": has_ordivon,
                    "blocked": blocker,
                    "forbidden_top_level": sorted(set(f.split("/")[0] for f in forbidden_wheel)),
                    "disclaimer": "Local build only. No upload. No publish.",
                },
                indent=2,
            )
        )
        return 1 if blocker else 0

    # Human output
    print("=" * 60)
    print("ORDIVON VERIFY — LOCAL BUILD ARTIFACT SMOKE")
    print("=" * 60)

    print(f"\n   ✅ Wheel: {build.get('wheel_path', 'N/A')} ({len(wheel_names)} members)")
    print(f"   ✅ Sdist: {build.get('sdist_path', 'N/A')}")
    print(f"   Forbidden paths in wheel:  {len(forbidden_wheel)}")
    print(f"   Forbidden paths in sdist:  {len(forbidden_sdist)}")
    print(f"   ordivon_verify present:    {has_ordivon}")

    if forbidden_wheel:
        print(f"\n   ❌ PRIVATE CORE LEAKAGE ({len(forbidden_wheel)} paths in wheel):")
        unique = sorted(set(f.split("/")[0] for f in forbidden_wheel))
        for u in unique:
            count = sum(1 for f in forbidden_wheel if f.startswith(u))
            print(f"      {u}/ ({count} files)")

    print(f"\n{'=' * 60}")
    if blocker:
        print("❌ BLOCKED: Private core code in build artifact.")
        print("   pyproject.toml packages the entire private repo.")
        print("   Public wedge needs its own package config.")
    else:
        print("✅ CLEAN: No private core in build artifact.")
    print("\n   Local build smoke only. No upload. No publish. No public release.")

    return 1 if blocker else 0


if __name__ == "__main__":
    sys.exit(main("--json" in sys.argv))
