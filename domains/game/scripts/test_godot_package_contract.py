"""Factory contract of native Godot preview publication, not a simulated game test.

Run the actual mise shell bodies with controlled supplier commands. These cases
prove stale/partial outputs cannot be mistaken for THIS invocation's release;
native Godot/CI smoke remains a separate, required consumer.
"""
from __future__ import annotations

import hashlib
import os
import shutil
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
  export:room-linux|export:room-windows)
    python3 -c 'import sys,tomllib,subprocess; from pathlib import Path; tasks=tomllib.loads(Path("mise.toml").read_text())["tasks"]; sys.exit(subprocess.run(["/bin/bash","-c",tasks[sys.argv[1]]["run"]]).returncode)' "$2";;
  *) echo "unexpected mise task: $*" >&2; exit 70;;
esac
""",
    )
    executable(
        bin_dir / "godot",
        """if [[ "$1" == --version ]]; then echo "4.7.2.stable.official.deadbeef"; exit 0; fi
if [[ "$*" == *"--import"* ]]; then
  if [[ "$INJECT_FAILURE" == import_error ]]; then echo "ERROR: import diagnostic" >&2; fi
  exit 0
fi
if [[ "$*" == *"Windows x86_64"* ]] && [[ "$INJECT_FAILURE" == windows ]]; then exit 47; fi
dest=""
for arg in "$@"; do dest="$arg"; done
if [[ "$*" == *"Linux x86_64"* ]]; then
  printf "#!/bin/sh\\nexit 0\\n" > "$dest"
  if [[ "$INJECT_FAILURE" == smoke_error ]]; then
    printf '#!/bin/sh\necho "ERROR: exported startup diagnostic" >&2\nexit 0\n' > "$dest"
  fi
  chmod +x "$dest"
  if [[ "$INJECT_FAILURE" == export_linux_error ]]; then echo "ERROR: Linux export diagnostic" >&2; fi
elif [[ "$*" == *"Windows x86_64"* ]]; then
  printf "fixture-win-binary" > "$dest"
  if [[ "$INJECT_FAILURE" == export_windows_error ]]; then echo "ERROR: Windows export diagnostic" >&2; fi
  if [[ "$INJECT_FAILURE" == template_late ]]; then printf 'changed' >> "$XDG_DATA_HOME/godot/export_templates/4.7.2.stable/windows_release_x86_64.exe"; fi
else
  echo "unexpected fixture Godot action: $*" >&2
  exit 71
