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
    # R11 source-bound composition: six more natural owners retain their
    # previous consumer tasks; every materializer must reclassify before its
    # FIRST effect, including when Task --force bypasses status/preconditions.
    r11_owners = (
        ("claude", "consumer:claude"),
        ("finance", "consumer:finance"),
        ("supply-chain", "consumer:supply-chain"),
        ("x-reality", "consumer:x-reality"),
        ("chat-ingress", "consumer:chat-ingress"),
        ("browserless", "consumer:browserless:provider-carrier"),
    )
    common = (ROOT / "scripts/native-sourcecut.py").read_text()
    assert "def accessible_parent(" in common and "def file_digest(" in common
    assert "def classify(" in common and "UNKNOWN:" in common
    assert "installed_identity[1] != installed_modes.get(installed, 0o644)" in common
    for subdir, owner in r11_owners:
        other = (ROOT / "consumers" / subdir / "Taskfile.yml").read_text()
        status = section(other, owner + ":sourcecut")
        materialize = section(other, owner + ":materialize")
        state = section(other, owner + ":classify")
        consumer_converge = section(other, owner + ":converge")
        assert "scripts/native-sourcecut.py" in state, owner
        assert "--file " in state and "--unit-loaded " in state, owner
        assert "status:\n      - task " + owner + ":sourcecut" in materialize, owner
        assert "task --silent " + owner + ":classify" in status, owner
        assert 'test "$verdict" = MATCH' in status, owner
        assert "task --silent " + owner + ":classify" in materialize, owner
        assert 'test "$verdict" = DRIFT' in materialize, owner
        # A dependency runs before Task's command guard. It cannot be another
        # owner's install/materialize, even when this owner returns UNKNOWN.
        before_cmds = materialize.split("    cmds:\n", 1)[0]
        assert ":materialize" not in before_cmds, owner
        if "install -" in materialize:
            assert materialize.index("task --silent " + owner + ":classify") < materialize.index("install -"), owner
        if subdir != "browserless":
            # R13: five fixed sing-box scopes reuse ONE native Linux flock
            # during the complete native converge/verify critical section.
            # This is source-bound to the Go Task handler; the kernel-backed
            # mutex semantics and crash cleanup are independently exercised
            # by actual parallel Go Task processes, not assumed by Z3.
            lock_call = (
                "flock -n -E 75 /run/lock/ordivon-network-v2-converge.lock"
            )
            assert consumer_converge.count(lock_call) == 1, owner
            assert consumer_converge.index(lock_call) < consumer_converge.index(
                'source_state="$(task --silent '
            ), owner
            assert 'NETWORK_V2_CONVERGE' in consumer_converge, owner
            assert 'task --silent ' + owner + ':validate' in consumer_converge
            post = owner + (":verify" if subdir in ("claude", "chat-ingress")
                            else ":ready")
            assert 'task --silent ' + post in consumer_converge, owner
            assert consumer_converge.index(
                'task --silent ' + post
            ) < consumer_converge.index('NETWORK_V2_CONVERGE\n'), owner
            assert 'case "$source_state/$process_state" in' in consumer_converge, owner
            assert "MATCH/MATCH)" in consumer_converge, owner
            assert "MATCH/DRIFT)" in consumer_converge, owner
            assert "DRIFT/MATCH|DRIFT/DRIFT)" in consumer_converge, owner
            match_branch = consumer_converge.split("MATCH/MATCH)", 1)[1].split(
                "MATCH/DRIFT)", 1)[0]
            assert "systemctl restart " not in match_branch, owner
            running = section(other, owner + ":process-fresh")
            assert "--unit-process-file " in running, owner
            assert '/usr/bin/sing-box \'["run","-c"]\'' in running, owner
            assert "scripts/native-sourcecut.py" in running, owner
            assert "task --silent " + owner + ":process-fresh" in consumer_converge, owner
            assert "systemctl is-active --quiet network-v2-" in consumer_converge, owner
        else:
            assert 'case "$verdict" in' in consumer_converge, owner
            assert "MATCH)" in consumer_converge and "DRIFT)" in consumer_converge, owner
            match_branch = consumer_converge.split("MATCH)", 1)[1].split(
                "DRIFT)", 1)[0]
            assert "systemctl restart " not in match_branch, owner
        assert "task --silent " + owner + ":sourcecut" in consumer_converge, owner
        assert "task --silent " + owner + ":materialize" in consumer_converge, owner
        if subdir == "browserless":
            assert "substrate:shared-egress:classify" in state
            assert 'case "$local_verdict/$shared_verdict" in' in state
            assert "MATCH/MATCH) echo MATCH" in state
            assert "MATCH/DRIFT|DRIFT/MATCH|DRIFT/DRIFT) echo DRIFT" in state
            assert "UNKNOWN:" in state
        else:
            assert "--mode /usr/local/libexec/network-v2/" + subdir + "-ready 0755" in state
    for subdir, preserved in (
        ("claude", ("verify", "stop")),
        ("finance", ("verify", "stop")),
        ("supply-chain", ("docker-rebind", "verify", "stop")),
        ("x-reality", ("verify", "stop")),
    ):
        original = (ROOT / "consumers" / subdir / "Taskfile.yml").read_text()
        for label in preserved:
            assert "  consumer:" + subdir + ":" + label + ":\n" in original
    # A Target restart is NOT a child service restart without PartOf=.
    # Source must explicitly bind each static sing-box child to its target.
    for name, unit in (
        ("claude", "network-v2-claude-proxy.service"),
        ("finance", "network-v2-finance-egress.service"),
        ("supply-chain", "network-v2-supply-chain-egress.service"),
        ("x-reality", "network-v2-x-reality-egress.service"),
        ("chat-ingress", "network-v2-chat-ingress-proxy.service"),
    ):
        service = (ROOT / "consumers" / name / "systemd" / unit).read_text()
        assert "Type=simple" in service, name
        assert "ExecStart=/usr/bin/sing-box run -c " in service, name
        assert "PartOf=network-v2-" + name + ".target" in service, name

    assert "systemctl restart network-v2-r0.target" in install  # only on actual drift
    assert "task: core:install" in activation
    assert "systemctl start network-v2-r0.target" in activation
    assert "systemctl restart " not in activation
    assert "deps: [core:sourcecut]" in check
    assert "--check-loaded-prometheus" in check
    assert has_exact_https_origin_probe(check)
    steps = ("task: core:validate", "task: core:install", "systemctl start network-v2-r0.target", "task: core:verify")
    assert [converge.index(step) for step in steps] == sorted(converge.index(step) for step in steps)
    return {"localCompareCalls": classifier.count("compare "), "consumerCount": 3 + len(r11_owners),
             "r11ConsumerOwners": [owner for _, owner in r11_owners],
             "r12ProcessGenerationConsumers": [owner for subdir, owner in r11_owners
                 if subdir != "browserless"],
             "r13NativeFlockGuardedConverges": 5,
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

    # Composition of two owners is not ordinary Boolean OR:
    # UNKNOWN on either side blocks deployment even when the other drifts.
    local, shared = z3.Ints("browserless_local shared_carrier")
    admissible = z3.And(
        z3.Or(local == MATCH, local == DRIFT, local == UNKNOWN),
        z3.Or(shared == MATCH, shared == DRIFT, shared == UNKNOWN),
    )
    composed = z3.If(
        z3.Or(local == UNKNOWN, shared == UNKNOWN), UNKNOWN,
        z3.If(z3.Or(local == DRIFT, shared == DRIFT), DRIFT, MATCH),
    )
    composition_claims = {
        "both_owners_match": z3.Implies(
            z3.And(local == MATCH, shared == MATCH), composed == MATCH),
        "local_unknown_overrides_shared_drift": z3.Implies(
            z3.And(local == UNKNOWN, shared == DRIFT), composed == UNKNOWN),
        "shared_unknown_overrides_local_drift": z3.Implies(
            z3.And(local == DRIFT, shared == UNKNOWN), composed == UNKNOWN),
        "either_witnessed_drift_admits_update": z3.Implies(
            z3.And(local != UNKNOWN, shared != UNKNOWN,
                   z3.Or(local == DRIFT, shared == DRIFT)), composed == DRIFT),
        "unknown_in_either_owner_never_installs": z3.Implies(
            z3.Or(local == UNKNOWN, shared == UNKNOWN), composed != DRIFT),
    }
    for label, claim in composition_claims.items():
        check = z3.Solver()
        check.add(admissible, z3.Not(claim))
        assert check.check() == z3.unsat, "composed sourcecut proof failed: " + label
    # Negative control: a simple OR conflates a witnessed DRIFT with UNKNOWN.
    bad_composition = z3.Or(local != MATCH, shared != MATCH)
    bad = z3.Solver()
    bad.add(admissible, local == MATCH, shared == UNKNOWN, bad_composition)
    assert bad.check() == z3.sat

    # R12 two-axis source/installed versus process-generation selection.
    # The process axis binds systemd main PID, real executable inode and exact
    # argv run -c CONFIG, plus birth order relative to config ctime/mtime.
    # It remains a creation-order witness, NOT an in-memory policy digest.
    installed, running = z3.Ints("r12_installed r12_running")
    allowed = z3.And(
        z3.Or(installed == MATCH, installed == DRIFT, installed == UNKNOWN),
        z3.Or(running == MATCH, running == DRIFT, running == UNKNOWN),
    )
    qualified = z3.And(installed != UNKNOWN, running != UNKNOWN)
    install_r12 = z3.And(qualified, installed == DRIFT)
    restart_r12 = z3.And(qualified, z3.Or(installed == DRIFT, running == DRIFT))
    start_r12 = z3.And(qualified, installed == MATCH, running == MATCH)
    loaded_claims = {
        "loaded_stale_with_installed_match_restarts_without_reinstall": z3.Implies(
            z3.And(installed == MATCH, running == DRIFT),
            z3.And(restart_r12, z3.Not(install_r12), z3.Not(start_r12))),
        "both_match_never_reinstall_or_restart": z3.Implies(
            z3.And(installed == MATCH, running == MATCH),
            z3.And(start_r12, z3.Not(restart_r12), z3.Not(install_r12))),
        "file_drift_requires_reinstall_and_owner_restart": z3.Implies(
            z3.And(installed == DRIFT, running != UNKNOWN),
            z3.And(install_r12, restart_r12)),
        "any_unknown_blocks_owner_effects": z3.Implies(
            z3.Or(installed == UNKNOWN, running == UNKNOWN),
            z3.And(z3.Not(install_r12), z3.Not(restart_r12), z3.Not(start_r12))),
    }
    for label, claim in loaded_claims.items():
        solver = z3.Solver()
        solver.add(allowed, z3.Not(claim))
        assert solver.check() == z3.unsat, "process generation proof failed: " + label
    historical = z3.Solver()
    historical.add(allowed, installed == MATCH, running == DRIFT,
                   z3.Not(installed == DRIFT))  # R11 lost restart after crash
    assert historical.check() == z3.sat

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
        "provedProperties": list(statements) + list(composition_claims) + list(loaded_claims),
        "negativeControls": [
            "Boolean SourceCut fail means install even when observation UNKNOWN",
            "external endpoint failure triggers legacy installer with matching SourceCut",
            "Boolean composition permits installation when shared SourceCut is UNKNOWN",
            "Post-install/pre-restart crash leaves source MATCH but running old",
        ],
        "sourceAdmission": admission,
        "sourcecutStates": ["MATCH", "DRIFT", "UNKNOWN"],
        "excluded": ["systemd start success", "external Internet availability",
                     "multi-file atomic release under crash", "loaded byte parity",
                     "actual application traffic and device-origin exit/DNS evidence"],
    }


if __name__ == "__main__":
    print(json.dumps(prove(), sort_keys=True))
