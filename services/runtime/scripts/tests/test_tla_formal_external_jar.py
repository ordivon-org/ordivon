"""Cold-workspace contract tests for the pinned TLA+ checker.

No network or host-global installs. A fake java process observes the selected jar
path; real TLC checking stays in the owner-native formal suite.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tla-formal"
ENV_JAR = "ORDIVON_TLA_TOOLS_JAR"


@pytest.fixture
def toolchain(tmp_path: Path):
    root = tmp_path / "runtime"
    scripts = root / "scripts"
    formal = root / "formal"
    scripts.mkdir(parents=True)
    formal.mkdir()
    script = scripts / "tla-formal"
    shutil.copyfile(SCRIPT, script)
    payload = b"tla-locked-test-carrier"
    external = tmp_path / "external tools.jar"
    external.write_bytes(payload)
    (formal / "toolchain.lock.json").write_text(json.dumps({
        "version": "fixture",
        "url": "https://invalid.example/never-fetch",
        "upstreamSha1": hashlib.sha1(payload).hexdigest(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "cacheRelativePath": "target/formal-tools/pinned.jar",
    }), encoding="utf-8")
    (formal / "RuntimeDispatchR1.tla").write_text("---- MODULE RuntimeDispatchR1 ----\n====", encoding="utf-8")
    (formal / "RuntimeDispatchR1.cfg").write_text("SPECIFICATION Spec\n", encoding="utf-8")
    binary = tmp_path / "bin"
    binary.mkdir()
    fake_java = binary / "java"
    fake_java.write_text('#!/bin/sh\nprintf "%s\\n" "$@" >> "$JAVA_ARGS_LOG"\n', encoding="utf-8")
    fake_java.chmod(0o755)
    env = {
        **os.environ,
        "PATH": str(binary) + os.pathsep + os.environ["PATH"],
        "JAVA_ARGS_LOG": str(tmp_path / "java-args.log"),
    }
    env.pop(ENV_JAR, None)
    return script, external, root / "target/formal-tools/pinned.jar", env


def invoke(toolchain, command="verify", jar=None):
    script, _, _, env = toolchain
    env = dict(env)
    if jar is not None:
        env[ENV_JAR] = str(jar)
    return subprocess.run(["bash", str(script), command], env=env, capture_output=True, text=True, timeout=15)


def test_external_digest_locked_jar_works_without_workspace_cache(toolchain):
    _, external, cache, _ = toolchain
    assert not cache.exists()
    result = invoke(toolchain, jar=external)
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout
    assert not cache.exists()


def test_external_check_invokes_java_using_exact_path(toolchain):
    _, external, _, env = toolchain
    result = invoke(toolchain, command="check", jar=external)
    assert result.returncode == 0, result.stderr
    observed = Path(env["JAVA_ARGS_LOG"]).read_text(encoding="utf-8")
    assert observed.count(str(external)) == 2
    assert "tla2sany.SANY" in observed
    assert "tlc2.TLC" in observed


def test_digest_mismatch_fails_closed(toolchain, tmp_path):
    _, external, _, _ = toolchain
    bad = tmp_path / "tampered.jar"
    bad.write_bytes(external.read_bytes() + b"-changed")
    result = invoke(toolchain, jar=bad)
    assert result.returncode != 0
    assert "digest" in result.stderr.lower() or "sha" in result.stderr.lower()


@pytest.mark.parametrize("invalid", ["relative.jar", ""])
def test_external_override_must_be_absolute_nonempty_file(toolchain, invalid):
    result = invoke(toolchain, jar=invalid)
    assert result.returncode != 0


def test_external_symlink_is_rejected(toolchain, tmp_path):
    _, external, _, _ = toolchain
    alias = tmp_path / "alias.jar"
    alias.symlink_to(external)
    assert invoke(toolchain, jar=alias).returncode != 0


def test_default_local_cache_still_works(toolchain):
    _, external, cache, _ = toolchain
    cache.parent.mkdir(parents=True)
    cache.write_bytes(external.read_bytes())
    result = invoke(toolchain)
    assert result.returncode == 0, result.stderr


def test_missing_default_cache_fails_without_network(toolchain):
    _, _, cache, env = toolchain
    assert not cache.exists()
    result = invoke(toolchain)
    assert result.returncode == 2
    assert "missing" in result.stderr.lower()
    assert not Path(env["JAVA_ARGS_LOG"]).exists()

def test_invalid_external_override_never_falls_back_to_valid_local_cache(toolchain, tmp_path):
    _, external, cache, _ = toolchain
    cache.parent.mkdir(parents=True)
    cache.write_bytes(external.read_bytes())
    invalid = tmp_path / "wrong.jar"
    invalid.write_bytes(b"incorrect")
    result = invoke(toolchain, jar=invalid)
    assert result.returncode != 0
    assert "digest mismatch" in result.stderr.lower()


def test_external_override_does_not_redirect_bootstrap_target(toolchain, tmp_path):
    _, external, cache, env = toolchain
    fake_curl = Path(env["PATH"].split(os.pathsep)[0]) / "curl"
    fake_curl.write_text(
        '#!/bin/sh\n'
        'while [ "$#" -gt 0 ]; do\n'
        '  if [ "$1" = "-o" ]; then shift; cp "$BOOTSTRAP_FIXTURE" "$1"; exit $?; fi\n'
        '  shift\n'
        'done\n'
        'exit 2\n',
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    original = external.read_bytes()
    # The fixture-driven fake curl cannot access the network.
    env["BOOTSTRAP_FIXTURE"] = str(external)
    script, _, _, _ = toolchain
    env[ENV_JAR] = str(tmp_path / "other-external.jar")
    result = subprocess.run(["bash", str(script), "bootstrap"], env=env,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert cache.read_bytes() == original
    assert external.read_bytes() == original
    assert not Path(env[ENV_JAR]).exists()
