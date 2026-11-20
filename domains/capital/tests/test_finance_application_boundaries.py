"""CLI composition must not creep back into Risk/Portfolio domain computations."""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/ordivon_capital"
APPLICATIONS = ROOT / "scripts/applications"
DOMAIN_AND_CLI = {
    "portfolio/paper_contribution_plan.py": "paper_contribution.py",
    "portfolio/paper_close_performance.py": "paper_performance.py",
    "risk/paper_close_risk.py": "paper_risk.py",
}


@pytest.mark.parametrize("domain_path,cli_path", DOMAIN_AND_CLI.items())
def test_paper_domain_math_does_not_own_accounting_cli(domain_path: str, cli_path: str):
    source = (SRC / domain_path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]
    assert not any("accounting.postgres_paper_close" in module for module in imports)
    assert not any(
        isinstance(node, ast.FunctionDef) and node.name == "main"
        for node in tree.body
    )
    composition = (APPLICATIONS / cli_path).read_text(encoding="utf-8")
    assert "from ordivon_capital.accounting.postgres_paper_close import" in composition
    assert "close_session(" not in composition


@pytest.mark.parametrize("cli_path", DOMAIN_AND_CLI.values())
def test_existing_read_only_paper_cli_help_is_available(cli_path: str):
    result = subprocess.run(
        [sys.executable, str(APPLICATIONS / cli_path), "--help"],
        cwd=ROOT,
        env=os.environ | {"PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--help" in result.stdout


@pytest.mark.parametrize("domain_path,cli_path", DOMAIN_AND_CLI.items())
def test_retired_module_cli_fails_explicitly_instead_of_silent_success(
    domain_path: str, cli_path: str
):
    module = "ordivon_capital." + domain_path.removesuffix(".py").replace("/", ".")
    result = subprocess.run(
        [sys.executable, "-m", module],
        cwd=ROOT,
        env=os.environ | {"PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert f"CLI moved to scripts/applications/{cli_path}" in result.stderr
    assert result.stdout == ""
