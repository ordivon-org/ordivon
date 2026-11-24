"""Bounded package-token identity observation is not package WFP enforcement."""
import importlib.util
from pathlib import Path
import pytest

P = (Path(__file__).resolve().parents[1] /
     "consumers/codex/windows_package_token_evidence.py")


def module():
    spec = importlib.util.spec_from_file_location("wfp_pkg_token", P)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def row(**changes):
    return {"process": "chatgpt.exe", "queryStatus": "OK",
            "isAppContainer": False, "tokenHasAppContainerSid": False,
            "packageSidEqualsAppContainer": False,
            "packageSidInGroups": False, **changes}


def test_native_win32_packaged_but_absent_sid_never_proves_firewall_policy():
    m = module()
    r = m.evaluate("S-1-15-2-1-2-3", [row(), row()])
    assert r["tokenObservation"] == "SAMPLED_PACKAGE_SID_ABSENT"
    assert r["packageFirewallEnforcement"] == "UNKNOWN"
    assert r["sampledProcesses"] == 2
    assert r["fullyReadTokens"] is True
    assert r["sideEffects"] == "READ_ONLY"


@pytest.mark.parametrize("detail", [
    {"packageSidInGroups": True},
    {"packageSidEqualsAppContainer": True},
])
def test_positive_token_sid_still_not_effectiveness_proof(detail):
    m = module()
    x = m.evaluate("S-1-15-2-1", [row(**detail)])
    assert x["tokenObservation"] == "SAMPLED_PACKAGE_SID_PRESENT"
    assert x["packageFirewallEnforcement"] == "UNKNOWN"
    assert x["matchingTokens"] == 1


def test_partial_token_query_is_unknown_not_false():
    m = module()
    x = m.evaluate("S-1-15-2-1", [row(), {"process": "codex.exe",
                                        "queryStatus": "PROCESS_UNAVAILABLE"}])
    assert x["tokenObservation"] == "UNKNOWN"
    assert not x["fullyReadTokens"]


def test_empty_sample_and_derived_sid_error_are_unknown():
    m = module()
    assert m.evaluate("S-1-15-2-1", [])["tokenObservation"] == "UNKNOWN"
    assert m.evaluate(None, [row()])["tokenObservation"] == "UNKNOWN"


@pytest.mark.parametrize("target", [
    "", "codex.exe", "codex.exe:0", "codex.exe:1",
    "codex.exe:-1", "codex.exe:inf", "bad/path.exe:20",
    "codex.exe:4294967296", "not-an-executable:42",
    "codex.exe: 20",
])
def test_untrusted_target_inputs_rejected(target):
    with pytest.raises(ValueError):
        module().parse_target(target)


def test_read_only_target_parser():
    assert module().parse_target("ChatGPT.exe:24424") == ("chatgpt.exe", 24424)