fi
""",
    )
    executable(
        bin_dir / "git",
        '''if [[ "$1" == rev-parse ]]; then echo "''' + FIXTURE_SHA + '''"; exit 0; fi
if [[ "$1" == status ]]; then
  if [[ "$INJECT_FAILURE" == dirty ]]; then
    echo " M domains/game/mise.toml"
  elif [[ "$INJECT_FAILURE" == root_dirty ]]; then
    # The old Game-local "-- ." status check hides the dirty root mise.toml,
    # even though mise cascades root configuration into native Game tasks.
    for arg in "$@"; do
      if [[ "$arg" == "." ]]; then exit 0; fi
    done
    echo " M mise.toml"
  elif [[ "$INJECT_FAILURE" == root_dirty_late ]]; then
    # First read: clean; second read: the root configuration changes after
    # native export. A package must not publish READY for a mixed input epoch.
    if [[ ! -e "$GIT_STATUS_COUNTER_FILE" ]]; then
      : > "$GIT_STATUS_COUNTER_FILE"
    else
      for arg in "$@"; do
        if [[ "$arg" == "." ]]; then exit 0; fi
      done
      echo " M mise.toml"
    fi
  fi
  exit 0
fi
exit 72
''',
    )
    for rel in (
        "examples/room-encounter/addons/dialogue_manager/LICENSE",
        "examples/room-encounter/assets/LICENSE.txt",
        "examples/beacon-relay/LICENSE",
        "examples/beacon-relay/fonts/LICENSE.txt",
        "examples/beacon-relay/CREDITS.txt",
    ):
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("fixture license or credits\n", encoding="utf-8")
    shutil.copyfile(GAME / "mise.toml", root / "mise.toml")
    (root / "scripts").mkdir()
    for module in ("native_export_identity.py", "native_process.py"):
        shutil.copyfile(GAME / "scripts" / module, root / "scripts" / module)
    for product in ("room-encounter", "beacon-relay"):
        project = root / "examples" / product
        project.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(GAME / "examples" / product / "export_presets.cfg", project / "export_presets.cfg")
        if fail == "custom_template":
            preset = project / "export_presets.cfg"
            preset.write_text(preset.read_text().replace('custom_template/release=""', 'custom_template/release="wrong.bin"'))
    data = root / "native-data"
    templates = data / "godot/export_templates/4.7.2.stable"
    templates.mkdir(parents=True)
    (templates / "linux_release.x86_64").write_bytes(b"fixture-linux-template")
    if fail != "missing_template":
        (templates / "windows_release_x86_64.exe").write_bytes(b"fixture-windows-template")
    env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
           "INJECT_FAILURE": fail, "GIT_STATUS_COUNTER_FILE": str(root / "git-status-counter"), "XDG_DATA_HOME": str(data)}
    env.pop("GAME_GODOT_TEMPLATE_DIR", None)
    if fail == "misleading_override":
        env["GAME_GODOT_TEMPLATE_DIR"] = str(root / "wrong-template-dir")
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
        if failure in ("dirty", "root_dirty"):
            assert "GAME_FACTORY_DIRTY_SOURCE_NOT_RELEASABLE" in result.stderr
        elif failure == "root_dirty_late":
            assert "GAME_FACTORY_SOURCE_CHANGED_DURING_BUILD" in result.stderr
        elif failure == "template_late":
            assert "GAME_FACTORY_EXPORT_INPUT_CHANGED_DURING_BUILD" in result.stderr
        elif failure in ("import_error", "export_linux_error", "export_windows_error", "smoke_error"):
            assert "native Godot process rejected: exit=0" in result.stderr
        elif failure == "missing_template":
            assert "missing or empty native export input" in result.stderr
        elif failure == "custom_template":
            assert "unsupported or ambiguous native export preset" in result.stderr
        elif failure == "misleading_override":
            assert "GAME_GODOT_TEMPLATE_DIR is unsupported" in result.stderr


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
        for label, value in (("LINUX", b"fixture-linux-template"), ("WINDOWS", b"fixture-windows-template")):
            assert f"TEMPLATE_{label}_SHA256={hashlib.sha256(value).hexdigest()}" in receipt
        assert f"ENGINE_SHA256={hashlib.sha256((root / 'fixture-bin/godot').read_bytes()).hexdigest()}" in receipt
        assert "RELEASE_PUBLISHED=false" in receipt
        assert "QUALIFICATION=native_headless_preview" in receipt
        assert "LINUX_SCOPE=native_headless_smoke" in receipt
        assert "WINDOWS_SCOPE=export_only" in receipt
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
            with tarfile.open(bundle / archives[0], "r:gz") as ar:
                assert {"room-encounter.x86_64", "DIALOGUE_MANAGER_LICENSE.txt", "KENNEY_ASSETS_LICENSE.txt"} == set(ar.getnames())
            with zipfile.ZipFile(bundle / archives[1]) as ar:
                assert {"room-encounter.exe", "DIALOGUE_MANAGER_LICENSE.txt", "KENNEY_ASSETS_LICENSE.txt"} == set(ar.namelist())


if __name__ == "__main__":
    for task, fail in (
        ("factory:package:room", "windows"),
        ("factory:package:room", "dirty"),
        ("factory:package:room", "root_dirty"),
        ("factory:package:room", "root_dirty_late"),
        ("factory:package:beacon", "test"),
        ("factory:package:beacon", "windows"),
        ("factory:package:beacon", "dirty"),
        ("factory:package:beacon", "root_dirty"),
        ("factory:package:beacon", "root_dirty_late"),
    ):
        assert_failure(task, fail)
    for task in ("factory:package:room", "factory:package:beacon"):
        for failure in ("template_late", "missing_template", "custom_template", "misleading_override"):
            assert_failure(task, failure)
    for task in ("factory:package:room", "factory:package:beacon"):
        for failure in ("export_linux_error", "export_windows_error", "smoke_error"):
            assert_failure(task, failure)
    assert_failure("factory:package:room", "import_error")
    assert_success("factory:package:room", ROOM)
    assert_success("factory:package:beacon", BEACON)
    print("GAME_FACTORY_PACKAGE_CONTRACT_PASS failures=24 successes=2")
