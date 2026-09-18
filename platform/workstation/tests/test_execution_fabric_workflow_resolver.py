import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workstation" / "execution_fabric" / "workflow_resolver.py"
SPEC = importlib.util.spec_from_file_location("ef_workflow_resolver", MODULE_PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

CATALOG = ROOT / "workstation" / "execution_fabric" / "catalog" / "current-r1.json"
WORKFLOWS = ROOT / "workstation" / "execution_fabric" / "workflows"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_catalog_records_only_proven_execution_providers():
    catalog = load(CATALOG)
    M.validate_catalog(catalog)
    providers = {item["providerId"]: item for item in catalog["providers"]}
    assert set(providers) == {
        "provider/linux-local/local-linux-runner-v1",
        "provider/linux-local/windows-native-launcher-v1",
    }
    assert providers["provider/linux-local/windows-native-launcher-v1"]["platform"] == "windows"
    windows = next(node for node in catalog["nodes"] if node["nodeId"] == "windows-local")
    assert windows["nativeControlPlane"] is False
    assert windows["providers"] == []


def test_real_workflows_fail_open_to_visibility_not_shell_fallback():
    catalog = load(CATALOG)
    for name in ("wsl-control-plane-recovery-r1.json", "d-drive-vhd-compact-r2.json"):
        binding = M.resolve(load(WORKFLOWS / name), catalog)
        assert binding["dispatchStarted"] is False
        assert binding["fullyResolved"] is False
        assert binding["bindings"]
        assert all(item["disposition"] == "unresolved" for item in binding["bindings"])
        assert all(item["candidateProviderIds"] == [] for item in binding["bindings"])


def test_unique_synthetic_provider_resolves_and_ambiguity_never_auto_selects():
    plan = {
        "schemaVersion": 1,
        "workflowId": "workflow/test",
        "ownerId": "controller/test",
        "executionStarted": False,
        "steps": [
            {
                "schemaVersion": 1,
                "stepId": "step/a",
                "kind": "act",
                "resourceId": "resource/test",
                "requestedCapabilityId": "capability/test/do",
                "authorityMode": "maintenance",
                "conflictMode": "exclusive_write",
                "dependsOn": [],
                "effectDispatched": False,
            }
        ],
    }
    base = {
        "schemaVersion": 1,
        "resources": [
            {
                "schemaVersion": 1,
                "resourceId": "resource/test",
                "resourceKind": "test",
                "nodeId": "node/test",
                "conflictDomains": [],
            }
        ],
        "nodes": [
            {
                "schemaVersion": 1,
                "nodeId": "node/test",
                "platform": "linux",
                "nativeControlPlane": True,
                "trustDomain": "ordivon.local",
                "providers": ["provider/a"],
                "capabilities": ["capability/test/do"],
                "authorityContexts": [],
            }
        ],
        "providers": [
            {
                "schemaVersion": 1,
                "providerId": "provider/a",
                "nodeId": "node/test",
                "platform": "linux",
                "capabilities": ["capability/test/do"],
            }
        ],
    }
    resolved = M.resolve(plan, base)
    assert resolved["fullyResolved"] is True
    assert resolved["bindings"][0]["selectedProviderId"] == "provider/a"

    base["nodes"][0]["providers"].append("provider/b")
    base["providers"].append(
        {
            "schemaVersion": 1,
            "providerId": "provider/b",
            "nodeId": "node/test",
            "platform": "linux",
            "capabilities": ["capability/test/do"],
        }
    )
    ambiguous = M.resolve(plan, base)
    assert ambiguous["fullyResolved"] is False
    assert ambiguous["bindings"][0]["disposition"] == "ambiguous"
    assert "selectedProviderId" not in ambiguous["bindings"][0]


def test_unresolved_capability_summary_is_deterministic():
    binding = M.resolve(load(WORKFLOWS / "d-drive-vhd-compact-r2.json"), load(CATALOG))
    capabilities = M.unresolved_capabilities(binding)
    assert capabilities == sorted(set(capabilities))
    assert "capability/storage/compact" in capabilities
    assert "capability/wsl/terminate" in capabilities
    assert "capability/runtime/doctor" in capabilities


def test_provider_backlog_covers_all_real_unresolved_capabilities_once_by_family():
    catalog = load(CATALOG)
    backlog = load(ROOT / "workstation" / "execution_fabric" / "provider-backlog-r1.json")
    assert backlog["status"] == "planned_not_implemented"
    planned = backlog["plannedProviders"]
    assert all(item["status"] == "missing" for item in planned)

    unresolved = set()
    for name in ("wsl-control-plane-recovery-r1.json", "d-drive-vhd-compact-r2.json"):
        unresolved.update(
            M.unresolved_capabilities(M.resolve(load(WORKFLOWS / name), catalog))
        )
    planned_capabilities = {
        capability
        for provider in planned
        for capability in provider["capabilities"]
    }
    assert planned_capabilities == unresolved

    current_provider_ids = {item["providerId"] for item in catalog["providers"]}
    assert not current_provider_ids.intersection(
        item["providerFamilyId"] for item in planned
    )
