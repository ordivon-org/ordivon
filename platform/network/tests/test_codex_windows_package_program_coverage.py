"""Package-root-only Windows Firewall rules cannot cover external children."""
import importlib.util
from pathlib import Path
import pytest

SOURCE = (Path(__file__).resolve().parents[1] /
          "consumers/codex/windows_package_program_coverage.py")


def module():
    spec = importlib.util.spec_from_file_location("win_cover", SOURCE)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


ROOT = r"C:\Program Files\WindowsApps\OpenAI.Codex_1"
T0 = "2026-11-08T12:30:00Z"
T1 = "2026-11-08T12:31:00Z"
T2 = "2026-11-08T12:32:00Z"


def proc(pid, parent, exe, name="node.exe", at=T1):
    return dict(pid=pid, parentPid=parent, name=name, executable=exe,
                creationUtc=at, session=1)


def fixture(*more):
    exe = ROOT + r"\app\ChatGPT.exe"
    return {
        "packageFamily": "OpenAI.Codex_2p2nqsd0c76g0",
        "packageVersion": "26.1103.4239.0",
        "installLocation": ROOT,
        "processes": [proc(50, 0, exe, "ChatGPT.exe", T0), *more],
        "signatures": [dict(executable=exe, status="Valid")],
    }


def test_prefix_collision_excluded():
    m = module()
    assert m.in_root(ROOT + r"\app\ChatGPT.exe", ROOT)
    assert not m.in_root(ROOT + r"-fake\ChatGPT.exe", ROOT)
    assert not m.in_root(r"C:\Program Files\WindowsApps\OpenAI.Codex_2\bin.exe", ROOT)


def test_external_child_and_grandchild_observed_without_policy_claim():
    m = module()
    x = m.summarize(fixture(
        proc(60, 50, r"C:\Windows\System32\cmd.exe", "cmd.exe"),
        proc(70, 60, r"C:\Program Files\nodejs\node.exe", "node.exe", T2),
    ))
    assert x["standing"] == "EXTERNAL_DESCENDANTS_OBSERVED"
    assert x["uniquePackagePrograms"] == 1
    assert x["externalDescendantCount"] == 2
    assert x["externalDescendantBasenames"] == {"cmd.exe": 1, "node.exe": 1}
    assert x["allProtocolFirewallCoverage"] == "UNKNOWN"
    assert ROOT not in str(x)


def test_reused_parent_pid_cannot_prove_lineage():
    x = module().summarize(fixture(
        proc(60, 50, r"C:\Windows\System32\cmd.exe", "cmd.exe", "2026-11-08T12:29:00Z")
    ))
    assert x["reusedParentPidExcluded"] == 1
    assert x["externalDescendantCount"] == 0


def test_missing_creation_date_is_unknown():
    x = module().summarize(fixture(proc(60, 50, r"C:\Windows\System32\cmd.exe", "cmd.exe", None)))
    assert x["unknownParentGeneration"] == 1
    assert x["standing"] == "UNKNOWN"


def test_absence_of_live_external_children_is_not_enforcement():
    x = module().summarize(fixture())
    assert x["standing"] == "NO_EXTERNAL_DESCENDANTS_IN_SNAPSHOT"
    assert x["allProtocolFirewallCoverage"] == "UNKNOWN"


def test_invalid_binary_signature_does_not_certify_source_identity():
    sample = fixture()
    sample["signatures"][0]["status"] = "NotSigned"
    x = module().summarize(sample)
    assert x["allObservedPackageBinariesSigned"] is False


def test_missing_external_path_is_counted():
    x = module().summarize(fixture(proc(60, 50, "", "cmd.exe")))
    assert x["externalDescendantMissingPath"] == 1


def test_same_binary_6_processes_counts_one_program():
    x = module().summarize(fixture(
        proc(51, 50, ROOT + r"\app\ChatGPT.exe", "ChatGPT.exe")
    ))
    assert x["packageProcessCount"] == 2
    assert x["uniquePackagePrograms"] == 1
    assert x["packagePrograms"][0]["processCount"] == 2


def test_no_package_root_in_snapshot_is_unknown():
    sample = fixture()
    sample["processes"] = []
    assert module().summarize(sample)["standing"] == "UNKNOWN"


@pytest.mark.parametrize("bad", [
    dict(installLocation="relative", processes=[], signatures=[]),
    dict(installLocation=ROOT, processes=[dict(pid="3", parentPid=1)], signatures=[]),
    dict(installLocation=ROOT, processes=[dict(pid=3, parentPid=0)]*2, signatures=[]),
    dict(installLocation=ROOT, processes=["bogus"], signatures=[]),
])
def test_malformed_native_input_rejected(bad):
    with pytest.raises(ValueError):
        module().summarize(bad)
