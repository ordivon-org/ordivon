"""Factory contract of native Godot preview publication, not a simulated game test.

Run the actual mise shell bodies with controlled supplier commands. These cases
prove stale/partial outputs cannot be mistaken for THIS invocation's release;
native Godot/CI smoke remains a separate, required consumer.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
TASKS = tomllib.loads((GAME / "mise.toml").read_text())["tasks"]
ROOM = ("room-encounter-linux-x86_64.tar.gz", "room-encounter-windows-x86_64.zip")
BEACON = ("beacon-relay-linux-x86_64.tar.gz", "beacon-relay-windows-x86_64.zip")
FIXTURE_SHA = "f" * 40


def executable(path: Path, content: str) -> None:
    path.write_text("#!/usr/bin/env bash\nset -e\n" + content, encoding="utf-8")
    path.chmod(0o755)


def run_task(root: Path, name: str, fail: str = "") -> subprocess.CompletedProcess[str]:
    bin_dir = root / "fixture-bin"
    bin_dir.mkdir(exist_ok=True)
    executable(
        bin_dir / "mise",
        """case "$2" in
  factory:validate:godot) exit 0;;
  test:beacon) if [[ "$INJECT_FAILURE" == test ]]; then exit 43; fi; exit 0;;
  export:room-linux)
    mkdir -p "$GAME_EXPORT_DIR"
    printf "fixture-linux" > "$GAME_EXPORT_DIR/../room-encounter-linux-x86_64.tar.gz";;
  export:room-windows)
    if [[ "$INJECT_FAILURE" == windows ]]; then exit 47; fi
    mkdir -p "$GAME_EXPORT_DIR"
    printf "fixture-windows" > "$GAME_EXPORT_DIR/../room-encounter-windows-x86_64.zip";;
  *) echo "unexpected mise task: $*" >&2; exit 70;;
esac
""",
    )
    executable(
        bin_dir / "godot",
        """if [[ "$1" == --version ]]; then echo "fixture-godot"; exit 0; fi
if [[ "$*" == *"Windows x86_64"* ]] && [[ "$INJECT_FAILURE" == windows ]]; then exit 47; fi
dest=""
for arg in "$@"; do dest="$arg"; done
if [[ "$*" == *"Linux x86_64"* ]]; then
  printf "#!/bin/sh\\nexit 0\\n" > "$dest"
  chmod +x "$dest"
elif [[ "$*" == *"Windows x86_64"* ]]; then
  printf "fixture-win-binary" > "$dest"
else
  echo "unexpected fixture Godot action: $*" >&2
  exit 71
fi
""",
    )
    executable(
        bin_dir / "git",
        '''if [[ "$1" == rev-parse ]]; then echo "''' + FIXTURE_SHA + '''"; exit 0; fi
if [[ "$1" == status ]]; then if [[ "$INJECT_FAILURE" == dirty ]]; then echo " M domains/game/mise.toml"; fi; exit 0; fi
exit 72
''',
    )
    for rel in (
        "examples/beacon-relay/LICENSE",
        "examples/beacon-relay/fonts/LICENSE.txt",
        "examples/beacon-relay/CREDITS.txt",
    ):
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("fixture license or credits\n", encoding="utf-8")
    env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "INJECT_FAILURE": fail}
    if name.endswith("beacon"):
        env["GAME_EXPORT_DIR"] = str(root / "dist" / "beacon-relay")
    return subprocess.run(
        ["/bin/bash", "-c", TASKS[name]["run"]],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def target_for(root: Path, name: str) -> Path:
    return root / "dist" / ("room-encounter" if name.endswith("room") else "beacon-relay")


def assert_failure(name: str, failure: str) -> None:
    with tempfile.TemporaryDirectory(prefix="game-package-negative-") as tmp:
        root = Path(tmp)
        target = target_for(root, name)
        target.mkdir(parents=True)
        old = target / "bundle-previous"
        old.mkdir()
        (old / "READY").write_text("last-good")
        result = run_task(root, name, failure)
        assert result.returncode != 0, (name, failure, result.stdout, result.stderr)
        assert "GAME_FACTORY_BUNDLE_PATH=" not in result.stdout
        assert sorted(p.name for p in target.glob("bundle-*")) == ["bundle-previous"]
        assert (old / "READY").read_text() == "last-good"
        assert not list(target.glob(".factory-package.*")), "staging leaked"
        if failure == "dirty":
            assert "GAME_FACTORY_DIRTY_SOURCE_NOT_RELEASABLE" in result.stderr


def assert_success(name: str, archives: tuple[str, str]) -> None:
    with tempfile.TemporaryDirectory(prefix="game-package-positive-") as tmp:
        root = Path(tmp)
        result = run_task(root, name)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        outputs = [line.split("=", 1)[1] for line in result.stdout.splitlines()
                   if line.startswith("GAME_FACTORY_BUNDLE_PATH=")]
        assert len(outputs) == 1, result.stdout
        bundle = Path(outputs[0])
        assert bundle.parent == target_for(root, name) and bundle.is_dir()
        assert sorted(p.name for p in bundle.iterdir()) == sorted(
            [*archives, "BUILD_SOURCE.txt", "SHA256SUMS", "READY"])
        receipt = (bundle / "BUILD_SOURCE.txt").read_text()
        assert f"SOURCE_COMMIT={FIXTURE_SHA}" in receipt
        assert f"SOURCE_TREE={FIXTURE_SHA}" in receipt
        assert "SOURCE_WORKTREE=clean" in receipt
        assert "RELEASE_PUBLISHED=false" in receipt
        assert "QUALIFICATION=native_headless_preview" in receipt
        check = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=bundle,
                               text=True, capture_output=True, check=False)
        assert check.returncode == 0, check.stdout + check.stderr
        assert not list(target_for(root, name).glob(".factory-package.*"))
        if name.endswith("beacon"):
            with tarfile.open(bundle / archives[0], "r:gz") as ar:
                assert {"beacon-relay.x86_64", "UPSTREAM_MIT_LICENSE.txt"}.issubset(ar.getnames())
            with zipfile.ZipFile(bundle / archives[1]) as ar:
                assert {"beacon-relay.exe", "CREDITS.txt"}.issubset(ar.namelist())
        else:
            assert (bundle / archives[0]).read_bytes() == b"fixture-linux"
            assert (bundle / archives[1]).read_bytes() == b"fixture-windows"


if __name__ == "__main__":
    for task, fail in (
        ("factory:package:room", "windows"),
        ("factory:package:room", "dirty"),
        ("factory:package:beacon", "test"),
        ("factory:package:beacon", "windows"),
        ("factory:package:beacon", "dirty"),
    ):
        assert_failure(task, fail)
    assert_success("factory:package:room", ROOM)
    assert_success("factory:package:beacon", BEACON)
    print("GAME_FACTORY_PACKAGE_CONTRACT_PASS failures=5 successes=2")
