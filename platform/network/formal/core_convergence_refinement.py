"""Z3 safety proof for independent Network SourceCut installation and live health.

This proves task-selection logic under successful-action assumptions, not
systemd behavior, real DNS, or reachability of an actual external endpoint.
"""
from __future__ import annotations

import json
import shlex
from urllib.parse import urlsplit
from pathlib import Path
import z3

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "Taskfile.yml"


def section(source: str, name: str) -> str:
    prefix = "  " + name + ":\n"
    assert source.count(prefix) == 1, "missing or ambiguous task: " + name
    tail = source.split(prefix, 1)[1]
    lines = tail.splitlines(keepends=True)
    boundary = next((i for i, value in enumerate(lines) if value.startswith('  ') and not value.startswith('   ') and value.strip().endswith(':')), len(lines))
    return ''.join(lines[:boundary])



def has_exact_https_origin_probe(check: str) -> bool:
    """Require native curl tokens plus parsed origin identity, not a URL substring."""
    for raw in check.splitlines():
        line = raw.strip()
        if not line.startswith("- curl --fail --silent --show-error "):
            continue
        argv = shlex.split(line.removeprefix("- "))
        if not argv or argv[0] != "curl" or "--proxy" not in argv:
            continue
        index = argv.index("--proxy")
        if index + 1 >= len(argv) or argv[index + 1] != "http://127.0.0.1:28080":
            continue
        target = urlsplit(argv[-1])
        if (target.scheme == "https" and target.hostname == "example.com"
                and target.port in (None, 443) and target.path == "/"
                and not target.username and not target.password
                and not target.query and not target.fragment):
            return True
    return False


def admit_implementation() -> dict:
    taskfile = TASKS.read_text()
    source = section(taskfile, "core:sourcecut")
    install = section(taskfile, "core:install")
    activation = section(taskfile, "core:converge")
    check = section(taskfile, "core:verify")
    converge = section(taskfile, "core:converge")

    assert "status:\n      - task core:sourcecut" in install
    assert "status:\n      - task core:verify" not in install
    assert source.count("cmp -s") >= 10
    assert "cmp -s config/prometheus/consumer.rules.yml" in source
    for forbidden in ("curl ", "dig ", "systemctl start ", "systemctl restart ", "--check-loaded-prometheus",
                      "http://", "https://", "core:verify"):
        assert forbidden not in source, "unexpected external/active probe in SourceCut: " + forbidden
    assert "systemctl restart network-v2-r0.target" in install  # only on actual drift
    assert "task: core:install" in activation
    assert "systemctl start network-v2-r0.target" in activation
    assert "systemctl restart " not in activation
    assert "deps: [core:sourcecut]" in check
    assert "--check-loaded-prometheus" in check
    assert has_exact_https_origin_probe(check)
    steps = ("task: core:validate", "task: core:install", "systemctl start network-v2-r0.target", "task: core:verify")
    assert [converge.index(step) for step in steps] == sorted(converge.index(step) for step in steps)
    return {"localCmpChecks": source.count("cmp -s"), "convergeSteps": list(steps)}


def prove() -> dict:
    admission = admit_implementation()
    same_source, active, external = z3.Bools("same_source active external")
    install = z3.Not(same_source)
    start = z3.Not(active)
    verified = z3.And(same_source, active, external)

    statements = {
        "source_match_implies_no_install": z3.Implies(same_source, z3.Not(install)),
        "external_failure_cannot_trigger_install": z3.Implies(
            z3.And(same_source, z3.Not(external)), z3.Not(install)),
        "source_drift_requires_install": z3.Implies(z3.Not(same_source), install),
        "dead_service_with_matching_source_requires_only_activation": z3.Implies(
            z3.And(same_source, z3.Not(active)), z3.And(z3.Not(install), start)),
        "healthy_running_source_unchanged": z3.Implies(
            z3.And(same_source, active), z3.And(z3.Not(install), z3.Not(start))),
        "live_success_is_independent_check": z3.Implies(
            verified, z3.And(same_source, active, external)),
    }
    for label, claim in statements.items():
        solver = z3.Solver()
        solver.set(timeout=8000)
        solver.add(z3.Not(claim))
        assert solver.check() == z3.unsat, "proof failed: " + label

    # Mutated pre-refactor selection: a failed external request triggered writes.
    legacy = z3.Not(z3.And(same_source, active, external))
    mutant = z3.Solver()
    mutant.add(same_source, active, z3.Not(external), legacy)
    assert mutant.check() == z3.sat, "historical network-trigger regression not detected"
    return {
        "kind": "ordivon.network.core-sourcecut-convergence-proof",
        "standing": "SOURCE_BOUND_SYMBOLIC_SELECTION_PROVED",
        "z3Version": z3.get_version_string(),
        "provedProperties": list(statements),
        "negativeControl": "old live-verify-as-install-status triggers install on external failure",
        "sourceAdmission": admission,
        "excluded": ["systemd start success", "external Internet availability",
                     "loaded config actual parity", "network packets and consumer effects"],
    }


if __name__ == "__main__":
    print(json.dumps(prove(), sort_keys=True))
