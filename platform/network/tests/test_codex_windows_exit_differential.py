"""Counterexamples to inferring mandatory VPN enforcement from Windows proxy."""
import importlib.util
import json
from pathlib import Path
import subprocess

SOURCE = Path(__file__).resolve().parents[1] / "consumers/codex/windows_exit_differential.py"


def module():
    spec = importlib.util.spec_from_file_location("windows_exit_differential", SOURCE)
    assert spec and spec.loader
    o = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(o)
    return o


class Probe:
    def __init__(self, responses):
        self.responses = responses
        self.commands = []

    def __call__(self, args, **kwargs):
        self.commands.append((args, kwargs))
        status, body = self.responses[len(self.commands) - 1]
        return subprocess.CompletedProcess(args, status, body, "possibly sensitive")


def ok(address):
    return (0, json.dumps({"ip": address}))


def test_distinct_public_exits_falsify_mandatory_proxy():
    m = module()
    p = Probe([ok("1.1.1.1"), ok("8.8.8.8")])
    output = m.evaluate(runner=p)
    assert output["standing"] == "DIRECT_EXIT_COUNTEREXAMPLE"
    assert output["samePublicExit"] is False
    assert output["direct"]["exitTag"] != output["proxy"]["exitTag"]
    assert "1.1.1.1" not in json.dumps(output)
    assert "8.8.8.8" not in json.dumps(output)
    assert "sensitive" not in json.dumps(output)
    direct, proxy = (x[0] for x in p.commands)
    assert direct[:2] == ["curl.exe", "-q"]
    assert direct[direct.index("--proxy") + 1] == ""
    assert direct[direct.index("--noproxy") + 1] == "*"
    assert proxy[proxy.index("--proxy") + 1] == "http://127.0.0.1:19781"
    assert proxy[proxy.index("--noproxy") + 1] == ""
    assert all(cmd[-1] == "https://ipinfo.io/json" for cmd in (direct, proxy))


def test_identical_public_exits_do_not_prove_mandatory_proxy():
    m = module()
    out = m.evaluate(runner=Probe([ok("1.1.1.1"), ok("1.1.1.1")]))
    assert out["standing"] == "UNKNOWN"
    assert out["samePublicExit"] is True


def test_direct_connection_failure_is_not_enforcement_proof():
    m = module()
    out = m.evaluate(runner=Probe([(28, ""), ok("1.1.1.1")]))
    assert out["standing"] == "UNKNOWN"
    assert out["samePublicExit"] is None
    assert out["direct"]["outcome"] == "FAILED"


def test_proxy_failure_is_not_direct_policy_proof():
    m = module()
    out = m.evaluate(runner=Probe([ok("1.1.1.1"), (56, "")]))
    assert out["standing"] == "UNKNOWN"


def test_malformed_or_private_address_never_counts_as_public_exit():
    m = module()
    for body in ("not json", '{"ip":"192.168.1.1"}',
                 '{"ip":"127.0.0.1"}', '{"ip":"::1"}', '{}'):
        out = m.evaluate(runner=Probe([(0, body), ok("8.8.8.8")]))
        assert out["standing"] == "UNKNOWN"
        assert out["direct"]["reason"] == "UNTRUSTED_EXIT_RESPONSE"


def test_curl_missing_or_timeout_is_unknown():
    m = module()
    def unavailable(args, **kwargs):
        raise FileNotFoundError("curl absent")
    assert m.evaluate(runner=unavailable)["standing"] == "UNKNOWN"
    def timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 17)
    assert m.evaluate(runner=timeout)["standing"] == "UNKNOWN"


def test_bad_transport_and_proxy_port_are_rejected():
    m = module()
    for mode in ("ftp", "tun"):
        try:
            m._probe(mode, curl="curl", port=19781, hmac_key=b"test")
        except ValueError:
            pass
        else:
            assert False
    try:
        m._probe("proxy", curl="curl", port=0, hmac_key=b"test")
    except ValueError:
        pass
    else:
        assert False


def test_fingerprint_is_per_run_and_not_deterministic_ip_hash():
    m = module()
    a = m.evaluate(runner=Probe([ok("1.1.1.1"), ok("8.8.8.8")]))
    b = m.evaluate(runner=Probe([ok("1.1.1.1"), ok("8.8.8.8")]))
    assert a["standing"] == b["standing"] == "DIRECT_EXIT_COUNTEREXAMPLE"
    assert a["direct"]["exitTag"] != b["direct"]["exitTag"]
    assert "non-linkable" not in a["fingerprintScope"] or a["direct"]["exitTag"] != b["direct"]["exitTag"]
