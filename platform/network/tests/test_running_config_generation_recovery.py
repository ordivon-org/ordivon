"""R12: a post-install/pre-restart crash must not make source MATCH imply loaded."""
from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts/native-sourcecut.py"

OWNER_BOUNDARIES = (
    ("claude", "consumer:claude", "network-v2-claude-proxy.service", "/etc/network-v2/claude/sing-box.json"),
    ("finance", "consumer:finance", "network-v2-finance-egress.service", "/etc/network-v2/finance/egress.json"),
    ("supply-chain", "consumer:supply-chain", "network-v2-supply-chain-egress.service", "/etc/network-v2/supply-chain/egress.json"),
    ("x-reality", "consumer:x-reality", "network-v2-x-reality-egress.service", "/etc/network-v2/x-reality/egress.json"),
    ("chat-ingress", "consumer:chat-ingress", "network-v2-chat-ingress-proxy.service", "/etc/network-v2/chat-ingress/sing-box.json"),
)


def make_busctl(tmp: Path) -> Path:
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "busctl"
    stub.write_text('#!/bin/sh\nif [ "$FAKE_BUS_FAIL" = 1 ]; then exit 51; fi\nfor item in "$@"; do last="$item"; done\nif [ "$1" = "--system" ]; then shift; fi\ncase "$1" in\n  call) echo \'o "/fake/network_unit"\';;\n  get-property) case "$last" in\n    ActiveState) printf \'s "%s"\\n\' "$FAKE_BUS_STATE";;\n    MainPID) printf \'u %s\\n\' "$FAKE_BUS_PID";;\n    ExecMainStartTimestamp) printf \'t %s\\n\' "$FAKE_BUS_START_US";;\n    *) exit 59;;\n  esac;;\n  *) exit 58;;\nesac\n')
    unit_stub = bin_dir / "systemctl"
    unit_stub.write_text(
        '#!/bin/sh\n'
        'if [ "$1" = show ]; then\n'
        '  if [ "$FAKE_SYSTEMD_LOAD" = not-found ]; then echo not-found; else echo loaded; fi\n'
        '  exit 0\n'
        'fi\n'
        'exit 72\n'
    )
    unit_stub.chmod(0o755)
    stub.chmod(0o755)
    return bin_dir


def run(
    cfg: Path, env: dict[str, str], *,
    executable: str = sys.executable,
    invocation: tuple[str, ...] = ("-c", "import time; time.sleep(25)"),
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK), "--unit-process-file",
         "fake-egress.service", str(cfg), executable, json.dumps(invocation)],
        env=env, capture_output=True, text=True, timeout=10,
    )


def test_native_systemd_process_epoch_exposes_interrupted_release(
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "runtime.json"
    cfg.write_bytes(b'{"generation":"old"}')
    # Native systemd timestamps are microsecond precision; make creation
    # order unambiguous without pretending a same-tick observation proves it.
    time.sleep(0.02)
    bin_dir = make_busctl(tmp_path)
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(25)", str(cfg)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        # systemd's creation epoch is supplied by the real systemd D-Bus in
        # production. This disposable process only supplies a live /proc PID
        # and argv describing the real file.
        env = {
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
            "FAKE_BUS_FAIL": "0",
            "FAKE_BUS_PID": str(child.pid),
            "FAKE_BUS_STATE": "active",
            "FAKE_BUS_START_US": str(time.time_ns() // 1000),
        }
        matching = run(cfg, env)
        assert (matching.returncode, matching.stdout.strip()) == (0, "MATCH"), matching.stderr
        # All installed bytes are now NEW but the original process is alive.
        cfg.write_bytes(b'{"generation":"new"}')
        stale = run(cfg, env)
        assert (stale.returncode, stale.stdout.strip()) == (0, "DRIFT")
        incorrect_executable = run(cfg, env, executable="/usr/bin/true")
        assert incorrect_executable.returncode != 0 and "UNKNOWN" in incorrect_executable.stderr
        incorrect_argv = run(cfg, env, invocation=("-c", "print('not the configured program')"))
        assert incorrect_argv.returncode != 0 and "UNKNOWN" in incorrect_argv.stderr
        failure = run(cfg, {**env, "FAKE_BUS_FAIL": "1"})
        assert failure.returncode != 0 and "UNKNOWN" in failure.stderr
        # First-install partial crash: installed config exists but systemd
        # independently proves the service unit has not been installed yet.
        uninstalled = run(cfg, {
            **env, "FAKE_BUS_FAIL": "1", "FAKE_SYSTEMD_LOAD": "not-found",
        })
        assert (uninstalled.returncode, uninstalled.stdout.strip()) == (0, "DRIFT")
        missing_pid = run(cfg, {**env, "FAKE_BUS_PID": "0"})
        assert missing_pid.returncode != 0 and "UNKNOWN" in missing_pid.stderr
        wrong_file = tmp_path / "not-loaded.json"
        wrong_file.write_bytes(b'{"generation":"unrelated"}')
        wrong_process = run(wrong_file, env)
        assert wrong_process.returncode != 0 and "UNKNOWN" in wrong_process.stderr
        future = run(cfg, {**env, "FAKE_BUS_START_US": str(time.time_ns() // 1000 + 10_000_000)})
        assert future.returncode != 0 and "UNKNOWN" in future.stderr
        failed_unit = run(cfg, {**env, "FAKE_BUS_STATE": "failed"})
        assert failed_unit.returncode != 0 and "UNKNOWN" in failed_unit.stderr
        inactive = run(cfg, {**env, "FAKE_BUS_STATE": "inactive", "FAKE_BUS_PID": "0"})
        assert (inactive.returncode, inactive.stdout.strip()) == (0, "MATCH")
        # A source symlink never becomes a trustworthy installed generation.
        cfg.unlink()
        cfg.symlink_to(tmp_path / "other")
        foreign = run(cfg, env)
        assert foreign.returncode != 0 and "UNKNOWN" in foreign.stderr
        cfg.unlink()
        missing = run(cfg, env)
        assert (missing.returncode, missing.stdout.strip()) == (0, "DRIFT")
    finally:
        child.terminate()
        child.wait(timeout=8)


@pytest.mark.parametrize("owner,task,unit,installed", OWNER_BOUNDARIES)
def test_owner_convergence_distinguishes_reinstall_from_only_restart(
    owner: str, task: str, unit: str, installed: str,
) -> None:
    body = (ROOT / "consumers" / owner / "Taskfile.yml").read_text()
    assert "\n  " + task + ":process-fresh:\n" in body
    probe = body.split("  " + task + ":process-fresh:\n", 1)[1].split(
        "  " + task + ":converge:\n", 1
    )[0]
    assert "--unit-process-file " + unit + " " + installed in probe
    assert '/usr/bin/sing-box \'["run","-c"]\'' in probe
    converge = body.split("  " + task + ":converge:\n", 1)[1]
    assert "task --silent " + task + ":process-fresh" in converge
    assert "MATCH/DRIFT)" in converge
    assert "DRIFT/MATCH|DRIFT/DRIFT)" in converge
    assert "MATCH/MATCH)" in converge
    assert "systemctl restart " in converge
    assert "task --silent " + task + ":sourcecut" in converge


def test_x_reality_target_restart_propagates_to_its_actual_egress_service() -> None:
    text = (ROOT / "consumers/x-reality/systemd/network-v2-x-reality-egress.service").read_text()
    assert "PartOf=network-v2-x-reality.target" in text
