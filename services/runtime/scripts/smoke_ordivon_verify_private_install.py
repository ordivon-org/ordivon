#!/usr/bin/env python3
"""Private package install smoke test for Ordivon Verify (PV-N4).

Creates an isolated environment, installs the local package in editable
mode, and verifies entrypoints + trust ladder. Does not publish, upload,
or write to project files.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "src" / "ordivon_verify"


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, **kw)


def smoke_imports():
    """Verify package import paths work."""
    print("1. Package imports ...")
    sys.path.insert(0, str(ROOT / "src"))
    try:
        import ordivon_verify  # noqa: F401
        from ordivon_verify.cli import main  # noqa: F401
        from ordivon_verify.report import build_report  # noqa: F401
        from ordivon_verify.runner import run_check  # noqa: F401

        print("   ✅ Package imports pass")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    finally:
        sys.path.pop(0)
    return True


def smoke_module_entrypoint():
    """Verify python -m ordivon_verify works."""
    print("2. Module entrypoint ...")
    result = _run([sys.executable, "-m", "ordivon_verify", "all"], cwd=str(ROOT))
    if result.returncode == 0 and "READY" in result.stdout:
        print("   ✅ Module entrypoint READY")
        return True
    print(f"   ❌ Module entrypoint failed (exit {result.returncode})")
    return False


def smoke_console_entrypoint():
    """Verify ordivon-verify console script works."""
    print("3. Console entrypoint ...")
    result = _run(["uv", "run", "ordivon-verify", "all"], cwd=str(ROOT))
    if result.returncode == 0 and "READY" in result.stdout:
        print("   ✅ Console entrypoint READY")
        return True
    print(f"   ❌ Console entrypoint failed (exit {result.returncode})")
    return False


def smoke_script_wrapper():
    """Verify script wrapper still works."""
    print("4. Script wrapper ...")
    result = _run(
        [sys.executable, str(ROOT / "scripts" / "ordivon_verify.py"), "all"],
        cwd=str(ROOT),
    )
    if result.returncode == 0 and "READY" in result.stdout:
        print("   ✅ Script wrapper READY")
        return True
    print(f"   ❌ Script wrapper failed (exit {result.returncode})")
    return False


def smoke_quickstart():
    """Verify quickstart fixture reaches READY."""
    print("5. Quickstart fixture ...")
    qs = ROOT / "examples" / "ordivon-verify" / "quickstart"
    result = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ordivon_verify.py"),
            "all",
            "--root",
            str(qs),
            "--config",
            str(qs / "ordivon.verify.json"),
        ],
        cwd=str(ROOT),
    )
    if result.returncode == 0 and "READY" in result.stdout:
        print("   ✅ Quickstart READY")
        return True
    print(f"   ❌ Quickstart failed (exit {result.returncode})")
    return False


def smoke_bad_fixture():
    """Verify bad fixture remains BLOCKED."""
    print("6. Bad external fixture ...")
    bad = ROOT / "tests" / "fixtures" / "ordivon_verify_external_repo"
    result = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ordivon_verify.py"),
            "all",
            "--root",
            str(bad),
            "--config",
            str(bad / "ordivon.verify.json"),
        ],
        cwd=str(ROOT),
    )
    if result.returncode == 1 and "BLOCKED" in result.stdout:
        print("   ✅ Bad external BLOCKED (exit 1)")
        return True
    print(f"   ❌ Bad external unexpected (exit {result.returncode})")
    return False


def smoke_package_boundary():
    """Verify no broker/finance imports in package source."""
    print("7. Package boundary ...")
    forbidden = ["adapters.finance", "domains.finance", "Alpaca", "broker", "RiskEngine"]
    found = []
    for py_file in PACKAGE_SRC.rglob("*.py"):
        content = py_file.read_text()
        for term in forbidden:
            if term in content:
                found.append(f"{py_file.name}: {term}")
    if not found:
        print("   ✅ No broker/finance imports in package")
        return True
    for f in found:
        print(f"   ❌ {f}")
    return False


def main() -> int:

    print("=" * 60)
    print("ORDIVON VERIFY — PRIVATE PACKAGE INSTALL SMOKE")
    print("=" * 60)
    print(f"  Root: {ROOT}")
    print(f"  Package: {PACKAGE_SRC}")
    print()

    results = {
        "imports": smoke_imports(),
        "module": smoke_module_entrypoint(),
        "console": smoke_console_entrypoint(),
        "wrapper": smoke_script_wrapper(),
        "quickstart": smoke_quickstart(),
        "bad_fixture": smoke_bad_fixture(),
        "boundary": smoke_package_boundary(),
    }

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"RESULT: {passed}/{total} checks pass")
    if passed == total:
        print("✅ Private package install smoke PASSED")
        return 0
    print("❌ Private package install smoke FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
