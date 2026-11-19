"""Behavioral proof for the single pure source/install/loaded classifier.

This is deliberately independent of a production systemd or real VPN.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "native-sourcecut.py"


def invoke(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK), *map(str, args)],
        text=True, capture_output=True, timeout=10, env=env,
    )


def fake_systemd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, result: str = "no") -> dict[str, str]:
    bin_path = tmp_path / "bin"
    bin_path.mkdir(exist_ok=True)
    cmd = bin_path / "systemctl"
    cmd.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        '  show) if [ "$SOURCECUT_SYSTEMD_FAIL" = 1 ]; then exit 53; fi; echo "$SOURCECUT_SYSTEMD_RESULT" ;;\n'
        '  is-enabled) if [ "$SOURCECUT_SYSTEMD_FAIL" = 1 ]; then exit 53; fi; echo enabled ;;\n'
        '  *) exit 87 ;;\n'
        'esac\n'
    )
    cmd.chmod(0o755)
    return {**os.environ, "PATH": str(bin_path) + ":" + os.environ.get("PATH", ""),
            "SOURCECUT_SYSTEMD_FAIL": "0", "SOURCECUT_SYSTEMD_RESULT": result}


def test_native_cut_match_only_with_existing_bytes_and_loaded_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = fake_systemd(tmp_path, monkeypatch)
    src = tmp_path / "source"
    dst = tmp_path / "installed"
    src.write_bytes(b"pinned-source")
    dst.write_bytes(b"pinned-source")
    result = invoke("--file", src, dst, "--unit-loaded", "fake.service",
                    "--unit-enabled", "fake.target", "enabled", env=env)
    assert (result.returncode, result.stdout.strip()) == (0, "MATCH")


def test_native_cut_proven_difference_and_first_install_are_drift(tmp_path: Path) -> None:
    src = tmp_path / "source"
    dst = tmp_path / "one" / "two" / "installed"
    src.write_bytes(b"pinned-source")
    # Missing owned intermediate directories must still admit a *first*
    # installation; R10's parent-exists test incorrectly classified this UNKNOWN.
    first = invoke("--file", src, dst)
    assert (first.returncode, first.stdout.strip()) == (0, "DRIFT")
    dst.parent.mkdir(parents=True)
    dst.write_bytes(b"old")
    changed = invoke("--file", src, dst)
    assert (changed.returncode, changed.stdout.strip()) == (0, "DRIFT")


def test_native_cut_unreadable_source_symlink_or_foreign_parent_is_unknown(tmp_path: Path) -> None:
    src = tmp_path / "source"
    dst = tmp_path / "installed"
    src.write_bytes(b"expected")
    dst.symlink_to(src)
    result = invoke("--file", src, dst)
    assert result.returncode != 0 and "UNKNOWN" in result.stderr
    dst.unlink()
    foreign = tmp_path / "foreign"
    foreign.symlink_to(tmp_path / "nonexistent")
    result = invoke("--file", src, foreign / "installed")
    assert result.returncode != 0 and "UNKNOWN" in result.stderr


def test_native_cut_failed_systemd_observation_does_not_become_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = fake_systemd(tmp_path, monkeypatch)
    src, dst = tmp_path / "s", tmp_path / "d"
    src.write_bytes(b"x")
    dst.write_bytes(b"x")
    failed = invoke("--file", src, dst, "--unit-loaded", "fake.service",
                    env={**env, "SOURCECUT_SYSTEMD_FAIL": "1"})
    assert failed.returncode != 0 and "UNKNOWN" in failed.stderr
    changed = invoke("--file", src, dst, "--unit-loaded", "fake.service",
                     env={**env, "SOURCECUT_SYSTEMD_RESULT": "yes"})
    assert (changed.returncode, changed.stdout.strip()) == (0, "DRIFT")


def test_native_cut_required_absence_cannot_be_skipped(tmp_path: Path) -> None:
    retired = tmp_path / "retired-file"
    assert (invoke("--absent", retired).returncode, invoke("--absent", retired).stdout.strip()) == (0, "MATCH")
    retired.write_text("obsolete")
    assert (invoke("--absent", retired).returncode, invoke("--absent", retired).stdout.strip()) == (0, "DRIFT")
    retired.unlink()
    retired.symlink_to(tmp_path / "elsewhere")
    result = invoke("--absent", retired)
    assert result.returncode != 0 and "UNKNOWN" in result.stderr


@pytest.mark.parametrize("owner", ("claude", "finance", "supply-chain", "x-reality", "chat-ingress", "browserless"))
def test_six_consumer_owners_never_restart_on_matching_source(owner: str) -> None:
    tasks = (ROOT / "consumers" / owner / "Taskfile.yml").read_text()
    prefix = ("consumer:browserless:provider-carrier" if owner == "browserless"
              else "consumer:" + owner)
    assert "  " + prefix + ":classify:" in tasks
    assert "  " + prefix + ":sourcecut:" in tasks
    assert "  " + prefix + ":materialize:" in tasks
    assert "  " + prefix + ":converge:" in tasks
    classifier = tasks.split("  " + prefix + ":classify:", 1)[1].split(
        "  " + prefix + ":sourcecut:", 1
    )[0]
    status = tasks.split("  " + prefix + ":sourcecut:", 1)[1].split(
        "  " + prefix + ":materialize:", 1
    )[0]
    materialize = tasks.split("  " + prefix + ":materialize:", 1)[1].split(
        "  " + prefix + ":start:" if owner != "browserless" else
        "  " + prefix + ":ready:", 1
    )[0]
    rest = tasks.split("  " + prefix + ":converge:", 1)[1]
    boundary = re.search(r"(?m)^  [a-zA-Z0-9:._-]+:\s*$", rest)
    convergence = rest[:boundary.start()] if boundary else rest
    assert "scripts/native-sourcecut.py" in classifier
    assert "--file " in classifier
    assert not any(x in classifier for x in ("curl ", "dig ", "systemctl restart "))
    assert "test \"$verdict\" = MATCH" in status
    assert "status:" in materialize and "task " + prefix + ":sourcecut" in materialize
    assert "task --silent " + prefix + ":classify" in materialize
    assert "test \"$verdict\" = DRIFT" in materialize
    assert materialize.index("task --silent " + prefix + ":classify") < materialize.index("install -")
    assert "MATCH)" in convergence and "DRIFT)" in convergence
    assert "task --silent " + prefix + ":materialize" in convergence
    assert convergence.index("MATCH)") < convergence.index("DRIFT)")
    assert "systemctl restart network-v2-gluetun-owned" not in convergence
    if owner != "browserless":
        assert convergence.index("systemctl start") < convergence.index("systemctl restart")


@pytest.mark.parametrize("owner,required", (
    ("finance", ("--glob \"consumers/finance/config/*-authority.json\"", "--absent /etc/network-v2/finance/provider-endpoints.json")),
    ("supply-chain", ("--absent /etc/network-v2/supply-chain/provider-endpoints.json", "--absent /etc/systemd/system/docker.service.d/ordivon-preservation-vpn-proxy.conf")),
    ("x-reality", ("--absent /usr/local/libexec/network-v2/x-reality-fault-smoke",)),
    ("browserless", ("m4-owned-mode.selected", "systemctl show network-v2-gluetun-owned.service --property=ActiveState --value", "test \"$gluetun_state\" != inactive")),
))
def test_consumer_retired_artifacts_and_single_provider_are_sourcecut_bound(
    owner: str, required: tuple[str, ...],
) -> None:
    tasks = (ROOT / "consumers" / owner / "Taskfile.yml").read_text()
    for pattern in required:
        assert pattern in tasks, (owner, pattern)


def test_native_cut_rejects_existing_nested_parent_symlink(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.write_bytes(b"pinned")
    parent = tmp_path / "actual"
    (parent / "child").mkdir(parents=True)
    (tmp_path / "foreign").symlink_to(parent, target_is_directory=True)
    result = invoke("--file", src, tmp_path / "foreign" / "child" / "installed")
    assert result.returncode != 0 and "UNKNOWN" in result.stderr


def test_native_cut_rejects_symlink_ancestor_for_existing_installed_file(tmp_path: Path) -> None:
    src = tmp_path / "source"
    src.write_bytes(b"pinned")
    actual = tmp_path / "real-dir"
    actual.mkdir()
    (actual / "installed").write_bytes(b"pinned")
    (tmp_path / "alias").symlink_to(actual, target_is_directory=True)
    result = invoke("--file", src, tmp_path / "alias" / "installed")
    assert result.returncode != 0 and "UNKNOWN" in result.stderr


def test_native_cut_detects_permission_mode_drift_even_when_bytes_match(tmp_path: Path) -> None:
    src = tmp_path / "s"
    dst = tmp_path / "d"
    src.write_bytes(b"same")
    dst.write_bytes(b"same")
    dst.chmod(0o600)
    result = invoke("--file", src, dst)
    assert (result.returncode, result.stdout.strip()) == (0, "DRIFT")
    dst.chmod(0o644)
    result = invoke("--file", src, dst)
    assert (result.returncode, result.stdout.strip()) == (0, "MATCH")
    # Explicit executable destination, regardless of the source checkout mode.
    result = invoke("--file", src, dst, "--mode", dst, "0755")
    assert (result.returncode, result.stdout.strip()) == (0, "DRIFT")
    dst.chmod(0o755)
    result = invoke("--file", src, dst, "--mode", dst, "0755")
    assert (result.returncode, result.stdout.strip()) == (0, "MATCH")


@pytest.mark.parametrize("owner,required", (
    ("claude", ("verify", "stop")),
    ("finance", ("verify", "stop")),
    ("supply-chain", ("docker-rebind", "verify", "stop")),
    ("x-reality", ("verify", "stop")),
    ("chat-ingress", ("verify", "stop")),
    ("browserless", ("provider-carrier:select", "provider-carrier:verify", "serial-accept")),
))
def test_preexisting_consumer_task_graph_is_preserved(owner: str, required: tuple[str, ...]) -> None:
    tasks = (ROOT / "consumers" / owner / "Taskfile.yml").read_text()
    for suffix in required:
        if owner == "browserless" and suffix == "serial-accept":
            task = "consumer:browserless:serial-accept"
        else:
            task = "consumer:" + owner + ":" + suffix
        assert "\n  " + task + ":\n" in tasks, task


def test_supply_chain_materialize_must_not_run_effectful_provider_dep_before_own_sourcecut() -> None:
    tasks = (ROOT / "consumers" / "supply-chain" / "Taskfile.yml").read_text()
    materialize = tasks.split("  consumer:supply-chain:materialize:\n", 1)[1].split(
        "  consumer:supply-chain:start:\n", 1)[0]
    pre = materialize.split("    cmds:\n", 1)[0]
    assert "consumer:browserless:provider-carrier:materialize" not in pre
    assert "task: consumer:browserless:provider-carrier:materialize" in materialize
    assert materialize.index("task: consumer:browserless:provider-carrier:materialize") > materialize.index(
        'test "$verdict" = DRIFT'
    )


def test_browserless_sourcecut_is_composition_of_own_and_shared_sourcecuts() -> None:
    tasks = (ROOT / "consumers" / "browserless" / "Taskfile.yml").read_text()
    classify = tasks.split("  consumer:browserless:provider-carrier:classify:\n", 1)[1].split(
        "  consumer:browserless:provider-carrier:sourcecut:\n", 1)[0]
    assert "substrate:shared-egress:classify" in classify
    assert "local_verdict" in classify and "shared_verdict" in classify


def test_browserless_selected_mode_requires_inactive_legacy_provider_units() -> None:
    tasks = (ROOT / "consumers" / "browserless" / "Taskfile.yml").read_text()
    classifier = tasks.split("  consumer:browserless:provider-carrier:classify:\n", 1)[1].split(
        "  consumer:browserless:provider-carrier:sourcecut:\n", 1
    )[0]
    assert 'systemctl show "$unit" --property=ActiveState --value' in classifier
    assert 'test "$observed" != inactive' in classifier
    assert "UNKNOWN: legacy carrier not proven inactive" in classifier
