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
    classifier = section(taskfile, "core:classify")
    install = section(taskfile, "core:install")
    activation = section(taskfile, "core:converge")
    check = section(taskfile, "core:verify")
    converge = section(taskfile, "core:converge")

    assert "status:\n      - task core:sourcecut" in install
    assert "status:\n      - task core:verify" not in install
    # Core, Mobile and Shared Egress use the same semantic distinction:
    # binary Task status may skip on MATCH, but only a proved DRIFT may mutate.
    assert "task --silent core:classify" in source
    assert 'test "$verdict" = MATCH' in source
    assert classifier.count("compare ") >= 11
    assert "compare config/prometheus/consumer.rules.yml" in classifier
    assert "UNKNOWN" in classifier and "DRIFT" in classifier and "MATCH" in classifier
    assert "comparison_rc" in classifier and "enabled()" in classifier
    assert "NeedDaemonReload" in classifier and "systemctl show" in classifier
    assert "task --silent core:classify" in install
    assert 'test "$verdict" = DRIFT' in install
    assert install.index("task --silent core:classify") < install.index("task: core:validate")
    for forbidden in ("curl ", "dig ", "systemctl start ", "systemctl restart ", "--check-loaded-prometheus",
                      "http://", "https://", "core:verify"):
        assert forbidden not in classifier, "unexpected external/active probe in Core classifier: " + forbidden
    for location, owner in (
        (ROOT / "consumers/mobile-tailnet-exit/Taskfile.yml", "consumer:mobile-tailnet-exit"),
        (ROOT / "substrates/shared-egress/Taskfile.yml", "substrate:shared-egress"),
    ):
        other = location.read_text()
        state = section(other, owner + ":classify")
        materialize = section(other, owner + ":materialize")
        source_check = section(other, owner + ":sourcecut")
        assert "UNKNOWN" in state and "MATCH" in state and "DRIFT" in state
        assert "cmp -s" in state and "comparison_rc" in state
        assert "task --silent " + owner + ":classify" in materialize
        assert ('test "$verdict" = DRIFT' in materialize or "DRIFT)" in materialize)
        assert "task --silent " + owner + ":classify" in source_check
        assert 'test "$verdict" = MATCH' in source_check
        assert materialize.index("task --silent " + owner + ":classify") < materialize.index("install -")
        for no_network in ("curl ", "dig ", "systemctl restart ", "systemctl start "):
            assert no_network not in state, (owner, no_network)
    assert "systemctl restart network-v2-r0.target" in install  # only on actual drift
    assert "task: core:install" in activation
    assert "systemctl start network-v2-r0.target" in activation
    assert "systemctl restart " not in activation
    assert "deps: [core:sourcecut]" in check
    assert "--check-loaded-prometheus" in check
    assert has_exact_https_origin_probe(check)
    steps = ("task: core:validate", "task: core:install", "systemctl start network-v2-r0.target", "task: core:verify")
    assert [converge.index(step) for step in steps] == sorted(converge.index(step) for step in steps)
    return {"localCompareCalls": classifier.count("compare "), "consumerCount": 3,
            "convergeSteps": list(steps)}


def prove() -> dict:
    admission = admit_implementation()
    # The trivalent refinement is necessary: an unreadable file, a failed
    # systemd query, or a transport failure is not proof of configuration drift.
    MATCH, DRIFT, UNKNOWN = 0, 1, 2
    sourcecut = z3.Int("sourcecut_state")
    active, external = z3.Bools("active external")
    install = sourcecut == DRIFT
    start = z3.Not(active)
    verified = z3.And(sourcecut == MATCH, active, external)
    valid = z3.Or(sourcecut == MATCH, sourcecut == DRIFT, sourcecut == UNKNOWN)
    statements = {
        "source_match_implies_no_install": z3.Implies(sourcecut == MATCH, z3.Not(install)),
        "source_unknown_cannot_trigger_install": z3.Implies(sourcecut == UNKNOWN, z3.Not(install)),
        "source_unknown_cannot_trigger_restart": z3.Implies(sourcecut == UNKNOWN, z3.Not(install)),
        "external_failure_cannot_trigger_install": z3.Implies(
            z3.And(sourcecut == MATCH, z3.Not(external)), z3.Not(install)),
        "source_drift_requires_install": z3.Implies(sourcecut == DRIFT, install),
        "dead_service_matching_source_requires_only_activation": z3.Implies(
            z3.And(sourcecut == MATCH, z3.Not(active)), z3.And(z3.Not(install), start)),
        "healthy_running_source_unchanged": z3.Implies(
            z3.And(sourcecut == MATCH, active), z3.And(z3.Not(install), z3.Not(start))),
        "live_success_is_independent_check": z3.Implies(
            verified, z3.And(sourcecut == MATCH, active, external)),
    }
    for label, claim in statements.items():
        solver = z3.Solver()
        solver.set(timeout=8000)
        solver.add(valid, z3.Not(claim))
        assert solver.check() == z3.unsat, "proof failed: " + label

    # Actual historical bug: Boolean Task status conflated any nonzero
    # observation (including UNKNOWN) with DRIFT and admitted writes.
    legacy_install = sourcecut != MATCH
    mutant = z3.Solver()
    mutant.add(valid, sourcecut == UNKNOWN, legacy_install)
    assert mutant.check() == z3.sat, "UNKNOWN-as-DRIFT regression not detected"
    # Independent older regression: external failure mistaken for install.
    legacy_network = z3.Not(z3.And(sourcecut == MATCH, active, external))
    network_mutant = z3.Solver()
    network_mutant.add(valid, sourcecut == MATCH, active, z3.Not(external), legacy_network)
    assert network_mutant.check() == z3.sat

    return {
        "kind": "ordivon.network.core-sourcecut-convergence-proof",
        "standing": "SOURCE_BOUND_SYMBOLIC_SELECTION_PROVED",
        "z3Version": z3.get_version_string(),
        "provedProperties": list(statements),
        "negativeControls": [
            "Boolean SourceCut fail means install even when observation UNKNOWN",
            "external endpoint failure triggers legacy installer with matching SourceCut",
        ],
        "sourceAdmission": admission,
        "sourcecutStates": ["MATCH", "DRIFT", "UNKNOWN"],
        "excluded": ["systemd start success", "external Internet availability",
                     "multi-file atomic release under crash", "loaded byte parity",
                     "actual application traffic and device-origin exit/DNS evidence"],
    }


if __name__ == "__main__":
    print(json.dumps(prove(), sort_keys=True))
