"""Adversarial contract tests for the actual Network Taskfile registry gate."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shlex
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "providers/surfshark/config/carrier-realizations.json"


def validate(candidate: dict) -> subprocess.CompletedProcess[str]:
    # Execute the real Taskfile jq command on in-memory input; never mutate the registry.
    line = next(
        line.strip() for line in (ROOT / "Taskfile.yml").read_text().splitlines()
        if line.strip().startswith("- jq -e ") and line.strip().endswith(REGISTRY + " >/dev/null")
    )
    argv = shlex.split(line[2:])
    argv = argv[: argv.index(REGISTRY)] + ["-"]
    return subprocess.run(
        argv, input=json.dumps(candidate), text=True, capture_output=True, cwd=ROOT,
        check=False,
    )


def baseline() -> dict:
    return json.loads((ROOT / REGISTRY).read_text())


def test_current_registry_is_accepted():
    result = validate(baseline())
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("mutation", ["second-active", "duplicate-id", "rogue-authoritative-candidate", "bad-reference"])
def test_registry_rejects_cross_record_violations(mutation: str):
    candidate = copy.deepcopy(baseline())
    if mutation == "second-active":
        second = copy.deepcopy(candidate["realizations"][0])
        second["realizationId"] = "second-active"
        candidate["realizations"].append(second)
    elif mutation == "duplicate-id":
        candidate["realizations"].append(copy.deepcopy(candidate["realizations"][0]))
    elif mutation == "rogue-authoritative-candidate":
        rogue = copy.deepcopy(candidate["realizations"][1])
        rogue["realizationId"] = "rogue-authoritative"
        rogue["productionAuthority"] = True
        candidate["realizations"].append(rogue)
    elif mutation == "bad-reference":
        candidate["realizations"][1]["clientIdentityRef"] = "other-client-identity"
    result = validate(candidate)
    assert result.returncode != 0, f"{mutation} was accepted despite violating single-session source contract"
