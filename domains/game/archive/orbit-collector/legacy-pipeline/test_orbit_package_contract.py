"""Native Orbit packaging contract: missing smoke prerequisites never produce a verified preview.

This invokes the real Game-owned package shell entry. A controlled PATH fixture supplies
only one of the two required probe commands, so the other must fail before any build
or GPU operation. A stale fixed-path candidate archive is deliberately invalidated.
This is NOT a graphical rendering acceptance test.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = GAME / "scripts" / "package_orbit_linux.sh"
ARCHIVE_NAME = "orbit-collector-linux-x86_64.tar.gz"


def main() -> None:
    for missing in ("xvfb-run", "timeout"):
        with tempfile.TemporaryDirectory(prefix="game-orbit-native-preflight-") as temporary:
            root = Path(temporary)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            # The packaging entry now invalidates its fixed previous archive
            # before probing graphics, so retain the three basic file utilities.
            for utility in ("dirname", "mkdir", "rm"):
                installed = shutil.which(utility)
                assert installed, f"required preflight utility absent: {utility}"
                (bin_dir / utility).symlink_to(installed)
            available = "timeout" if missing == "xvfb-run" else "xvfb-run"
            binary = bin_dir / available
            binary.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            binary.chmod(0o755)
            output = root / "out"
            output.mkdir()
            # An earlier successful preview must not masquerade as this failed build.
            stale_archive = output / ARCHIVE_NAME
            stale_archive.write_bytes(b"older-build")
            env = os.environ.copy()
            env["PATH"] = str(bin_dir)
            env["GAME_EXPORT_DIR"] = str(output)
            result = subprocess.run(
                ["/bin/bash", str(PACKAGE_SCRIPT)],
                cwd=GAME,
                env=env,
                text=True,
                capture_output=True,
                timeout=20,
                check=False,
            )
            assert result.returncode == 3, (
                f"missing {missing} returned {result.returncode}: "
                f"{result.stdout}\n{result.stderr}"
            )
            assert f"ORBIT_WINDOWED_SMOKE_ENV_BLOCKED missing={missing}" in result.stderr
            assert "ORBIT_FACTORY_LINUX_PREVIEW_READY" not in (
                result.stdout + result.stderr
            )
            assert not stale_archive.exists(), (
                "failed packaging must retire the previous candidate at the fixed output path"
            )
    # A child can return 124 immediately; that is not a native timeout expiry.
    # This is a real GNU timeout negative control, not a virtual GPU test.
    timeout_path = shutil.which("timeout")
    assert timeout_path is not None, "GNU timeout required by Linux package contract"
    early = subprocess.run(
        [timeout_path, "--verbose", "2s", "/bin/bash", "-c", "exit 124"],
        cwd=GAME,
        text=True,
        capture_output=True,
        timeout=8,
        check=False,
    )
    assert early.returncode == 124, early
    assert "timeout: sending signal TERM to command" not in (early.stdout + early.stderr), (
        "early return code 124 cannot substitute for a timeout-expiry witness"
    )
    print("GAME_ORBIT_PACKAGE_ENV_BLOCKED_PASS cases=2 ready=no archive=no")
    print("GAME_ORBIT_TIMEOUT_EARLY_124_REJECTED_PASS cases=1")


if __name__ == "__main__":
    main()
