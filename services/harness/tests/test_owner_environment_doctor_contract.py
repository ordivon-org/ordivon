"""Owner-native CDC: Harness doctor consumes current declared tool versions."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

OWNER = Path(__file__).resolve().parents[1]
SCRIPT = OWNER / "scripts/owner-environment"


def test_owner_doctor_uses_declared_versions_and_locked_sync():
    text = SCRIPT.read_text()
    assert "sync --locked --group dev --group test" in text
    assert '"$repo/mise.toml" "$repo/pyproject.toml"' in text
    assert "tomllib.loads" in text
    assert "md.version" in text


def _fake_checkout(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    shutil.copy2(SCRIPT, tmp_path / "scripts/owner-environment")
    shutil.copy2(OWNER / "mise.toml", tmp_path / "mise.toml")
    shutil.copy2(OWNER / "pyproject.toml", tmp_path / "pyproject.toml")
    # The real installed environment is the independent verifier oracle;
    # only the candidate source specification is varied.
    (tmp_path / ".venv").symlink_to(OWNER / ".venv", target_is_directory=True)
    return tmp_path


@pytest.mark.parametrize(
    ("source", "original", "replacement", "expected"),
    [
        ("mise.toml", 'python = "3.15.1"', 'python = "0.0.0"', "Harness requires Python 0.0.0"),
        ("pyproject.toml", 'ruff==0.17.2', 'ruff==0.0.0', "unexpected Ruff version"),
        ("pyproject.toml", 'pytest==9.1.1', 'pytest==0.0.0', "unexpected pytest version"),
    ],
)
def test_doctor_fails_on_declared_manifest_drift(
    tmp_path: Path, source: str, original: str, replacement: str, expected: str
):
    check = _fake_checkout(tmp_path)
    path = check / source
    before = path.read_text()
    assert before.count(original) == 1
    path.write_text(before.replace(original, replacement, 1))
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    result = subprocess.run(
        ["/usr/bin/bash", str(check / "scripts/owner-environment"), "doctor"],
        cwd=check,
        env=env,
        text=True,
        capture_output=True,
        timeout=35,
        check=False,
    )
    assert result.returncode != 0
    assert expected in result.stderr + result.stdout


def test_local_acceptance_reuses_resolved_owner_uv():
    text = (OWNER / "scripts/local-acceptance").read_text()
    assert "command -v uv" not in text
    assert '"$owner_environment" bootstrap' in text
    assert '"${MISE_BIN:-mise}" which uv' in text


def test_bootstrap_selects_owner_pinned_uv_not_ambient_path(tmp_path: Path):
    """A historical local-Main consumer requires mise, not a PATH uv shim."""
    checkout = tmp_path / "checkout"
    (checkout / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT, checkout / "scripts/owner-environment")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    selected = tmp_path / "selected-uv"
    selected.write_text(
        '#!/usr/bin/bash\nprintf "selected\n" >> "$ORDIVON_UV_PROBE"\n'
    )
    selected.chmod(0o755)
    stale = fake_bin / "uv"
    stale.write_text(
        '#!/usr/bin/bash\nprintf "stale\n" >> "$ORDIVON_UV_PROBE"\n'
    )
    stale.chmod(0o755)
    mise = fake_bin / "mise"
    mise.write_text(
        '#!/usr/bin/bash\n'
        'if [[ "$1" == which && "$2" == uv ]]; then printf "%s\n" "$ORDIVON_TEST_SELECTED_UV"; '
        'elif [[ "$1" == exec && "$2" == -- ]]; then shift 2; exec "$@"; '
        'else exit 91; fi\n'
    )
    mise.chmod(0o755)
    marker = tmp_path / "uv-selection.log"
    env = dict(os.environ)
    env.pop("UV_BIN", None)
    env.pop("MISE_BIN", None)
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '/usr/bin:/bin')}"
    env["ORDIVON_TEST_SELECTED_UV"] = str(selected)
    env["ORDIVON_UV_PROBE"] = str(marker)
    result = subprocess.run(
        ["/usr/bin/bash", str(checkout / "scripts/owner-environment"), "bootstrap"],
        env=env, cwd=checkout, text=True, capture_output=True, timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.read_text().splitlines() == ["selected"]

    env["UV_BIN"] = str(stale)
    marker.unlink()
    rejected = subprocess.run(
        ["/usr/bin/bash", str(checkout / "scripts/owner-environment"), "bootstrap"],
        env=env, cwd=checkout, text=True, capture_output=True, timeout=15,
        check=False,
    )
    assert rejected.returncode != 0, "an unpinned explicit override was accepted"
    assert not marker.exists(), "a stale uv was executed during rejected admission"


def test_real_materialized_harness_owner_doctor():
    result = subprocess.run(
        ["/usr/bin/bash", str(SCRIPT), "doctor"],
        cwd=OWNER,
        env={k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"},
        text=True,
        capture_output=True,
        timeout=35,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "owner environment doctor: valid profile=test" in result.stdout
