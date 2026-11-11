"""The Host's advertised default focused test must be a real native consumer."""
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_focused_default_points_at_a_real_test_file_and_readme_agrees() -> None:
    tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
    runner = tasks["test:focused"]["run"]
    match = re.search(r"HOST_PYTEST_NODE:-([^}]+)", runner)
    assert match is not None
    default = match.group(1)
    assert (ROOT / default).is_file(), f"default focused pytest target is missing: {default}"
    assert default in (ROOT / "README.md").read_text()
