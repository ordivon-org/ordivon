"""R13: native flock serializes a complete owner converge and readiness receipt.

Uses the ORIGINAL Go Task converge shell, with only dependencies and systemctl
substituted in disposable paths; no real Network unit is started or stopped.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import signal
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
OWNERS = ("claude", "finance", "supply-chain", "x-reality", "chat-ingress")
LOCKFILE = "/run/lock/ordivon-network-v2-converge.lock"


def task_section(text: str, task: str) -> str:
    match = re.search(r"(?m)^  " + re.escape(task) + r":\s*$", text)
    assert match, task
    tail = text[match.end():]
    end = re.search(r"(?m)^  [\w:.-]+:\s*$", tail)
    return "  " + task + ":\n" + tail[:end.start() if end else len(tail)]


def fixture(tmp: Path, owner: str, *, shared_lock: Path) -> tuple[Path, dict[str, str]]:
    directory = tmp / owner
    directory.mkdir(parents=True)
    name = "consumer:" + owner
    original = (ROOT / "consumers" / owner / "Taskfile.yml").read_text()
    converge = task_section(original, name + ":converge")
    converge = converge.replace(LOCKFILE, str(shared_lock))
    cfg = directory / "Taskfile.yml"
    prefix = "version: '3'\n\ntasks:\n"
    for action, command in (
        ("validate", "/usr/bin/true"),
        ("classify", 'echo "$SOURCE_STATE"'),
        ("process-fresh", 'echo "$PROCESS_STATE"'),
        ("sourcecut", "/usr/bin/true"),
        ("materialize", 'printf "materialize\\n" >> "$EVENTS"; touch "$BARRIER"; sleep 1.6'),
        ("ready", 'printf "verify\\n" >> "$EVENTS"; sleep 0.05'),
        ("verify", 'printf "verify\\n" >> "$EVENTS"; sleep 0.05'),
    ):
        prefix += "  " + name + ":" + action + ":\n    cmds:\n      - |\n        " + command + "\n\n"
    cfg.write_text(prefix + converge)
    mockbin = directory / "bin"
    mockbin.mkdir()
    fake = mockbin / "systemctl"
    fake.write_text('#!/bin/sh\nprintf "systemctl %s\\n" "$*" >> "$EVENTS"\nexit 0\n')
    fake.chmod(0o755)
    env = {
        **os.environ,
        "PATH": str(mockbin) + os.pathsep + os.environ["PATH"],
        "SOURCE_STATE": "DRIFT",
        "PROCESS_STATE": "MATCH",
        "EVENTS": str(directory / "events"),
        "BARRIER": str(directory / "materialize-started"),
    }
    return directory, env


def command(owner: str) -> list[str]:
    return ["/usr/bin/mise", "exec", "task@3.54.0", "--",
            "task", "--silent", "consumer:" + owner + ":converge"]


@pytest.mark.parametrize("owner", OWNERS)
def test_converge_lock_precedes_all_effects_and_includes_verification(owner: str) -> None:
    content = (ROOT / "consumers" / owner / "Taskfile.yml").read_text()
    task = task_section(content, "consumer:" + owner + ":converge")
    assert task.count(LOCKFILE) == 1
    assert "flock -n -E 75 " + LOCKFILE + " /bin/sh -s" in task
    assert task.index("flock -n -E 75 ") < task.index("source_state=")
    assert "NETWORK_V2_CONVERGE" in task
    assert "task --silent consumer:" + owner + (":verify" if owner in ("claude", "chat-ingress") else ":ready") in task
    assert task.index("systemctl is-active") < task.rindex("task --silent consumer:" + owner)


def test_parallel_native_converge_is_serialized_and_lock_recovers_after_crash(tmp_path: Path) -> None:
    lock = tmp_path / "shared-native-network.lock"
    directory, env = fixture(tmp_path, "finance", shared_lock=lock)
    cmd = command("finance")
    first = subprocess.Popen(cmd, cwd=directory, env=env, start_new_session=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        barrier = Path(env["BARRIER"])
        deadline = time.monotonic() + 12
        while not barrier.exists() and time.monotonic() < deadline:
            assert first.poll() is None, "first native publish exited before materialization"
            time.sleep(0.02)
        assert barrier.exists()
        second = subprocess.run(cmd, cwd=directory, env=env,
                                capture_output=True, text=True, timeout=8)
        assert second.returncode != 0, "two same-owner publishers overlapped"
        assert "already" in second.stderr.lower() or "in progress" in second.stderr.lower()
        assert Path(env["EVENTS"]).read_text().count("materialize") == 1
        # Native process-group death must release its kernel-held flock.
        os.killpg(first.pid, signal.SIGKILL)
        first.communicate(timeout=6)
        third = subprocess.run(cmd, cwd=directory, env=env,
                               capture_output=True, text=True, timeout=15)
        assert third.returncode == 0, third.stderr
        assert Path(env["EVENTS"]).read_text().count("materialize") == 2
    finally:
        if first.poll() is None:
            os.killpg(first.pid, signal.SIGKILL)
        first.communicate(timeout=7)


def test_different_consumers_share_the_same_publish_lock(tmp_path: Path) -> None:
    lock = tmp_path / "shared-native-network.lock"
    a, env_a = fixture(tmp_path, "claude", shared_lock=lock)
    b, env_b = fixture(tmp_path, "finance", shared_lock=lock)
    first = subprocess.Popen(command("claude"), cwd=a, env=env_a,
                             start_new_session=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 12
        while not Path(env_a["BARRIER"]).exists() and time.monotonic() < deadline:
            assert first.poll() is None
            time.sleep(0.02)
        assert Path(env_a["BARRIER"]).exists()
        peer = subprocess.run(command("finance"), cwd=b, env=env_b,
                              capture_output=True, text=True, timeout=8)
        assert peer.returncode != 0
        assert not Path(env_b["BARRIER"]).exists()
        out, err = first.communicate(timeout=12)
        assert first.returncode == 0, (out, err)
        after = subprocess.run(command("finance"), cwd=b, env=env_b,
                               capture_output=True, text=True, timeout=15)
        assert after.returncode == 0, after.stderr
        assert Path(env_b["BARRIER"]).exists()
    finally:
        if first.poll() is None:
            os.killpg(first.pid, signal.SIGKILL)
        first.communicate(timeout=7)
