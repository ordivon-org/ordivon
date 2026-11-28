"""Native terminal versus observation consistency; never invoke a provider."""
import json
from pathlib import Path
import subprocess
import sys

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "providers/gluetun"))
from active_observation import receive_observation, parse_curl_receipt


def observation(a=True, b=True, state="QUALIFIED_ACTIVE_SAMPLE"):
    return {
        "kind":"ordivon.network.gluetun-active-qualification",
        "standing":state, "observedAtUtc":"2026-11-26T01:30:00+00:00",
        "currentCatalogCountry":"Japan", "currentPublicExitCountryCode":"JP",
        "actualEndpointStableDuringSample":True,"providerStatus":"running",
        "qualifiedStandbyCount":0,
        "business":{"ordinary_https":{"httpTlsAndConnect":a,"totalMs":20},
                    "github_https":{"httpTlsAndConnect":b,"totalMs":30}},
    }


@settings(max_examples=150, derandomize=True, database=None, deadline=None)
@given(st.booleans(), st.booleans(), st.sampled_from(["QUALIFIED_ACTIVE_SAMPLE","NOT_QUALIFIED"]),
       st.integers(-12,4))
def test_native_terminal_and_business_truth_table(a, b, state, code):
    raw = observation(a,b,state)
    # Independent relation: precisely the two coherent terminal classes.
    valid = (a and b and state=="QUALIFIED_ACTIVE_SAMPLE" and code==0
             or not (a and b) and state=="NOT_QUALIFIED" and code==1)
    if valid:
        assert receive_observation(json.dumps(raw), code)==raw
    else:
        with pytest.raises(ValueError):
            receive_observation(json.dumps(raw), code)


@pytest.mark.parametrize("timing", ["nan","inf","-inf","1e308","-1"])
def test_nonfinite_or_negative_timing_is_unknown_not_a_business_failure(timing):
    with pytest.raises(ValueError):
        parse_curl_receipt("200 200 0.1 " + timing)


@pytest.mark.parametrize("code", [0,1,-9])
def test_real_child_stdout_before_terminal_is_not_completion(code):
    raw = observation()
    source = "import os,signal,sys; print(sys.argv[1],flush=True); "
    source += "os.kill(os.getpid(),signal.SIGKILL)" if code == -9 else f"sys.exit({code})"
    result = subprocess.run([sys.executable,"-c",source,json.dumps(raw)],
                            capture_output=True,text=True,timeout=5)
    assert result.returncode == code and json.loads(result.stdout)==raw
    if code == 0:
        assert receive_observation(result.stdout,result.returncode)==raw
    else:
        with pytest.raises(ValueError):
            receive_observation(result.stdout,result.returncode)


def test_duplicate_and_nonfinite_json_are_not_native_evidence():
    raw = json.dumps(observation())
    for text in (raw[:-1]+',"standing":"QUALIFIED_ACTIVE_SAMPLE"}',
                 raw[:-1]+',"extra":NaN}'):
        with pytest.raises(ValueError):
            receive_observation(text,0)


@pytest.mark.parametrize("state",["UNKNOWN","REJECTED_FORBIDDEN_EXIT","REJECTED_NOT_ALLOWED"])
def test_native_nonqualified_reports_are_preserved_without_reinterpretation(state):
    raw={"kind":"ordivon.network.gluetun-active-qualification","standing":state}
    assert receive_observation(json.dumps(raw),1)==raw
    with pytest.raises(ValueError):
        receive_observation(json.dumps(raw),0)
