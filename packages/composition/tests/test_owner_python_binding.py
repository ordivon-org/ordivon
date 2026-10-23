"""Consumer execution must use the interpreter declared by the owner mise.toml."""

import subprocess
import sys
from pathlib import Path


def test_uv_python_matches_mise_owner_interpreter():
    root = Path(__file__).resolve().parents[1]
    selected = subprocess.run(
        ["mise", "which", "python"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    expected = subprocess.run(
        [selected, "-c", "import sys; print('.'.join(map(str,sys.version_info[:3])))"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    observed = ".".join(map(str, sys.version_info[:3]))
    assert observed == expected, (
        f"uv consumer interpreter {observed} != owner-selected mise Python {expected}"
    )


def test_verify_binds_uv_python_before_lock_sync_and_tests():
    import tomllib

    data = tomllib.loads((Path(__file__).resolve().parents[1] / "mise.toml").read_text())
    script = data["tasks"]["verify"]["run"]
    marker = 'export UV_PYTHON="$(mise which python)"'
    assert marker in script, "native uv must bind the mise-selected owner Python"
    assert script.index(marker) < script.index("uv lock --check")
