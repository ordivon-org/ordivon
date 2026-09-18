import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workstation" / "execution_fabric" / "workflows"


def load(name):
    return json.loads((WORKFLOWS / name).read_text(encoding="utf-8"))


def validate_plan(plan):
    assert plan["schemaVersion"] == 1
    assert plan["executionStarted"] is False
    steps = plan["steps"]
    assert steps
    ids = [step["stepId"] for step in steps]
    assert len(ids) == len(set(ids))
    known = set(ids)
    for step in steps:
        assert step["schemaVersion"] == 1
        assert step["effectDispatched"] is False
        assert step["kind"] in {"observe", "gate", "act", "verify", "recover", "compensate"}
        assert step["authorityMode"] in {
            "open_control",
            "normal",
            "maintenance",
            "recovery",
            "security",
            "security_lab",
            "emergency",
            "strict",
        }
        assert step["conflictMode"] in {
            "observer",
            "shared_read",
            "exclusive_write",
            "cooperative_write",
            "adversarial_lab",
        }
        assert set(step.get("dependsOn", [])) <= known
        assert step["stepId"] not in step.get("dependsOn", [])
        for forbidden in ("command", "executable", "args", "powershell", "shell", "script"):
            assert forbidden not in step

    state = {}

    def visit(step_id):
        if state.get(step_id) == 1:
            raise AssertionError("workflow dependency cycle")
        if state.get(step_id) == 2:
            return
        state[step_id] = 1
        step = next(item for item in steps if item["stepId"] == step_id)
        for dependency in step.get("dependsOn", []):
            visit(dependency)
        state[step_id] = 2

    for step_id in ids:
        visit(step_id)


def by_id(plan):
    return {step["stepId"]: step for step in plan["steps"]}


def test_wsl_recovery_is_capability_only_and_keeps_recovery_order():
    plan = load("wsl-control-plane-recovery-r1.json")
    validate_plan(plan)
    steps = by_id(plan)
    assert steps["step/probe-control-plane"]["dependsOn"] == ["step/probe-wsl"]
    assert steps["step/ensure-control-plane"]["dependsOn"] == ["step/probe-control-plane"]
    assert steps["step/ensure-control-plane"]["requestedCapabilityId"] == "capability/service/ensure"
    assert steps["step/verify-runtime-health"]["dependsOn"] == ["step/ensure-control-plane"]


def test_d_drive_compact_preserves_destructive_safety_gates():
    plan = load("d-drive-vhd-compact-r2.json")
    validate_plan(plan)
    steps = by_id(plan)

    assert steps["step/validate-authorization"]["dependsOn"] == ["step/doctor-preflight"]
    assert steps["step/terminate-wsl"]["dependsOn"] == ["step/trim-filesystem"]
    assert steps["step/exclusive-open"]["dependsOn"] == ["step/confirm-distro-offline"]
    assert steps["step/compact-vhd"]["dependsOn"] == ["step/exclusive-open"]
    assert steps["step/compact-vhd"]["requestedCapabilityId"] == "capability/storage/compact"
    assert steps["step/verify-vhd-non-growth"]["dependsOn"] == ["step/compact-vhd"]
    assert steps["step/recover-control-plane"]["dependsOn"] == ["step/verify-vhd-non-growth"]
    assert steps["step/post-doctor"]["dependsOn"] == ["step/verify-runtime-health"]


def test_workflow_manifests_are_plan_only_not_embedded_scripts():
    for path in sorted(WORKFLOWS.glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        lowered = raw.lower()
        for forbidden in ("diskpart.exe", "powershell.exe", "systemctl ", "wsl.exe", "fstrim "):
            assert forbidden not in lowered
        validate_plan(json.loads(raw))
