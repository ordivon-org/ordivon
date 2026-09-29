from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_docs  # noqa: E402
from ordivon_harness.cli import build_parser  # noqa: E402


def test_canonical_documented_harness_commands_exist() -> None:
    assert check_docs.validate_documented_cli_commands() == []


def test_unknown_documented_command_is_detectable() -> None:
    assert check_docs.extract_documented_cli_commands(
        "```bash\nordivon-harness --state-root /tmp/state capabilities\n```\n"
    ) == {"capabilities"}
    assert "capabilities" not in check_docs.cli_subcommands()


@pytest.mark.parametrize(
    "command",
    ["doctor", "status", "inspect", "explain", "run", "resume", "store-init"],
)
def test_quickstart_command_help_is_parseable(command: str) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as result:
        parser.parse_args([command, "--help"])
    assert result.value.code == 0
