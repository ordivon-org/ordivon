"""Exercise the qualification hook through real pytest subprocesses."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# Independent fixture names: the qualified contract is deliberately explicit.
RECOVERY = "tests/test_pgbackrest_native_recovery_contract.py"
RETENTION = "tests/test_pgbackrest_native_retention_contract.py"
RECOVERY_CASE = "test_exact_backup_status_and_required_wal_are_separate_predicates"
RETENTION_CASE = "test_two_full_generations_retain_seven_exact_recovery_points"


def run_fixture(tmp_path, scenario, *, qualified=True):
    tests = tmp_path / "tests"
    tests.mkdir()
    first = f"class NativeBackupRecoveryContract(unittest.TestCase):\n    def {RECOVERY_CASE}(self):\n        pass\n"
    second = f"class NativeBackupRetentionContract(unittest.TestCase):\n    def {RETENTION_CASE}(self):\n        pass\n"
    args = [RECOVERY, RETENTION]
    if scenario == "skip":
        first = "@unittest.skip('native prerequisite missing')\n" + first
    elif scenario == "xfail":
        first = first.replace("        pass", "        pytest.xfail('known issue')")
    elif scenario == "xpass":
        first = "@pytest.mark.xfail(strict=False)\n" + first
    elif scenario == "setup":
        first = first.replace("    def test_", "    def setUp(self):\n        raise RuntimeError('setup failed')\n    def test_", 1)
    elif scenario == "teardown":
        first = first.replace("    def test_", "    def tearDown(self):\n        raise RuntimeError('teardown failed')\n    def test_", 1)
    elif scenario == "missing":
        args = [RECOVERY]
    elif scenario == "deselect":
        args += ["-k", RECOVERY_CASE]
    elif scenario == "collect-only":
        args += ["--collect-only"]
    elif scenario == "substitute":
        second = second.replace(RETENTION_CASE, "test_unrelated")
    elif scenario == "extra":
        second += "\ndef test_extra():\n    pass\n"
    elif scenario == "duplicate":
        (tmp_path / "conftest.py").write_text(
            "def pytest_collection_modifyitems(items):\n    items.append(items[0])\n"
        )
    elif scenario == "fail":
        first = first.replace("        pass", "        self.fail('assertion failed')")
    header = "import unittest\nimport pytest\n"
    (tmp_path / RECOVERY).write_text(header + first)
    (tmp_path / RETENTION).write_text(header + second)
    env = dict(os.environ)
    for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"):
        env.pop(key, None)
    env.update(PYTHONPATH=str(ROOT), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    plugin = ["-p", "workstation.backup_test_qualification"] if qualified else []
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-o", "addopts=", *plugin, *args],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15, check=False,
    )


def test_native_exact_obligations_pass(tmp_path):
    result = run_fixture(tmp_path, "pass")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BACKUP_QUALIFICATION_COMPLETE" in result.stdout


@pytest.mark.parametrize("scenario", [
    "skip", "xfail", "xpass", "missing", "deselect", "collect-only",
    "substitute", "extra", "duplicate", "setup", "teardown", "fail",
])
def test_native_incomplete_or_failed_session_is_rejected(tmp_path, scenario):
    result = run_fixture(tmp_path, scenario)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "BACKUP_QUALIFICATION_COMPLETE" not in result.stdout
    assert "BACKUP_QUALIFICATION_INCOMPLETE" in result.stdout


@pytest.mark.parametrize("scenario", ["skip", "xfail", "xpass", "missing", "collect-only"])
def test_ordinary_runner_can_exit_zero_without_complete_obligation(tmp_path, scenario):
    result = run_fixture(tmp_path, scenario, qualified=False)
    assert result.returncode == 0, result.stdout + result.stderr


def run_task_fixture(tmp_path, report, *, runner_status=0):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("native task shell is unavailable")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    capture = tmp_path / "invocation.json"
    fake = bin_dir / "uv"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['TEST_CAPTURE']).write_text(json.dumps({"
        "'args': sys.argv[1:], 'env': {k: os.environ.get(k) for k in "
        "('PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD', "
        "'ORDIVON_TEST_NATIVE_BACKUP_CHAIN', 'ORDIVON_TEST_NATIVE_BACKUP_RETENTION')}}))\n"
        "sys.exit(int(os.environ['TEST_EXIT']))\n"
    )
    fake.chmod(0o755)
    task = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]["backup:native-verify"]["run"]
    env = dict(os.environ)
    env.update(
        PATH=str(bin_dir) + os.pathsep + env.get("PATH", ""),
        TEST_CAPTURE=str(capture),
        TEST_EXIT=str(runner_status),
        PYTEST_ADDOPTS="--collect-only -k nonexistent",
        PYTEST_PLUGINS="nonexistent",
        ORDIVON_NATIVE_BACKUP_JUNIT=str(report),
    )
    result = subprocess.run(
        [bash, "-c", task], cwd=ROOT, env=env, capture_output=True,
        text=True, timeout=15, check=False,
    )
    return result, capture


def test_task_invokes_native_runner_without_inherited_selection(tmp_path):
    report = tmp_path / "fresh.xml"
    result, capture = run_task_fixture(tmp_path, report, runner_status=41)
    assert result.returncode == 41, result.stdout + result.stderr
    observed = json.loads(capture.read_text())
    assert observed["args"] == [
        "run", "--locked", "python", "-m", "pytest", "-o", "addopts=",
        "-p", "workstation.backup_test_qualification", f"--junitxml={report}",
        RECOVERY, RETENTION,
    ]
    assert observed["env"] == {
        "PYTEST_ADDOPTS": None,
        "PYTEST_PLUGINS": None,
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "ORDIVON_TEST_NATIVE_BACKUP_CHAIN": "1",
        "ORDIVON_TEST_NATIVE_BACKUP_RETENTION": "1",
    }


@pytest.mark.parametrize("kind", ["existing", "dangling"])
def test_task_refuses_preexisting_report_before_runner(tmp_path, kind):
    report = tmp_path / "report.xml"
    if kind == "existing":
        report.write_bytes(b"previous-attempt")
    else:
        try:
            report.symlink_to(tmp_path / "missing")
        except OSError:
            pytest.skip("native symlink creation unavailable")
    result, capture = run_task_fixture(tmp_path, report)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "BACKUP_QUALIFICATION_REPORT_EXISTS" in result.stderr
    assert not capture.exists()
    if kind == "existing":
        assert report.read_bytes() == b"previous-attempt"
    else:
        assert report.is_symlink() and not report.exists()
