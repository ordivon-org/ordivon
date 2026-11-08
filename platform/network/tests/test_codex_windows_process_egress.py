"""Counterexamples: no historical Windows traffic may be inferred from a profile."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "consumers/codex/windows_process_egress.py"


def module():
    spec = importlib.util.spec_from_file_location("win_codex_process_witness", SOURCE)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def test_proxy_requires_both_http_and_https_with_same_scoped_endpoint():
    witness = module()
    assert witness.proxy_env_state({}) == "UNSET"
    assert witness.proxy_env_state({"HTTPS_PROXY": "http://127.0.0.1:19982"}) == "PARTIAL"
    assert witness.proxy_env_state({
        "HTTP_PROXY": "http://127.0.0.1:19980",
        "HTTPS_PROXY": "http://127.0.0.1:19982",
    }) == "MISMATCH"
    assert witness.proxy_env_state({
        "HTTP_PROXY": "http://127.0.0.1:19781",
        "HTTPS_PROXY": "http://127.0.0.1:19781",
    }) == "SCOPED"


def test_unrelated_tls_socket_does_not_certify_a_proxy_route():
    witness = module()
    assert witness.socket_observation("UNSET", 0, 1) == "NONLOCAL_TLS_SOCKET_OBSERVED"
    assert witness.socket_observation("SCOPED", 0, 1) == "NONLOCAL_TLS_SOCKET_OBSERVED"
    assert witness.socket_observation("SCOPED", 1, 0) == "LOCAL_PROXY_SOCKET_OBSERVED"
    assert witness.socket_observation("UNSET", 1, 0) == "LOCAL_PROXY_SOCKET_OBSERVED"
    assert witness.socket_observation("UNREADABLE", 1, 1) == "PROXY_AND_OTHER_TLS_SOCKETS_OBSERVED"



def test_windows_desktop_default_is_shared_carrier_not_linux_codex_proxy():
    witness = module()
    assert witness.proxy_env_state({
        "HTTP_PROXY": "http://127.0.0.1:19781",
        "HTTPS_PROXY": "http://127.0.0.1:19781",
    }) == "SCOPED"
    assert witness.proxy_env_state({
        "HTTP_PROXY": "http://127.0.0.1:19982",
        "HTTPS_PROXY": "http://127.0.0.1:19982",
    }) == "MISMATCH"
    assert witness.proxy_env_state({
        "HTTP_PROXY": "http://127.0.0.1:19982",
        "HTTPS_PROXY": "http://127.0.0.1:19982",
    }, port=19982) == "SCOPED"


def test_snapshot_does_not_infer_bypass_or_full_proof_from_socket(tmp_path):
    witness = module()

    class Connection:
        def __init__(self, ip, port):
            self.status = "ESTABLISHED"
            self.raddr = (ip, port)

    class Process:
        pid = 9001
        info = {"name": "codex.exe", "pid": 9001}
        def environ(self):
            return {}  # Windows user-level system proxy does not imply HTTP_PROXY.
        def create_time(self):
            return 1000000.0
        def net_connections(self, kind):
            assert kind == "tcp"
            return [Connection("127.0.0.1", 19781),
                    Connection("93.184.215.14", 443)]

    class Psutil:
        AccessDenied = type("AccessDenied", (Exception,), {})
        NoSuchProcess = type("NoSuchProcess", (Exception,), {})
        def process_iter(self, attrs):
            assert attrs == ["name", "pid"]
            return [Process()]

    data = witness.observe(Psutil(), tmp_path / "absent", 19781)
    assert data["standing"] == "END_TO_END_EGRESS_UNKNOWN"
    assert data["proxyPortRole"] == "windows-desktop-shared-carrier"
    assert data["windowsSystemProxyPolicy"] == "NOT_EVALUATED"
    assert data["observedProcessCount"] == 1
    p = data["processes"][0]
    assert p["proxyEnvironment"] == "UNSET"
    assert p["proxyTcpSockets"] == 1
    assert p["nonlocalTlsTcpSockets"] == 1
    assert p["socketObservation"] == "PROXY_AND_OTHER_TLS_SOCKETS_OBSERVED"
    assert not any("93.184." in str(value) for value in p.values())
